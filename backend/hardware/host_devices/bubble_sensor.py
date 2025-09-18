"""
气泡传感器(主机模块)
气1、气2、气3、气4 (4个传感器)
"""

from typing import Dict, Any, List, Optional
import asyncio
from ..hardware_config import MockDataGenerator, is_mock_mode


class BubbleSensorHost:
    """主机模块气泡传感器类"""
    
    def __init__(self, mock: Optional[bool] = None):
        self.device_id = 'bubble_sensor_host'
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.sensors = {
            '气1': {'location': '进样管路', 'status': False, 'bubble_detected': False},
            '气2': {'location': '流动相A', 'status': False, 'bubble_detected': False},
            '气3': {'location': '流动相B', 'status': False, 'bubble_detected': False},
            '气4': {'location': '废液管路', 'status': False, 'bubble_detected': False}
        }
    
    async def initialize(self) -> bool:
        """初始化气泡传感器"""
        if self.mock:
            for sensor_id in self.sensors:
                self.sensors[sensor_id]['status'] = True
            await asyncio.sleep(0.2)
            return True
        else:
            pass
    
    async def read_sensor(self, sensor_id: str) -> Dict[str, Any]:
        """
        读取单个传感器状态
        :param sensor_id: 传感器ID(气1/气2/气3/气4)
        :return: 传感器状态
        """
        if self.mock:
            if sensor_id in self.sensors:
                sensor = self.sensors[sensor_id].copy()
                sensor['bubble_detected'] = MockDataGenerator.generate_bubble_status()
                await asyncio.sleep(0.01)
                return sensor
            return {}
        else:
            pass
    
    async def read_all_sensors(self) -> Dict[str, Dict[str, Any]]:
        """读取所有传感器状态"""
        if self.mock:
            all_status = {}
            for sensor_id in self.sensors:
                all_status[sensor_id] = await self.read_sensor(sensor_id)
            return all_status
        else:
            pass
    
    async def monitor_bubbles(self, callback=None):
        """
        持续监测气泡
        :param callback: 检测到气泡时的回调函数
        """
        pass
    
    async def reset_sensor(self, sensor_id: str) -> bool:
        """重置传感器"""
        pass
    
    async def get_alarm_status(self) -> List[str]:
        """获取告警状态"""
        if self.mock:
            alarms = []
            for sensor_id, sensor in self.sensors.items():
                if MockDataGenerator.generate_bubble_status():
                    alarms.append(f'{sensor_id}: 检测到气泡于{sensor["location"]}')
            return alarms
        else:
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock