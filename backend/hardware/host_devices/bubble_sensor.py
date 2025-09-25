"""
气泡传感器(主机模块)
气1、气2、气3、气4 (4个传感器)
"""

from typing import Dict, Any, List, Optional
import asyncio
try:
    from smbus2 import SMBus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
from ..hardware_config import MockDataGenerator, is_mock_mode


class BubbleSensorHost:
    """主机模块气泡传感器类"""

    def __init__(self, mock: Optional[bool] = None):
        self.device_id = 'bubble_sensor_host'
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.sensors = {
            '气1': {'location': '进样管路', 'status': False, 'bubble_detected': False, 'param': 1},
            '气2': {'location': '流动相A', 'status': False, 'bubble_detected': False, 'param': 2},
            '气3': {'location': '流动相B', 'status': False, 'bubble_detected': False, 'param': 3},
            '气4': {'location': '废液管路', 'status': False, 'bubble_detected': False, 'param': 4}
        }

        # I2C配置
        self.bus_id = 1
        self.addr = 0x20
        self.reg = 0x12
        self.bus = None

        # 传感器参数映射表（按照控制对象映射）
        self.sensor_mapping = {
            '气1': 1,  # 1号气泡传感器
            '气2': 2,  # 2号气泡传感器
            '气3': 3,  # 4号气泡传感器
            '气4': 4   # 3号气泡传感器
        }

    def _init_i2c(self) -> bool:
        """初始化I2C总线"""
        if not SMBUS_AVAILABLE or self.mock:
            return True

        try:
            if self.bus is None:
                self.bus = SMBus(self.bus_id)
            return True
        except Exception:
            return False

    def _read_input_state(self) -> int:
        """读取I2C输入状态"""
        if self.mock:
            # mock模式下返回随机状态
            return 0xFF

        if not self._init_i2c():
            return -1

        try:
            return self.bus.read_byte_data(self.addr, self.reg)
        except Exception:
            return -1

    def _is_bubble_detected(self, pos: int) -> bool:
        """
        判断第pos位（1-8，从右到左）是否为1
        :param pos: 位置（1-8），1为最右边
        :return: True/False
        """
        if not (1 <= pos <= 8):
            return False

        state = self._read_input_state()
        if state == -1:
            return False

        return bool((state >> (pos - 1)) & 1)
    
    async def initialize(self) -> bool:
        """初始化气泡传感器"""
        if self.mock:
            for sensor_id in self.sensors:
                self.sensors[sensor_id]['status'] = True
            await asyncio.sleep(0.2)
            return True
        else:
            # 初始化I2C总线
            init_success = self._init_i2c()
            if init_success:
                for sensor_id in self.sensors:
                    self.sensors[sensor_id]['status'] = True

            await asyncio.sleep(0.2)
            return init_success
    
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
            if sensor_id not in self.sensors:
                return {}

            sensor = self.sensors[sensor_id].copy()
            pos = self.sensor_mapping.get(sensor_id)

            if pos is not None:
                # 使用I2C读取气泡状态
                bubble_detected = self._is_bubble_detected(pos)
                sensor['bubble_detected'] = bubble_detected
                sensor['status'] = self._read_input_state() != -1  # 通信是否成功
            else:
                sensor['bubble_detected'] = False
                sensor['status'] = False

            await asyncio.sleep(0.01)
            return sensor
    
    async def read_all_sensors(self) -> Dict[str, Dict[str, Any]]:
        """读取所有传感器状态"""
        if self.mock:
            all_status = {}
            for sensor_id in self.sensors:
                all_status[sensor_id] = await self.read_sensor(sensor_id)
            return all_status
        else:
            # 一次性读取所有传感器状态，提高效率
            input_state = self._read_input_state()
            all_status = {}

            for sensor_id in self.sensors:
                sensor = self.sensors[sensor_id].copy()
                pos = self.sensor_mapping.get(sensor_id)

                if pos is not None and input_state != -1:
                    bubble_detected = bool((input_state >> (pos - 1)) & 1)
                    sensor['bubble_detected'] = bubble_detected
                    sensor['status'] = True
                else:
                    sensor['bubble_detected'] = False
                    sensor['status'] = False

                all_status[sensor_id] = sensor

            await asyncio.sleep(0.01)
            return all_status
    
    async def monitor_bubbles(self, callback=None):
        """
        持续监测气泡
        :param callback: 检测到气泡时的回调函数
        """
        while True:
            try:
                all_status = await self.read_all_sensors()

                # 检查是否有传感器检测到气泡
                for sensor_id, sensor_data in all_status.items():
                    if sensor_data.get('bubble_detected', False):
                        if callback:
                            await callback(sensor_id, sensor_data)

                await asyncio.sleep(1)  # 每秒检测一次
            except Exception as e:
                print(f"监测气泡时发生错误: {e}")
                await asyncio.sleep(1)
    
    async def reset_sensor(self, sensor_id: str) -> bool:
        """重置传感器"""
        if sensor_id not in self.sensors:
            return False

        if self.mock:
            await asyncio.sleep(0.1)
            return MockDataGenerator.generate_success_status()
        else:
            # 对于I2C传感器，重置主要是重新初始化连接
            try:
                init_success = self._init_i2c()
                if init_success and sensor_id in self.sensors:
                    self.sensors[sensor_id]['status'] = True
                    await asyncio.sleep(0.1)
                    return True
                return False
            except Exception:
                return False

    async def get_alarm_status(self) -> List[str]:
        """获取告警状态"""
        if self.mock:
            alarms = []
            for sensor_id, sensor in self.sensors.items():
                if MockDataGenerator.generate_bubble_status():
                    alarms.append(f'{sensor_id}: 检测到气泡于{sensor["location"]}')
            return alarms
        else:
            alarms = []
            all_status = await self.read_all_sensors()

            for sensor_id, sensor_data in all_status.items():
                if sensor_data.get('bubble_detected', False):
                    location = sensor_data.get('location', '未知位置')
                    alarms.append(f'{sensor_id}: 检测到气泡于{location}')

            return alarms

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock