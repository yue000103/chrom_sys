"""
设备数据收集器
定期收集所有设备的数据并发布到MQTT
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DeviceDataCollector:
    """设备数据收集器"""

    def __init__(self, mqtt_publisher, host_processor, collect_processor):
        self.mqtt_publisher = mqtt_publisher
        self.host_processor = host_processor
        self.collect_processor = collect_processor
        self.collection_interval = 1.0  # 数据收集间隔（秒）
        self.is_running = False
        self._collector_task = None
        self.collected_count = 0
        self.hardware_devices = {}  # 存储实际的硬件设备实例

    async def start(self):
        """启动数据收集器"""
        if self.is_running:
            logger.warning("设备数据收集器已在运行")
            return

        self.is_running = True
        await self.mqtt_publisher.start()
        self._collector_task = asyncio.create_task(self._collection_loop())
        logger.info("设备数据收集器已启动")

    async def stop(self):
        """停止数据收集器"""
        self.is_running = False

        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass

        await self.mqtt_publisher.stop()
        logger.info("设备数据收集器已停止")

    def register_hardware_device(self, device_type: str, device_instance):
        """
        注册硬件设备实例
        :param device_type: 设备类型
        :param device_instance: 设备实例
        """
        self.hardware_devices[device_type] = device_instance
        logger.info(f"注册硬件设备: {device_type}")

    async def _collection_loop(self):
        """数据收集循环"""
        try:
            while self.is_running:
                await self._collect_and_publish()
                await asyncio.sleep(self.collection_interval)

        except asyncio.CancelledError:
            logger.info("数据收集循环被取消")
        except Exception as e:
            logger.error(f"数据收集循环错误: {e}")

    async def _collect_and_publish(self):
        """收集并发布所有设备数据"""
        try:
            # 收集主机模块设备数据
            host_data = await self._collect_host_devices_data()

            # 收集收集模块设备数据
            collect_data = await self._collect_collect_devices_data()

            # 合并所有数据
            all_data = host_data + collect_data

            # 发布到MQTT
            for device_data in all_data:
                device_type = device_data.get("device_type")
                device_id = device_data.get("device_id")
                await self.mqtt_publisher.publish_device_data(
                    device_type, device_id, device_data
                )

            self.collected_count += len(all_data)
            logger.debug(f"收集并发布了 {len(all_data)} 个设备数据")

        except Exception as e:
            logger.error(f"数据收集和发布错误: {e}")

    async def _collect_host_devices_data(self) -> List[Dict[str, Any]]:
        """收集主机模块设备数据"""
        devices_data = []

        # 主机设备类型
        host_device_types = [
            ("relay_controller", "RelayController"),
            ("pressure_sensor_ttyAMA0", "PressureSensor"),
            ("detector_ttyAMA3", "DetectorController"),
            ("pump_controller_ttyAMA2", "PumpController"),
            ("bubble_sensor_host", "BubbleSensorHost")
        ]

        for device_id, device_class in host_device_types:
            try:
                device = self.hardware_devices.get(device_id)

                if device is None:
                    # 如果没有注册实际设备，生成模拟数据
                    data = await self._generate_mock_data(device_id, "host")
                else:
                    # 从实际设备获取数据
                    if hasattr(device, 'get_status'):
                        data = await device.get_status()
                    elif hasattr(device, 'get_data_stream'):
                        data = await device.get_data_stream()
                    else:
                        data = {"error": "设备没有数据获取方法"}

                # 处理数据
                device_type = device_id.split('_')[0] if '_' in device_id else device_id
                processed_data = await self.host_processor.process_data({
                    "device_id": device_id,
                    "device_type": device_type,
                    "data": data
                })

                devices_data.append(processed_data)

            except Exception as e:
                logger.error(f"收集{device_id}数据失败: {e}")

        return devices_data

    async def _collect_collect_devices_data(self) -> List[Dict[str, Any]]:
        """收集收集模块设备数据"""
        devices_data = []

        # 收集设备类型
        collect_device_types = [
            ("led_controller", "LEDController"),
            ("valve_controller", "ValveController"),
            ("bubble_sensor_collect", "BubbleSensorCollect"),
            ("multi_valve_controller", "MultiValveController"),
            ("spray_pump_controller", "SprayPumpController")
        ]

        for device_id, device_class in collect_device_types:
            try:
                device = self.hardware_devices.get(device_id)

                if device is None:
                    # 如果没有注册实际设备，生成模拟数据
                    data = await self._generate_mock_data(device_id, "collect")
                else:
                    # 从实际设备获取数据
                    if hasattr(device, 'get_status'):
                        data = await device.get_status()
                    else:
                        data = {"error": "设备没有数据获取方法"}

                # 处理数据
                device_type = device_id.replace('_controller', '')
                processed_data = await self.collect_processor.process_data({
                    "device_id": device_id,
                    "device_type": device_type,
                    "data": data
                })

                devices_data.append(processed_data)

            except Exception as e:
                logger.error(f"收集{device_id}数据失败: {e}")

        return devices_data

    async def _generate_mock_data(self, device_id: str, module_type: str) -> Dict[str, Any]:
        """生成模拟数据"""
        from hardware.hardware_config import MockDataGenerator

        base_data = {
            "device_id": device_id,
            "mode": "mock",
            "status": MockDataGenerator.generate_device_status(),
            "timestamp": datetime.now().isoformat()
        }

        # 根据设备类型生成特定数据
        if "pressure" in device_id:
            base_data["pressure"] = MockDataGenerator.generate_pressure()
            base_data["unit"] = "MPa"
        elif "detector" in device_id:
            base_data["signal"] = MockDataGenerator.generate_signal()
            base_data["wavelength"] = 254.0
        elif "pump" in device_id:
            base_data["flow_rate"] = MockDataGenerator.generate_flow_rate()
            base_data["pressure"] = MockDataGenerator.generate_pressure()
        elif "bubble" in device_id:
            base_data["bubble_detected"] = MockDataGenerator.generate_bubble_status()
        elif "valve" in device_id:
            base_data["position"] = MockDataGenerator.generate_valve_position()
        elif "led" in device_id:
            base_data["status"] = "on" if MockDataGenerator.generate_success_status() else "off"
            base_data["brightness"] = 100

        return base_data

    def set_collection_interval(self, interval: float):
        """
        设置数据收集间隔
        :param interval: 间隔时间（秒）
        """
        if interval > 0:
            self.collection_interval = interval
            logger.info(f"数据收集间隔设置为: {interval}秒")
        else:
            logger.warning("无效的收集间隔，必须大于0")

    def get_statistics(self) -> Dict[str, Any]:
        """获取收集统计信息"""
        return {
            "is_running": self.is_running,
            "collected_count": self.collected_count,
            "collection_interval": self.collection_interval,
            "registered_devices": list(self.hardware_devices.keys()),
            "publisher_stats": self.mqtt_publisher.get_statistics()
        }

    async def collect_specific_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        收集特定设备的数据
        :param device_id: 设备ID
        :return: 设备数据
        """
        device = self.hardware_devices.get(device_id)

        if device:
            try:
                if hasattr(device, 'get_status'):
                    return await device.get_status()
                elif hasattr(device, 'get_data_stream'):
                    return await device.get_data_stream()
            except Exception as e:
                logger.error(f"收集设备{device_id}数据失败: {e}")
                return None
        else:
            # 生成模拟数据
            return await self._generate_mock_data(device_id, "unknown")