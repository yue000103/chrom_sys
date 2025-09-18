"""
数据处理器模块
提供向后兼容的DataProcessor类，同时包含新的模块化组件
"""

import asyncio
import random
from datetime import datetime
import logging
from typing import Optional

from core.mqtt_manager import MQTTManager
from .mqtt_publisher import MQTTPublisher
from .host_devices_processor import HostDevicesProcessor
from .collect_devices_processor import CollectDevicesProcessor
from .device_data_collector import DeviceDataCollector
from .data_aggregator import DataAggregator

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    数据处理器 - 保持向后兼容性
    整合所有新的数据处理组件
    """

    def __init__(self, mqtt_manager: MQTTManager, db_manager=None):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.generated_count = 0
        self.data_interval = 1.0  # 每秒生成一个数据点 (开发文档要求)

        # 初始化新的组件
        self.mqtt_publisher = MQTTPublisher(mqtt_manager)
        self.host_processor = HostDevicesProcessor()
        self.collect_processor = CollectDevicesProcessor()
        self.data_collector = DeviceDataCollector(
            self.mqtt_publisher,
            self.host_processor,
            self.collect_processor
        )
        self.data_aggregator = DataAggregator()

        # 设备收集任务
        self._device_collection_task = None

        # 存储硬件设备实例
        self.host_devices = {}  # 主机设备
        self.collect_devices = {}  # 采集设备

    async def start(self):
        """启动数据处理器"""
        if self.is_running:
            logger.warning("数据处理器已在运行")
            return

        self.is_running = True

        # 启动原有的随机数据生成任务（保持兼容性）
        self._task = asyncio.create_task(self._data_generation_loop())

        # 启动新的设备数据收集任务
        await self.data_collector.start()
        await self.data_aggregator.start()

        # 启动设备数据收集循环
        self._device_collection_task = asyncio.create_task(self._device_collection_loop())

        logger.info("数据处理器已启动（包含新的设备数据收集）")

    async def stop(self):
        """停止数据处理器"""
        self.is_running = False

        # 停止原有任务
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # 停止设备收集任务
        if self._device_collection_task:
            self._device_collection_task.cancel()
            try:
                await self._device_collection_task
            except asyncio.CancelledError:
                pass

        # 停止新组件
        await self.data_collector.stop()
        await self.data_aggregator.stop()

        logger.info("数据处理器已停止")

    async def _data_generation_loop(self):
        """数据生成循环 - 保持原有功能"""
        try:
            while self.is_running:
                # 生成随机数据 (0-100) - 开发文档要求
                value = random.uniform(0, 100)

                # 创建数据格式 - 符合开发文档要求
                await self.generate_random_data(value)

                # 增加计数器
                self.generated_count += 1

                # 等待指定间隔 (1秒)
                await asyncio.sleep(self.data_interval)

        except asyncio.CancelledError:
            logger.info("数据生成循环被取消")
        except Exception as e:
            logger.error(f"数据生成循环出错: {e}")

    async def _device_collection_loop(self):
        """设备数据收集循环"""
        try:
            while self.is_running:
                # 收集所有设备数据
                all_device_data = await self._collect_all_device_data()

                # 发布每个设备的数据到其对应的MQTT主题
                for device_data in all_device_data:
                    device_id = device_data.get("device_id")
                    device_type = device_data.get("device_type")
                    data = device_data.get("data")
                    timestamp = device_data.get("timestamp")

                    if device_id and device_type and data:
                        # 更新聚合器
                        self.data_aggregator.update_device_data(device_id, device_data)

                        # 直接发布到MQTT
                        await self.mqtt_publisher.publish_device_data(device_type, device_id, data)

                        # 保存到数据库
                        if self.db_manager:
                            try:
                                # 提取数值类型的数据
                                if device_type == "detector" and isinstance(data, dict):
                                    signal_values = data.get("signal", [0, 0])
                                    # 如果是双通道数据
                                    if isinstance(signal_values, list) and len(signal_values) == 2:
                                        # 保存A通道
                                        await self.db_manager.insert_sensor_data(
                                            device_id=f"{device_id}_channel_a",
                                            data_type="signal_a",
                                            value=signal_values[0],
                                            unit="mAU",
                                            raw_data=str({"channel": "A", "wavelength": data.get("wavelength", [254, 280])[0]})
                                        )
                                        # 保存B通道
                                        await self.db_manager.insert_sensor_data(
                                            device_id=f"{device_id}_channel_b",
                                            data_type="signal_b",
                                            value=signal_values[1],
                                            unit="mAU",
                                            raw_data=str({"channel": "B", "wavelength": data.get("wavelength", [254, 280])[1]})
                                        )
                                    else:
                                        # 兼容单通道
                                        await self.db_manager.insert_sensor_data(
                                            device_id=device_id,
                                            data_type="signal",
                                            value=signal_values if isinstance(signal_values, (int, float)) else 0,
                                            unit="mAU",
                                            raw_data=str(data)
                                        )
                                elif device_type == "pressure_sensor" and isinstance(data, dict):
                                    pressure_value = data.get("pressure", 0)
                                    await self.db_manager.insert_sensor_data(
                                        device_id=device_id,
                                        data_type="pressure",
                                        value=pressure_value,
                                        unit="MPa",
                                        raw_data=str(data)
                                    )
                                elif isinstance(data, (int, float)):
                                    await self.db_manager.insert_sensor_data(
                                        device_id=device_id,
                                        data_type=device_type,
                                        value=float(data),
                                        raw_data=str(data)
                                    )
                            except Exception as e:
                                logger.error(f"保存传感器数据到数据库时出错 {device_id}: {e}")

                        # 也通过mqtt_manager发布以保持兼容性
                        if device_type == "detector":
                            signal_values = data.get("signal", [0, 0])
                            wavelength_values = data.get("wavelength", [254, 280])

                            # 发布双通道信号（以数组形式）
                            await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/signal", signal_values)

                            # 发布双通道波长（以数组形式）
                            await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/wavelength", wavelength_values)

                            # 单独发布每个通道的数据
                            if "channel_a" in data:
                                await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/channel_a", data["channel_a"])

                            if "channel_b" in data:
                                await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/channel_b", data["channel_b"])

                            # 发布保留时间
                            if "retention_time" in data:
                                await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/retention_time", {
                                    "retention_time": data["retention_time"],
                                    "unit": "min",
                                    "timestamp": timestamp
                                })

                            # 发布完整数据
                            await self.mqtt_manager.publish(f"chromatography/detector/{device_id}/full_data", data)

                        elif device_type == "pressure_sensor":
                            pressure_value = data.get("pressure", 0)
                            await self.mqtt_manager.publish_chromatography_data("pressure", device_id, pressure_value)

                # 发布聚合数据
                if all_device_data:
                    aggregated_data = await self.data_aggregator.get_aggregated_data()
                    await self.mqtt_publisher.publish_aggregated_data(aggregated_data)

                    # 发布系统状态
                    system_status = {
                        "timestamp": datetime.now().isoformat(),
                        "device_count": len(all_device_data),
                        "is_running": self.is_running,
                        "data_interval": self.data_interval
                    }
                    await self.mqtt_publisher.publish_system_status(system_status)

                    # 记录MQTT消息到数据库
                    if self.db_manager:
                        try:
                            await self.db_manager.log_mqtt_message(
                                topic="chromatography/system/status",
                                payload=str(system_status),
                                direction="publish"
                            )
                        except Exception as e:
                            logger.debug(f"记录MQTT消息时出错: {e}")

                # 等待下一个收集周期
                await asyncio.sleep(self.data_interval)

        except asyncio.CancelledError:
            logger.info("设备收集循环被取消")
        except Exception as e:
            logger.error(f"设备收集循环出错: {e}")

    async def _collect_all_device_data(self):
        """收集所有设备数据"""
        all_data = []

        try:
            # 从硬件设备收集数据
            timestamp = datetime.now().isoformat()

            # 收集主机设备数据
            if hasattr(self, 'host_devices') and self.host_devices:
                for device_name, device in self.host_devices.items():
                    try:
                        if hasattr(device, 'get_status'):
                            status = await device.get_status()
                            all_data.append({
                                "device_id": device_name,
                                "device_type": device.__class__.__name__,
                                "data": status,
                                "timestamp": timestamp
                            })
                        elif hasattr(device, 'get_signal'):
                            signal = await device.get_signal()
                            all_data.append({
                                "device_id": device_name,
                                "device_type": "detector",
                                "data": {"signal": signal},
                                "timestamp": timestamp
                            })
                        elif hasattr(device, 'get_pressure'):
                            pressure = await device.get_pressure()
                            all_data.append({
                                "device_id": device_name,
                                "device_type": "pressure_sensor",
                                "data": {"pressure": pressure},
                                "timestamp": timestamp
                            })
                    except Exception as e:
                        logger.error(f"收集设备 {device_name} 数据时出错: {e}")

            # 收集采集设备数据
            if hasattr(self, 'collect_devices') and self.collect_devices:
                for device_name, device in self.collect_devices.items():
                    try:
                        if hasattr(device, 'get_status'):
                            status = await device.get_status()
                            all_data.append({
                                "device_id": device_name,
                                "device_type": device.__class__.__name__,
                                "data": status,
                                "timestamp": timestamp
                            })
                    except Exception as e:
                        logger.error(f"收集设备 {device_name} 数据时出错: {e}")

        except Exception as e:
            logger.error(f"收集设备数据时出错: {e}")

        return all_data

    async def generate_random_data(self, value: float):
        """生成随机数据并发布到MQTT - 保持原有功能"""
        try:
            # 发布到 data/random 主题 - 开发文档要求
            success = await self.mqtt_manager.publish_random_data(value)

            if success:
                logger.debug(f"生成随机数据: {value:.2f} (总计: {self.generated_count})")
            else:
                logger.warning(f"发布随机数据失败: {value:.2f}")

        except Exception as e:
            logger.error(f"生成随机数据时出错: {e}")

    async def process_sensor_data(self, device_id: str, raw_data: dict):
        """处理传感器数据 - 保持原有功能"""
        try:
            # 根据设备类型处理数据
            if "pressure" in device_id.lower():
                await self._process_pressure_data(device_id, raw_data)
            elif "detector" in device_id.lower():
                await self._process_detector_data(device_id, raw_data)
            elif "bubble" in device_id.lower():
                await self._process_bubble_data(device_id, raw_data)
            else:
                logger.warning(f"未知设备类型: {device_id}")

        except Exception as e:
            logger.error(f"处理传感器数据时出错 {device_id}: {e}")

    async def _process_pressure_data(self, device_id: str, data: dict):
        """处理压力传感器数据"""
        value = data.get("value", 0)
        await self.mqtt_manager.publish_chromatography_data("pressure", device_id, value)

    async def _process_detector_data(self, device_id: str, data: dict):
        """处理检测器数据"""
        value = data.get("value", 0)
        await self.mqtt_manager.publish_chromatography_data("detector", device_id, value)

    async def _process_bubble_data(self, device_id: str, data: dict):
        """处理气泡传感器数据"""
        value = data.get("value", 0)
        await self.mqtt_manager.publish_chromatography_data("bubble", device_id, value)

    def get_statistics(self):
        """获取数据处理统计信息"""
        return {
            "is_running": self.is_running,
            "generated_count": self.generated_count,
            "data_interval": self.data_interval,
            "start_time": datetime.now().isoformat() if self.is_running else None,
            "collector_stats": self.data_collector.get_statistics(),
            "aggregator_stats": self.data_aggregator.get_statistics_summary()
        }

    def set_data_interval(self, interval: float):
        """设置数据生成间隔"""
        if interval > 0:
            self.data_interval = interval
            self.data_collector.set_collection_interval(interval)
            logger.info(f"数据生成间隔已设置为: {interval}秒")
        else:
            logger.warning("无效的数据间隔，必须大于0")

    def register_hardware_device(self, device_type: str, device_instance):
        """
        注册硬件设备实例到数据收集器
        :param device_type: 设备类型
        :param device_instance: 设备实例
        """
        self.data_collector.register_hardware_device(device_type, device_instance)

    def register_host_device(self, device_name: str, device_instance):
        """
        注册主机设备
        :param device_name: 设备名称
        :param device_instance: 设备实例
        """
        self.host_devices[device_name] = device_instance
        logger.info(f"注册主机设备: {device_name}")

    def register_collect_device(self, device_name: str, device_instance):
        """
        注册采集设备
        :param device_name: 设备名称
        :param device_instance: 设备实例
        """
        self.collect_devices[device_name] = device_instance
        logger.info(f"注册采集设备: {device_name}")


# 导出所有组件
__all__ = [
    'DataProcessor',
    'MQTTPublisher',
    'HostDevicesProcessor',
    'CollectDevicesProcessor',
    'DeviceDataCollector',
    'DataAggregator'
]