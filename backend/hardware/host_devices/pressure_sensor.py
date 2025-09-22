"""
压力传感器
ttyAMA0接口，波特率9600
"""

from typing import Dict, Any, Optional
import asyncio
import time
from ..hardware_config import MockDataGenerator, is_mock_mode


class PressureSensor:
    """压力传感器类"""

    def __init__(self, port: str = 'ttyAMA0', baudrate: int = 9600, mock: Optional[bool] = None):
        self.device_id = f'pressure_sensor_{port}'
        self.port = port
        self.baudrate = baudrate
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.connection = None
        self.current_pressure = 0.0
        self.is_connected = False
        self.calibration_offset = 0.0

    async def connect(self) -> bool:
        """连接传感器"""
        if self.mock:
            # Mock模式下模拟连接
            await asyncio.sleep(0.2)  # 模拟连接延时
            self.is_connected = True
            self.current_pressure = MockDataGenerator.generate_pressure()
            return True
        else:
            # 实际串口连接
            pass

    async def read_pressure(self) -> float:
        """
        读取当前压力值
        :return: 压力值(MPa)
        """
        if self.mock:
            # Mock模式下生成模拟压力值
            if not self.is_connected:
                raise Exception("传感器未连接")
            # 模拟压力波动
            self.current_pressure = MockDataGenerator.generate_pressure(0.5, 8.0)
            await asyncio.sleep(0.01)  # 模拟读取延时
            return self.current_pressure + self.calibration_offset
        else:
            # 实际硬件读取
            pass

    async def calibrate(self, calibration_params: Dict[str, Any]) -> bool:
        """
        校准传感器
        :param calibration_params: 校准参数
        :return: 校准结果
        """
        if self.mock:
            # Mock模式下模拟校准
            self.calibration_offset = calibration_params.get('offset', 0.0)
            await asyncio.sleep(0.5)  # 模拟校准延时
            return MockDataGenerator.generate_success_status()
        else:
            # 实际硬件校准
            pass

    async def get_data_stream(self) -> Dict[str, Any]:
        """获取实时数据流"""
        if self.mock:
            # Mock模式下返回模拟数据流
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'timestamp': time.time(),
                'pressure': await self.read_pressure(),
                'unit': 'MPa',
                'status': 'normal' if self.is_connected else 'disconnected',
                'port': self.port,
                'baudrate': self.baudrate
            }
        else:
            # 实际硬件数据流
            pass

    async def disconnect(self) -> bool:
        """断开连接"""
        if self.mock:
            # Mock模式下模拟断开
            self.is_connected = False
            await asyncio.sleep(0.1)  # 模拟断开延时
            return True
        else:
            # 实际硬件断开
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock

    async def get_pressure(self) -> float:
        """
        获取当前压力值（兼容方法名）
        :return: 压力值(MPa)
        """
        return await self.read_pressure()