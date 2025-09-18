"""
气泡传感器(收集模块)
气5、气6、气7 (3个传感器)
"""

from typing import Dict, Any, List, Optional
import asyncio
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
            pass
    
    async def read_all_status(self) -> Dict[str, Dict[str, Any]]:
        """读取所有传感器状态"""
        if self.mock:
            all_status = {}
            for sensor_id in self.sensors:
                all_status[sensor_id] = await self.read_sensor_status(sensor_id)
            return all_status
        else:
            pass

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
        pass
    
    async def calibrate_sensor(self, sensor_id: str) -> bool:
        """校准传感器"""
        pass
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass