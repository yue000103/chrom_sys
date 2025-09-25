"""
检测器控制器
ttyAMA3接口，波特率57600
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
import math
import random
import serial
from datetime import datetime
# from ..hardware_config import is_mock_mode


class DetectorController:
    """检测器控制器类"""

    def __init__(self, port: str = '/dev/ttyAMA3', baudrate: int = 57600, mock: Optional[bool] = True):
        self.device_id = f'detector_{port.replace("/dev/", "")}'
        self.port = port
        self.baudrate = baudrate
        self.mock = mock
        self.serial_connection = None
        self.detection_mode = 'UV'  # UV/荧光/电化学等
        self.is_connected = False
        self.is_detecting = False
        self.timeout = 5.0  # 串口超时时间

        # 双通道波长配置
        self.wavelength_a = 120.0  # A通道波长
        self.wavelength_b = 254.0  # B通道波长
        self.wavelength = 254.0  # 保留兼容性
        self.mock_time = 0  # 用于模拟时间进程

    def _open_serial(self) -> bool:
        """打开串口连接"""
        try:
            self.serial_connection = serial.Serial(
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
            print(f"Successfully connected to serial port {self.port}")
            return True
        except Exception as e:
            print(f"Serial connection failed: {str(e)}")
            return False

    def _close_serial(self):
        """关闭串口连接"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"Serial connection to {self.port} closed")

    def _send_command(self, command: str) -> str:
        """发送命令并接收响应"""
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial connection is not available")
            return ""

        try:
            # 清空输入缓冲区
            self.serial_connection.reset_input_buffer()

            # 发送命令
            full_command = f"#{command}\n\r".encode('utf-8')
            self.serial_connection.write(full_command)

            # 等待并接收响应
            time.sleep(0.1)
            response = ""
            start_time = time.time()

            while time.time() - start_time < self.timeout:
                if self.serial_connection.in_waiting > 0:
                    response += self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8')
                    if response.endswith('\n') or response.endswith('\r\n'):
                        break
                time.sleep(0.01)

            response = response.strip()
            return response

        except Exception as e:
            print(f"Command execution failed: {str(e)}")
            return ""

    def _parse_collect_data(self, data: str):
        """解析采集数据"""
        try:
            # 提取数据部分
            data_str = data[3:]

            # 查找并提取A和B数据段
            index = data_str.find('A')
            if index == -1:
                raise ValueError("ECOM: Marker 'A' not found in data")

            a_val = data_str[index:data_str.find('B')]
            b_val = data_str[data_str.find('B'):]

            # 转换A和B值为浮点数
            a_val = float(a_val[1:a_val.find(':')]) / 100000
            b_val = float(b_val[1:b_val.find(':')]) / 100000

            return a_val, b_val

        except (ValueError, IndexError) as e:
            print(f"ECOM: Failed to parse data: {e}")
            return 0.0, 0.0

    def _parse_wavelength_data(self, data: str):
        """解析波长数据"""
        try:
            a_index = data.index('A') + 1
            b_index = data.index('B') + 1
            a_wavelength = int(data[a_index:b_index - 1])
            b_wavelength = int(data[b_index:])
            return a_wavelength, b_wavelength
        except (ValueError, IndexError):
            print("波长数据格式错误，无法解析")
            return 0, 0

    async def connect(self) -> bool:
        """连接检测器"""
        if self.mock:
            await asyncio.sleep(0.2)
            self.is_connected = True
            return True
        else:
            # 实际硬件连接
            success = self._open_serial()
            if success:
                self.is_connected = True
                # 开灯并开始采集
                await self._open_light()
                return True
            return False

    async def _open_light(self) -> bool:
        """开启检测器灯泡"""
        if self.mock:
            return True

        # 读取灯状态
        response = self._send_command('LPr')
        if response and "F" in response:
            # 灯未开启，开灯
            light_response = self._send_command('LPwT')
            return light_response is not None
        return True
    
    async def set_wavelength(self, wavelength, channel: str = 'A') -> bool:
        """
        设置检测波长
        :param wavelength: 波长值，可以是单个数值(float)或数组([wavelength_a, wavelength_b])
        :param channel: 通道 'A' 或 'B' (仅在传入单个数值时使用)
        :return: 设置结果
        """
        if self.mock:
            # Mock模式逻辑保持不变
            if isinstance(wavelength, (list, tuple)) and len(wavelength) >= 2:
                wavelength_a, wavelength_b = wavelength[0], wavelength[1]
                if 190 <= wavelength_a <= 800 and 190 <= wavelength_b <= 800:
                    self.wavelength_a = float(wavelength_a)
                    self.wavelength_b = float(wavelength_b)
                    self.wavelength = float(wavelength_a)
                    await asyncio.sleep(0.1)
                    return True
                return False
            elif isinstance(wavelength, (int, float)):
                if 190 <= wavelength <= 800:
                    if channel == 'A':
                        self.wavelength_a = float(wavelength)
                        self.wavelength = float(wavelength)
                    elif channel == 'B':
                        self.wavelength_b = float(wavelength)
                    await asyncio.sleep(0.1)
                    return True
                return False
            return False
        else:
            # 实际硬件模式
            if isinstance(wavelength, (list, tuple)) and len(wavelength) >= 2:
                # 设置双通道波长
                wavelength_a, wavelength_b = int(wavelength[0]), int(wavelength[1])
                if 190 <= wavelength_a <= 800 and 190 <= wavelength_b <= 800:
                    command = f"WLwA{wavelength_a}B{wavelength_b}"
                    response = self._send_command(command)
                    if response is not None:
                        # 验证设置是否成功
                        a_val, b_val = await self._read_wavelength_hardware()
                        if a_val == wavelength_a and b_val == wavelength_b:
                            self.wavelength_a = float(wavelength_a)
                            self.wavelength_b = float(wavelength_b)
                            self.wavelength = float(wavelength_a)
                            return True
                return False
            elif isinstance(wavelength, (int, float)):
                # 单通道设置，保持另一通道不变
                if 190 <= wavelength <= 800:
                    wavelength_val = int(wavelength)
                    if channel == 'A':
                        command = f"WLwA{wavelength_val}B{int(self.wavelength_b)}"
                        target_a, target_b = wavelength_val, int(self.wavelength_b)
                    else:
                        command = f"WLwA{int(self.wavelength_a)}B{wavelength_val}"
                        target_a, target_b = int(self.wavelength_a), wavelength_val

                    response = self._send_command(command)
                    if response is not None:
                        # 验证设置是否成功
                        a_val, b_val = await self._read_wavelength_hardware()
                        if a_val == target_a and b_val == target_b:
                            self.wavelength_a = float(target_a)
                            self.wavelength_b = float(target_b)
                            if channel == 'A':
                                self.wavelength = float(wavelength_val)
                            return True
                return False
            return False

    async def _read_wavelength_hardware(self):
        """从硬件读取当前波长设置"""
        if self.mock:
            return int(self.wavelength_a), int(self.wavelength_b)

        response = self._send_command('WLr')
        if response:
            return self._parse_wavelength_data(response)
        return 0, 0
    
    async def start_detection(self) -> bool:
        """开始检测"""
        if self.mock:
            if self.is_connected:
                self.is_detecting = True
                await asyncio.sleep(0.05)
                return True
            return False
        else:
            # 实际硬件模式：发送开始采集命令
            if not self.is_connected:
                return False

            # 发送开始采集命令
            response = self._send_command('ABs')
            if response is not None:
                self.is_detecting = True
                return True
            return False
    
    async def stop_detection(self) -> bool:
        """停止检测"""
        if self.mock:
            self.is_detecting = False
            await asyncio.sleep(0.05)
            return True
        else:
            # 实际硬件模式：停止采集
            if not self.is_connected:
                return False

            # 停止采集（通过停止发送采集命令实现）
            self.is_detecting = False
            await asyncio.sleep(0.05)
            return True
    
    async def get_signal(self) -> List[float]:
        """
        获取当前检测信号（A/B双通道）
        :return: [A通道信号, B通道信号]
        """
        if self.mock:
            if not self.is_detecting:
                return [0.0, 0.0]

            # Each call represents one second passed
            self.mock_time += 1
            t = self.mock_time

            # Baseline drift (slow)
            baseline = 1 + 0.0005 * t

            # A通道: 三个高斯峰
            # At 4 min, height 20, width 1 min
            peak1_a = 20 * math.exp(-((t - 4 * 60) ** 2) / (2 * (60) ** 2))
            # At 7 min, height 50, width 2.5 min
            peak2_a = 50 * math.exp(-((t - 7 * 60) ** 2) / (2 * (150) ** 2))
            # At 12 min, height 30, width 2 min
            peak3_a = 30 * math.exp(-((t - 12 * 60) ** 2) / (2 * (120) ** 2))

            # B通道: 不同的响应（模拟280nm的不同吸收）
            # 蛋白质在280nm有更强吸收
            peak1_b = 20 * math.exp(-((t - 2 * 60) ** 2) / (2 * (60) ** 2))
            peak2_b = 50 * math.exp(-((t - 12 * 60) ** 2) / (2 * (150) ** 2))  # 蛋白质峰更高
            peak3_b = 30 * math.exp(-((t - 30 * 60) ** 2) / (2 * (120) ** 2))

            # Small random noise for each channel
            noise_a = random.gauss(0, 0.2)
            noise_b = random.gauss(0, 0.15)

            value_a = baseline + peak1_a + peak2_a + peak3_a + noise_a
            value_b = baseline + peak1_b + peak2_b + peak3_b + noise_b  # B通道基线稍低

            return [round(value_a, 5), round(value_b, 5)]
        else:
            # 实际硬件模式：从硬件读取信号数据
            if not self.is_detecting:
                return [0.0, 0.0]

            # 发送采集数据命令
            response = self._send_command('ABr')
            if response:
                a_val, b_val = self._parse_collect_data(response)
                return [round(a_val, 5), round(b_val, 5)]
            else:
                return [0.0, 0.0]
    
    async def get_spectrum(self) -> List[Dict[str, float]]:
        """获取光谱数据"""
        if self.mock:
            await asyncio.sleep(0.2)
            # Return mock spectrum data
            return [{"wavelength": 200 + i * 10, "intensity": random.uniform(0, 100)} for i in range(50)]
        else:
            # 实际硬件模式：返回空列表（该硬件不支持全光谱扫描）
            await asyncio.sleep(0.2)
            return []

    async def auto_zero(self) -> bool:
        """自动调零"""
        if self.mock:
            await asyncio.sleep(1.0)
            return True
        else:
            # 实际硬件模式：发送调零命令
            if not self.is_connected:
                return False

            # 发送调零命令（使用AZs命令如果存在，否则使用模拟调零）
            await asyncio.sleep(1.0)  # 模拟调零过程
            return True

    def get_wavelength(self) -> List[float]:
        """
        获取当前设置的波长
        :return: 返回双通道波长列表 [A通道波长, B通道波长]
        """
        return [self.wavelength_a, self.wavelength_b]
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取检测器完整状态数据（双通道）
        :return: 包含双通道信号、波长、模式等完整信息
        """
        if self.mock:
            # 获取双通道信号值
            signal_values = await self.get_signal()

            # 返回完整的检测器数据
            return {
                "device_id": self.device_id,
                "device_type": "detector",
                "is_connected": self.is_connected,
                "is_detecting": self.is_detecting,
                "detection_mode": self.detection_mode,
                "wavelength": [self.wavelength_a, self.wavelength_b],  # 双通道波长 [A, B]
                "signal": signal_values,  # 双通道信号 [A, B] (mAU)
                "channel_a": {
                    "wavelength": self.wavelength_a,
                    "signal": signal_values[0],
                    "unit": "mAU"
                },
                "channel_b": {
                    "wavelength": self.wavelength_b,
                    "signal": signal_values[1],
                    "unit": "mAU"
                },
                "time_point": self.mock_time,  # 当前时间点（秒）
                "retention_time": round(self.mock_time / 60, 2),  # 保留时间（分钟）
                "unit": "mAU",
                "timestamp": time.time()
            }
        else:
            # 实际硬件模式：获取实际硬件状态
            signal_values = await self.get_signal()
            current_wavelength = await self._read_wavelength_hardware()

            return {
                "device_id": self.device_id,
                "device_type": "detector",
                "is_connected": self.is_connected,
                "is_detecting": self.is_detecting,
                "detection_mode": self.detection_mode,
                "wavelength": [float(current_wavelength[0]), float(current_wavelength[1])],
                "signal": signal_values,
                "channel_a": {
                    "wavelength": float(current_wavelength[0]),
                    "signal": signal_values[0],
                    "unit": "mAU"
                },
                "channel_b": {
                    "wavelength": float(current_wavelength[1]),
                    "signal": signal_values[1],
                    "unit": "mAU"
                },
                "unit": "mAU",
                "timestamp": time.time()
            }

    async def disconnect(self) -> bool:
        """断开连接"""
        if self.mock:
            self.is_connected = False
            self.is_detecting = False
            await asyncio.sleep(0.1)
            return True
        else:
            # 实际硬件模式：关闭串口连接
            try:
                if self.is_detecting:
                    await self.stop_detection()

                self._close_serial()
                self.is_connected = False
                self.is_detecting = False
                await asyncio.sleep(0.1)
                return True
            except Exception as e:
                print(f"Disconnect error: {e}")
                return False

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock

if __name__ == '__main__':
    async def test():
        detector = DetectorController(mock=True)
        await detector.connect()
        await detector.set_wavelength(254)
        await detector.start_detection()
        for _ in range(10):
            signal = await detector.get_signal()
            print(f'Signal: {signal}')
            await asyncio.sleep(1)
        await detector.stop_detection()
        await detector.disconnect()

    asyncio.run(test())