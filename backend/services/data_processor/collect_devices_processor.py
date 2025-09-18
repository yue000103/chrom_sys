"""
收集设备数据处理器
处理所有收集模块设备的数据
"""

from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class CollectDevicesProcessor(BaseProcessor):
    """收集设备数据处理器"""

    def __init__(self):
        super().__init__("CollectDevicesProcessor")
        self.device_handlers = {
            "led_controller": self._process_led_data,
            "led": self._process_led_data,
            "valve_controller": self._process_valve_data,
            "valve": self._process_valve_data,
            "bubble_sensor_collect": self._process_bubble_data,
            "bubble": self._process_bubble_data,
            "multi_valve_controller": self._process_multi_valve_data,
            "multi_valve": self._process_multi_valve_data,
            "spray_pump_controller": self._process_spray_pump_data,
            "spray_pump": self._process_spray_pump_data
        }

    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理收集设备数据"""
        try:
            if not self.validate_data(data):
                raise ValueError("数据验证失败")

            device_type = data.get("device_type")
            handler = self.device_handlers.get(device_type)

            if handler:
                processed_data = await handler(data)
                self.processed_count += 1
                self.last_process_time = datetime.now()
                return processed_data
            else:
                raise ValueError(f"未知的设备类型: {device_type}")

        except Exception as e:
            return await self.handle_error(e, data)

    async def _process_led_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理LED控制器数据"""
        device_id = data.get("device_id", "led_controller")
        raw_data = data.get("data", {})

        processed_data = self.format_data(
            device_id=device_id,
            device_type="led_controller",
            data={
                "status": raw_data.get("status", "off"),
                "brightness": raw_data.get("brightness", 0),
                "base_url": raw_data.get("base_url", "http://192.168.1.129")
            },
            status=raw_data.get("status", "normal"),
            mode=raw_data.get("mode", "online")
        )

        return processed_data

    async def _process_valve_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理阀门控制器数据"""
        device_id = data.get("device_id", "valve_controller")
        raw_data = data.get("data", {})

        # 处理每个阀门的状态
        valves_data = {}
        for valve_id, valve_info in raw_data.get("valves", {}).items():
            valves_data[valve_id] = {
                "name": valve_info.get("name"),
                "status": valve_info.get("status", "closed"),
                "timestamp": datetime.now().isoformat()
            }

        # 检查是否有阀门处于打开状态
        any_open = any(
            v["status"] in ["opened", "running", "position_2"]
            for v in valves_data.values()
        )
        system_status = "active" if any_open else "idle"

        processed_data = self.format_data(
            device_id=device_id,
            device_type="valve_controller",
            data={
                "valves": valves_data,
                "base_url": raw_data.get("base_url", "http://192.168.1.129"),
                "system_status": system_status
            },
            status=system_status,
            mode=raw_data.get("mode", "online")
        )

        return processed_data

    async def _process_bubble_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理收集模块气泡传感器数据"""
        device_id = data.get("device_id", "bubble_sensor_collect")
        raw_data = data.get("data", {})

        # 处理每个传感器的数据
        sensors_data = {}
        bubble_detected_count = 0

        for sensor_id, sensor_info in raw_data.get("sensors", {}).items():
            bubble_detected = sensor_info.get("bubble_detected", False)
            if bubble_detected:
                bubble_detected_count += 1

            sensors_data[sensor_id] = {
                "location": sensor_info.get("location"),
                "bubble_detected": bubble_detected,
                "status": sensor_info.get("status", False),
                "timestamp": datetime.now().isoformat()
            }

        # 系统告警状态
        alert_status = "normal"
        if bubble_detected_count > 0:
            alert_status = f"bubble_detected_{bubble_detected_count}"

        processed_data = self.format_data(
            device_id=device_id,
            device_type="bubble_sensor_collect",
            data={
                "sensors": sensors_data,
                "bubble_count": bubble_detected_count,
                "base_url": raw_data.get("base_url", "http://192.168.1.129"),
                "alert_status": alert_status
            },
            status=alert_status,
            mode=raw_data.get("mode", "online")
        )

        return processed_data

    async def _process_multi_valve_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多向阀数据"""
        device_id = data.get("device_id", "multi_valve_controller")
        raw_data = data.get("data", {})

        # 处理每个多向阀的数据
        valves_data = {}
        for valve_id, valve_info in raw_data.get("valves", {}).items():
            valves_data[valve_id] = {
                "positions": valve_info.get("positions", 6),
                "current_position": valve_info.get("current_position", 1),
                "status": valve_info.get("status", "idle"),
                "timestamp": datetime.now().isoformat()
            }

        # 检查是否有阀门在移动
        any_moving = any(v["status"] == "moving" for v in valves_data.values())
        system_status = "moving" if any_moving else "idle"

        processed_data = self.format_data(
            device_id=device_id,
            device_type="multi_valve",
            data={
                "valves": valves_data,
                "base_url": raw_data.get("base_url", "http://192.168.1.129"),
                "system_status": system_status
            },
            status=system_status,
            mode=raw_data.get("mode", "online")
        )

        return processed_data

    async def _process_spray_pump_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理隔膜泵数据"""
        device_id = data.get("device_id", "spray_pump_controller")
        raw_data = data.get("data", {})

        pump_data = raw_data.get("pump", {})

        # 计算累计运行时间和体积
        runtime = pump_data.get("runtime", 0)
        total_volume = pump_data.get("total_volume", 0.0)

        processed_data = self.format_data(
            device_id=device_id,
            device_type="spray_pump",
            data={
                "status": pump_data.get("status", "stopped"),
                "flow_rate": pump_data.get("flow_rate", 0.0),
                "pressure": pump_data.get("pressure", 0.0),
                "runtime": runtime,
                "total_volume": total_volume,
                "base_url": raw_data.get("base_url", "http://192.168.1.129"),
                "unit_flow": "mL/min",
                "unit_pressure": "MPa"
            },
            status=pump_data.get("status", "stopped"),
            mode=raw_data.get("mode", "online")
        )

        return processed_data

    async def collect_all_collect_devices_data(self, hardware_manager) -> List[Dict[str, Any]]:
        """收集所有收集模块设备的数据"""
        devices_data = []

        # 这里应该调用实际的硬件设备获取数据
        # 示例代码，实际使用时需要导入并调用硬件设备
        device_types = [
            "led_controller",
            "valve_controller",
            "bubble_sensor_collect",
            "multi_valve",
            "spray_pump"
        ]

        for device_type in device_types:
            try:
                # 模拟获取设备数据
                mock_data = {
                    "device_id": f"{device_type}_01",
                    "device_type": device_type,
                    "data": {
                        "mode": "mock",
                        "status": "normal"
                    }
                }
                processed_data = await self.process_data(mock_data)
                devices_data.append(processed_data)

            except Exception as e:
                logger.error(f"收集{device_type}数据失败: {e}")

        return devices_data