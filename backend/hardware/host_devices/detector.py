"""
检测器控制器
ttyAMA3接口，波特率57600
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
import math
import random
# from ..hardware_config import is_mock_mode


class DetectorController:
    """检测器控制器类"""

    def __init__(self, port: str = 'ttyAMA3', baudrate: int = 57600, mock: Optional[bool] = True):
        self.device_id = f'detector_{port}'
        self.port = port
        self.baudrate = baudrate
        self.mock = mock
        self.connection = None
        self.detection_mode = 'UV'  # UV/荧光/电化学等
        self.is_connected = False
        self.is_detecting = False
        # 双通道波长配置
        self.wavelength_a = 254.0  # A通道波长
        self.wavelength_b = 280.0  # B通道波长
        self.wavelength = 254.0  # 保留兼容性
        self.mock_time = 0  # 用于模拟时间进程
    
    async def connect(self) -> bool:
        """连接检测器"""
        if self.mock:
            await asyncio.sleep(0.2)
            self.is_connected = True
            return True
        else:
            pass
    
    async def set_wavelength(self, wavelength: float, channel: str = 'A') -> bool:
        """
        设置检测波长
        :param wavelength: 波长(nm)
        :param channel: 通道 'A' 或 'B'
        :return: 设置结果
        """
        if self.mock:
            if 190 <= wavelength <= 800:
                if channel == 'A':
                    self.wavelength_a = wavelength
                    self.wavelength = wavelength  # 兼容旧代码
                elif channel == 'B':
                    self.wavelength_b = wavelength
                await asyncio.sleep(0.1)
                return True
            return False
        else:
            pass
    
    async def start_detection(self) -> bool:
        """开始检测"""
        if self.mock:
            if self.is_connected:
                self.is_detecting = True
                await asyncio.sleep(0.05)
                return True
            return False
        else:
            pass
    
    async def stop_detection(self) -> bool:
        """停止检测"""
        if self.mock:
            self.is_detecting = False
            await asyncio.sleep(0.05)
            return True
        else:
            pass
    
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
            pass
    
    async def get_spectrum(self) -> List[Dict[str, float]]:
        """获取光谱数据"""
        if self.mock:
            await asyncio.sleep(0.2)
            # Return mock spectrum data
            return [{"wavelength": 200 + i * 10, "intensity": random.uniform(0, 100)} for i in range(50)]
        else:
            pass

    async def auto_zero(self) -> bool:
        """自动调零"""
        if self.mock:
            await asyncio.sleep(1.0)
            return True
        else:
            pass
    
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
            return {}

    async def disconnect(self) -> bool:
        """断开连接"""
        if self.mock:
            self.is_connected = False
            self.is_detecting = False
            await asyncio.sleep(0.1)
            return True
        else:
            pass

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