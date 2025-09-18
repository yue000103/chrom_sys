"""
MQTT发布管理器
管理所有设备数据的MQTT发布
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """MQTT发布管理器"""

    def __init__(self, mqtt_manager):
        self.mqtt_manager = mqtt_manager
        self.publish_queue = asyncio.Queue()
        self.batch_size = 10
        self.batch_interval = 0.5  # 批量发送间隔（秒）
        self.retry_count = 3
        self.retry_delay = 1.0  # 重试延迟（秒）
        self._publisher_task = None
        self.is_running = False
        self.statistics = defaultdict(int)

        # 定义所有MQTT主题
        self.topics = {
            # 主机模块设备主题
            "relay": "chromatography/relay/{device_id}/status",
            "pressure": "chromatography/pressure/sensor/value",
            "detector": "chromatography/detector/signal",
            "pump": "chromatography/pump/{device_id}/status",
            "bubble_host": "chromatography/bubble/host/{device_id}/status",

            # 收集模块设备主题
            "led": "chromatography/led/status",
            "valve": "chromatography/valve/{device_id}/status",
            "bubble_collect": "chromatography/bubble/collect/{device_id}/status",
            "multivalve": "chromatography/multivalve/{device_id}/position",
            "spray_pump": "chromatography/spray_pump/status",

            # 系统主题
            "system_status": "chromatography/system/status",
            "system_alert": "chromatography/system/alert",
            "data_aggregated": "chromatography/data/aggregated",

            # 保留原有主题兼容性
            "data_random": "data/random",
            "chromatography_pressure": "chromatography/pressure",
            "chromatography_detector": "chromatography/detector",
            "chromatography_bubble": "chromatography/bubble",
            "chromatography_flow": "chromatography/flow"
        }

    async def start(self):
        """启动发布管理器"""
        if self.is_running:
            logger.warning("MQTT发布管理器已在运行")
            return

        self.is_running = True
        self._publisher_task = asyncio.create_task(self._publisher_loop())
        logger.info("MQTT发布管理器已启动")

    async def stop(self):
        """停止发布管理器"""
        self.is_running = False

        if self._publisher_task:
            self._publisher_task.cancel()
            try:
                await self._publisher_task
            except asyncio.CancelledError:
                pass

        # 发送队列中剩余的数据
        await self._flush_queue()
        logger.info("MQTT发布管理器已停止")

    async def publish_device_data(self, device_type: str, device_id: str, data: Dict[str, Any]):
        """
        发布设备数据
        :param device_type: 设备类型
        :param device_id: 设备ID
        :param data: 设备数据
        """
        topic = self._get_topic(device_type, device_id)
        if topic:
            await self.publish_queue.put({
                "topic": topic,
                "data": data,
                "device_type": device_type,
                "device_id": device_id
            })
            self.statistics[f"queued_{device_type}"] += 1

    async def publish_system_status(self, status: Dict[str, Any]):
        """发布系统状态"""
        await self.publish_queue.put({
            "topic": self.topics["system_status"],
            "data": status,
            "device_type": "system",
            "device_id": "system"
        })

    async def publish_alert(self, alert: Dict[str, Any]):
        """发布告警信息"""
        await self.publish_queue.put({
            "topic": self.topics["system_alert"],
            "data": alert,
            "device_type": "alert",
            "device_id": "system"
        })

    async def publish_aggregated_data(self, aggregated_data: Dict[str, Any]):
        """发布聚合数据"""
        await self.publish_queue.put({
            "topic": self.topics["data_aggregated"],
            "data": aggregated_data,
            "device_type": "aggregated",
            "device_id": "system"
        })

    def _get_topic(self, device_type: str, device_id: str) -> Optional[str]:
        """根据设备类型获取MQTT主题"""
        topic_template = None

        # 主机模块设备
        if device_type == "relay_controller":
            topic_template = self.topics["relay"]
        elif device_type == "pressure_sensor":
            return self.topics["pressure"]
        elif device_type == "detector":
            return self.topics["detector"]
        elif device_type == "pump_controller":
            topic_template = self.topics["pump"]
        elif device_type == "bubble_sensor_host":
            topic_template = self.topics["bubble_host"]

        # 收集模块设备
        elif device_type == "led_controller":
            return self.topics["led"]
        elif device_type == "valve_controller":
            topic_template = self.topics["valve"]
        elif device_type == "bubble_sensor_collect":
            topic_template = self.topics["bubble_collect"]
        elif device_type == "multi_valve":
            topic_template = self.topics["multivalve"]
        elif device_type == "spray_pump":
            return self.topics["spray_pump"]

        # 如果需要格式化主题（包含device_id）
        if topic_template and "{device_id}" in topic_template:
            return topic_template.format(device_id=device_id)

        return topic_template

    async def _publisher_loop(self):
        """发布循环"""
        batch = []
        last_publish_time = asyncio.get_event_loop().time()

        try:
            while self.is_running:
                try:
                    # 获取数据，最多等待batch_interval秒
                    timeout = self.batch_interval
                    item = await asyncio.wait_for(
                        self.publish_queue.get(),
                        timeout=timeout
                    )
                    batch.append(item)

                    # 检查是否需要发送批次
                    current_time = asyncio.get_event_loop().time()
                    if (len(batch) >= self.batch_size or
                        current_time - last_publish_time >= self.batch_interval):
                        await self._publish_batch(batch)
                        batch = []
                        last_publish_time = current_time

                except asyncio.TimeoutError:
                    # 超时，发送当前批次
                    if batch:
                        await self._publish_batch(batch)
                        batch = []
                        last_publish_time = asyncio.get_event_loop().time()

        except asyncio.CancelledError:
            # 被取消，发送剩余数据
            if batch:
                await self._publish_batch(batch)
            raise

        except Exception as e:
            logger.error(f"发布循环错误: {e}")

    async def _publish_batch(self, batch: List[Dict[str, Any]]):
        """批量发布数据"""
        for item in batch:
            await self._publish_with_retry(item)

    async def _publish_with_retry(self, item: Dict[str, Any]):
        """带重试的发布"""
        topic = item["topic"]
        data = item["data"]
        device_type = item.get("device_type", "unknown")

        for attempt in range(self.retry_count):
            try:
                success = await self.mqtt_manager.publish_data(topic, data)
                if success:
                    self.statistics[f"published_{device_type}"] += 1
                    logger.debug(f"成功发布到 {topic}")
                    return
                else:
                    logger.warning(f"发布失败 (尝试 {attempt + 1}/{self.retry_count}): {topic}")

            except Exception as e:
                logger.error(f"发布异常 (尝试 {attempt + 1}/{self.retry_count}): {e}")

            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)

        # 所有重试失败
        self.statistics[f"failed_{device_type}"] += 1
        logger.error(f"发布最终失败: {topic}")

    async def _flush_queue(self):
        """清空队列中的所有数据"""
        batch = []
        while not self.publish_queue.empty():
            try:
                item = self.publish_queue.get_nowait()
                batch.append(item)
                if len(batch) >= self.batch_size:
                    await self._publish_batch(batch)
                    batch = []
            except asyncio.QueueEmpty:
                break

        if batch:
            await self._publish_batch(batch)

    def get_statistics(self) -> Dict[str, Any]:
        """获取发布统计信息"""
        return {
            "queue_size": self.publish_queue.qsize(),
            "is_running": self.is_running,
            "statistics": dict(self.statistics)
        }

    async def publish_batch_device_data(self, device_data_list: List[Dict[str, Any]]):
        """批量发布设备数据"""
        for device_data in device_data_list:
            device_type = device_data.get("device_type")
            device_id = device_data.get("device_id")
            data = device_data.get("data")

            if device_type and device_id and data:
                await self.publish_device_data(device_type, device_id, data)

    def set_batch_config(self, batch_size: Optional[int] = None,
                        batch_interval: Optional[float] = None):
        """设置批量配置"""
        if batch_size is not None and batch_size > 0:
            self.batch_size = batch_size
            logger.info(f"批量大小设置为: {batch_size}")

        if batch_interval is not None and batch_interval > 0:
            self.batch_interval = batch_interval
            logger.info(f"批量间隔设置为: {batch_interval}秒")