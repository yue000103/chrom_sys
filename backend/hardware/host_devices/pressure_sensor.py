"""
压力传感器
ttyAMA0接口，波特率9600
"""

from typing import Dict, Any, Optional
import asyncio
import time
import serial
from ..hardware_config import MockDataGenerator, is_mock_mode


class PressureSensor:
    """压力传感器类"""

    def __init__(self, port: str = 'ttyAMA0', baudrate: int = 9600, mock: Optional[bool] = None):
        self.device_id = f'pressure_sensor_{port}'
        self.port = f'/dev/{port}' if not port.startswith('/dev/') else port
        self.baudrate = baudrate
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.connection = None
        self.current_pressure = 0.0
        self.is_connected = False
        self.calibration_offset = 0.0
        self.timeout = 5.0

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
            try:
                self.connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                self.is_connected = True
                return True
            except Exception:
                self.is_connected = False
                return False

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
            if not self.connection or not self.connection.is_open:
                raise Exception("传感器未连接")

            pressure = await self._read_pressure_sync()
            if pressure is not None:
                self.current_pressure = pressure + self.calibration_offset
                return self.current_pressure
            else:
                raise Exception("读取压力值失败")

    def _send_command(self, hex_command: str) -> Optional[str]:
        """发送命令到传感器"""
        if not self.connection or not self.connection.is_open:
            return None

        try:
            cmd_bytes = bytes.fromhex(hex_command.replace(" ", ""))
            self.connection.reset_input_buffer()
            self.connection.write(cmd_bytes)
            self.connection.flush()

            time.sleep(0.1)
            response = b""
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.connection.in_waiting > 0:
                    response += self.connection.read(self.connection.in_waiting)
                    if len(response) >= 3:
                        if len(response) >= response[2] + 5:
                            break
                time.sleep(0.01)

            if response:
                return response.hex().upper()
            return None
        except Exception:
            return None

    async def _read_pressure_sync(self) -> Optional[float]:
        """同步读取压力值"""
        send_cmd = "01 03 00 00 00 01 84 0A"
        response_hex = self._send_command(send_cmd)
        if not response_hex:
            return None

        try:
            data_bytes = bytes.fromhex(response_hex)
            if len(data_bytes) < 5:
                return None
            if data_bytes[0] != 0x01 or data_bytes[1] != 0x03 or data_bytes[2] != 0x02:
                return None

            data_value = (data_bytes[3] << 8) | data_bytes[4]
            pressure = (1.6 * data_value) / 2000
            return pressure
        except Exception:
            return None

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
            try:
                pressure = await self.read_pressure()
                return {
                    'device_id': self.device_id,
                    'mode': 'hardware',
                    'timestamp': time.time(),
                    'pressure': pressure,
                    'unit': 'MPa',
                    'status': 'normal' if self.is_connected else 'disconnected',
                    'port': self.port,
                    'baudrate': self.baudrate
                }
            except Exception:
                return {
                    'device_id': self.device_id,
                    'mode': 'hardware',
                    'timestamp': time.time(),
                    'pressure': None,
                    'unit': 'MPa',
                    'status': 'error',
                    'port': self.port,
                    'baudrate': self.baudrate
                }

    async def disconnect(self) -> bool:
        """断开连接"""
        if self.mock:
            # Mock模式下模拟断开
            self.is_connected = False
            await asyncio.sleep(0.1)  # 模拟断开延时
            return True
        else:
            # 实际硬件断开
            try:
                if self.connection and self.connection.is_open:
                    self.connection.close()
                self.is_connected = False
                return True
            except Exception:
                return False

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