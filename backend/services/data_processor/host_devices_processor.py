"""
主机设备数据处理器
自主管理设备数据采集和MQTT发布
每秒调用一次get_signal等方法，并发布到MQTT
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class HostDevicesProcessor(BaseProcessor):
    """主机设备数据处理器 - 自主管理数据采集和发布"""

    def __init__(self, mqtt_manager=None):
        super().__init__("HostDevicesProcessor")
        self.mqtt_manager = mqtt_manager
        self.devices = {}  # 存储注册的设备实例
        self.latest_data = {}  # 存储每个设备的最新数据
        self.is_running = False
        self.collection_task = None
        self.collection_interval = 1.0  # 默认1秒采集一次

    def register_device(self, device_name: str, device_instance):
        """
        注册设备实例
        :param device_name: 设备名称/ID
        :param device_instance: 设备实例对象
        """
        self.devices[device_name] = device_instance
        logger.info(f"注册设备: {device_name} -> {device_instance.__class__.__name__}")

    async def start(self):
        """启动自主数据采集"""
        if self.is_running:
            logger.warning("HostDevicesProcessor已在运行")
            return

        self.is_running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("HostDevicesProcessor数据采集已启动")

    async def stop(self):
        """停止数据采集"""
        self.is_running = False

        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        logger.info("HostDevicesProcessor数据采集已停止")

    async def _collection_loop(self):
        """数据采集主循环 - 每秒执行一次"""
        logger.info(f"开始数据采集循环，间隔: {self.collection_interval}秒")

        while self.is_running:
            try:
                # 采集所有设备数据
                await self._collect_and_publish_all()

                # 等待下一个采集周期
                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                logger.info("数据采集循环被取消")
                break
            except Exception as e:
                logger.error(f"数据采集循环出错: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_and_publish_all(self):
        """采集并发布所有设备数据"""
        for device_name, device in self.devices.items():
            try:
                # 根据设备类型采集数据
                device_type = device.__class__.__name__.lower()

                if 'detector' in device_type:
                    await self._collect_detector_data(device_name, device)
                elif 'pressure' in device_type:
                    await self._collect_pressure_data(device_name, device)
                elif 'pump' in device_type:
                    await self._collect_pump_data(device_name, device)
                elif 'relay' in device_type:
                    await self._collect_relay_data(device_name, device)
                elif 'bubble' in device_type:
                    await self._collect_bubble_data(device_name, device)
                else:
                    # 通用数据采集
                    await self._collect_generic_data(device_name, device)

            except Exception as e:
                logger.error(f"采集设备 {device_name} 数据时出错: {e}")

    async def _collect_detector_data(self, device_name: str, detector):
        """采集并发布检测器数据"""
        try:
            # 检查设备是否在检测状态
            if not hasattr(detector, 'is_detecting') or not detector.is_detecting:
                return

            # 调用get_signal获取双通道信号
            if hasattr(detector, 'get_signal'):
                signals = await detector.get_signal()

                # 获取波长信息
                wavelengths = [
                    getattr(detector, 'wavelength_a', 254),
                    getattr(detector, 'wavelength_b', 280)
                ]

                # 构建数据
                timestamp = datetime.now().isoformat()
                retention_time = getattr(detector, 'mock_time', 0) / 60 if hasattr(detector, 'mock_time') else 0

                # 存储最新数据供API调用
                detector_data = {
                    "device_id": device_name,
                    "device_type": "detector",
                    "signal": signals,  # [A, B]
                    "wavelength": wavelengths,  # [254, 280]
                    "channel_a": {
                        "wavelength": wavelengths[0],
                        "signal": signals[0] if isinstance(signals, list) else signals,
                        "unit": "mAU"
                    },
                    "channel_b": {
                        "wavelength": wavelengths[1] if len(wavelengths) > 1 else 280,
                        "signal": signals[1] if isinstance(signals, list) and len(signals) > 1 else 0,
                        "unit": "mAU"
                    },
                    "retention_time": round(retention_time, 2),
                    "timestamp": timestamp,
                    "is_detecting": detector.is_detecting
                }

                # 存储到最新数据字典
                self.latest_data[device_name] = detector_data

                # 只发布信号数据到MQTT（不发布波长和通道数据）
                if self.mqtt_manager:
                    # 只发布双通道信号 [A, B]
                    await self.mqtt_manager.publish(
                        f"chromatography/detector/{device_name}/signal",
                        signals
                    )

                    # 发布保留时间
                    await self.mqtt_manager.publish(
                        f"chromatography/detector/{device_name}/retention_time",
                        {
                            "retention_time": round(retention_time, 2),
                            "unit": "min",
                            "timestamp": timestamp
                        }
                    )

                    logger.debug(f"发布检测器数据: {device_name} -> 信号={signals}, 波长={wavelengths}")

        except Exception as e:
            logger.error(f"采集检测器 {device_name} 数据时出错: {e}")

    async def _collect_pressure_data(self, device_name: str, pressure_sensor):
        """采集并发布压力传感器数据"""
        try:
            if hasattr(pressure_sensor, 'get_pressure'):
                pressure = await pressure_sensor.get_pressure()

                if self.mqtt_manager:
                    await self.mqtt_manager.publish(
                        f"chromatography/pressure/{device_name}/value",
                        {
                            "pressure": pressure,
                            "unit": "MPa",
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                logger.debug(f"发布压力数据: {device_name} -> {pressure} MPa")

        except Exception as e:
            logger.error(f"采集压力传感器 {device_name} 数据时出错: {e}")

    async def _collect_pump_data(self, device_name: str, pump):
        """采集并发布泵数据"""
        try:
            if hasattr(pump, 'get_status'):
                status = await pump.get_status()

                if self.mqtt_manager:
                    await self.mqtt_manager.publish(
                        f"chromatography/pump/{device_name}/status",
                        status
                    )

                logger.debug(f"发布泵状态: {device_name}")

        except Exception as e:
            logger.error(f"采集泵 {device_name} 数据时出错: {e}")

    async def _collect_relay_data(self, device_name: str, relay):
        """采集并发布继电器数据"""
        try:
            if hasattr(relay, 'get_all_status'):
                status = relay.get_all_status()

                if self.mqtt_manager:
                    await self.mqtt_manager.publish(
                        f"chromatography/relay/{device_name}/status",
                        status
                    )

                logger.debug(f"发布继电器状态: {device_name}")

        except Exception as e:
            logger.error(f"采集继电器 {device_name} 数据时出错: {e}")

    async def _collect_bubble_data(self, device_name: str, bubble_sensor):
        """采集并发布气泡传感器数据"""
        try:
            if hasattr(bubble_sensor, 'get_bubble_status'):
                status = await bubble_sensor.get_bubble_status()

                if self.mqtt_manager:
                    await self.mqtt_manager.publish(
                        f"chromatography/bubble/{device_name}/status",
                        {
                            "bubble_detected": status,
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                logger.debug(f"发布气泡状态: {device_name} -> {status}")

        except Exception as e:
            logger.error(f"采集气泡传感器 {device_name} 数据时出错: {e}")

    async def _collect_generic_data(self, device_name: str, device):
        """通用数据采集"""
        try:
            # 尝试调用get_status方法
            if hasattr(device, 'get_status'):
                status = await device.get_status()

                if self.mqtt_manager:
                    device_type = device.__class__.__name__.lower()
                    await self.mqtt_manager.publish(
                        f"chromatography/{device_type}/{device_name}/status",
                        status
                    )

                logger.debug(f"发布设备状态: {device_name}")

        except Exception as e:
            logger.error(f"采集设备 {device_name} 数据时出错: {e}")

    def set_collection_interval(self, interval: float):
        """设置数据采集间隔"""
        if interval > 0:
            self.collection_interval = interval
            logger.info(f"数据采集间隔设置为: {interval}秒")
        else:
            logger.warning("无效的采集间隔，必须大于0")

    def get_device_data(self, device_name: str = None) -> Dict[str, Any]:
        """
        获取设备的最新数据
        :param device_name: 设备名称，为None则返回所有设备数据
        :return: 设备数据
        """
        if device_name:
            return self.latest_data.get(device_name, {})
        else:
            return self.latest_data.copy()

    def get_detector_data(self, device_name: str = "detector_1") -> Dict[str, Any]:
        """
        获取检测器的完整数据（专门为API提供）
        :param device_name: 检测器名称
        :return: 包含波长、A/B通道、信号等完整数据
        """
        data = self.latest_data.get(device_name, {})
        if not data:
            # 返回默认值
            return {
                "device_id": device_name,
                "device_type": "detector",
                "signal": [0.0, 0.0],
                "wavelength": [254, 280],
                "channel_a": {"wavelength": 254, "signal": 0.0, "unit": "mAU"},
                "channel_b": {"wavelength": 280, "signal": 0.0, "unit": "mAU"},
                "retention_time": 0.0,
                "is_detecting": False,
                "timestamp": datetime.now().isoformat()
            }
        return data

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_running": self.is_running,
            "device_count": len(self.devices),
            "devices": list(self.devices.keys()),
            "collection_interval": self.collection_interval,
            "processed_count": self.processed_count,
            "last_process_time": self.last_process_time.isoformat() if self.last_process_time else None,
            "latest_data_count": len(self.latest_data)
        }

    # 保留原有的process_data方法以保持兼容性
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理主机设备数据（兼容旧接口）"""
        return data