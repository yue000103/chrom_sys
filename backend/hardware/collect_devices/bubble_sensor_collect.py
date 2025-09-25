"""
气泡传感器(收集模块)
气5、气6、气7 (3个传感器)
"""

from typing import Dict, Any, List, Optional
import asyncio
import requests
from ..hardware_config import MockDataGenerator, is_mock_mode


class BubbleSensorCollect:
    """收集模块气泡传感器类"""

    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'bubble_sensor_collect'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.sensors = {
            '气5': {'location': '收集管路1', 'status': False, 'bubble_detected': False},
            '气6': {'location': '收集管路2', 'status': False, 'bubble_detected': False},
            '气7': {'location': '收集管路3', 'status': False, 'bubble_detected': False}
        }
        # 传感器状态对照表：检测到液体时的返回值
        self.sensor_detection_values = {
            '气5': 0b11110100,  # 244
            '气6': 0b11110010,  # 242
            '气7': 0b11110001   # 241
        }

    def _get_bubble_status_from_hardware(self) -> int:
        """从硬件获取气泡状态数据"""
        try:
            url = f"{self.base_url}/device/data"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get('data', -1)
            return -1
        except:
            return -1

    def _parse_sensor_data(self, raw_data: int, sensor_id: str) -> bool:
        """解析传感器数据，判断是否检测到液体"""
        if raw_data == -1:
            return False

        # 根据传感器ID获取对应的检测值
        detection_value = self.sensor_detection_values.get(sensor_id)
        if detection_value is None:
            return False

        # 如果原始数据等于检测值，则说明检测到液体（气泡）
        return raw_data == detection_value
    
    async def read_sensor_status(self, sensor_id: str) -> Dict[str, Any]:
        """
        读取传感器状态
        :param sensor_id: 传感器ID(气5/气6/气7)
        :return: 传感器状态
        """
        if self.mock:
            if sensor_id in self.sensors:
                sensor = self.sensors[sensor_id].copy()
                sensor['status'] = True
                sensor['bubble_detected'] = MockDataGenerator.generate_bubble_status()
                await asyncio.sleep(0.01)
                return sensor
            return {}
        else:
            if sensor_id not in self.sensors:
                return {}

            # 从硬件获取数据
            raw_data = self._get_bubble_status_from_hardware()
            bubble_detected = self._parse_sensor_data(raw_data, sensor_id)

            sensor = self.sensors[sensor_id].copy()
            sensor['status'] = raw_data != -1  # 通信是否成功
            sensor['bubble_detected'] = bubble_detected
            sensor['raw_data'] = raw_data

            await asyncio.sleep(0.01)
            return sensor
    
    async def read_all_status(self) -> Dict[str, Dict[str, Any]]:
        """读取所有传感器状态"""
        if self.mock:
            all_status = {}
            for sensor_id in self.sensors:
                all_status[sensor_id] = await self.read_sensor_status(sensor_id)
            return all_status
        else:
            # 从硬件获取一次数据，然后解析所有传感器状态
            raw_data = self._get_bubble_status_from_hardware()
            all_status = {}

            for sensor_id in self.sensors:
                bubble_detected = self._parse_sensor_data(raw_data, sensor_id)
                sensor = self.sensors[sensor_id].copy()
                sensor['status'] = raw_data != -1
                sensor['bubble_detected'] = bubble_detected
                sensor['raw_data'] = raw_data
                all_status[sensor_id] = sensor

            await asyncio.sleep(0.01)
            return all_status

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock
    
    async def monitor_bubbles(self, callback=None):
        """
        持续监测气泡
        :param callback: 检测到气泡时的回调函数
        """
        while True:
            try:
                all_status = await self.read_all_status()

                # 检查是否有传感器检测到气泡
                for sensor_id, sensor_data in all_status.items():
                    if sensor_data.get('bubble_detected', False):
                        if callback:
                            await callback(sensor_id, sensor_data)

                await asyncio.sleep(1)  # 每秒检测一次
            except Exception as e:
                print(f"监测气泡时发生错误: {e}")
                await asyncio.sleep(1)

    async def calibrate_sensor(self, sensor_id: str) -> bool:
        """校准传感器"""
        if sensor_id not in self.sensors:
            return False

        if self.mock:
            await asyncio.sleep(0.5)  # 模拟校准时间
            return MockDataGenerator.generate_success_status()
        else:
            # 实际硬件校准逻辑可以在这里实现
            # 目前只是读取状态验证通信
            status = await self.read_sensor_status(sensor_id)
            return status.get('status', False)

    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_status = await self.read_all_status()

        stats = {
            'total_sensors': len(self.sensors),
            'active_sensors': 0,
            'sensors_with_bubbles': 0,
            'sensor_details': {}
        }

        for sensor_id, sensor_data in all_status.items():
            if sensor_data.get('status', False):
                stats['active_sensors'] += 1
            if sensor_data.get('bubble_detected', False):
                stats['sensors_with_bubbles'] += 1

            stats['sensor_details'][sensor_id] = {
                'location': sensor_data.get('location', ''),
                'status': sensor_data.get('status', False),
                'bubble_detected': sensor_data.get('bubble_detected', False)
            }

        return stats