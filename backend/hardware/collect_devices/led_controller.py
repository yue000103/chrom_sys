"""
LED灯控制器
192.168.1.129/led/on
"""

from typing import Dict, Any, Optional
import asyncio
from ..hardware_config import MockDataGenerator, is_mock_mode


class LEDController:
    """LED灯控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'led_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.led_status = False
        self.brightness = 100  # 0-100
    
    async def turn_on(self) -> bool:
        """打开LED灯"""
        if self.mock:
            self.led_status = True
            await asyncio.sleep(0.05)
            return True
        else:
            pass
    
    async def turn_off(self) -> bool:
        """关闭LED灯"""
        if self.mock:
            self.led_status = False
            await asyncio.sleep(0.05)
            return True
        else:
            pass
    
    async def set_brightness(self, brightness: int) -> bool:
        """
        设置亮度
        :param brightness: 亮度值(0-100)
        :return: 设置结果
        """
        if self.mock:
            if 0 <= brightness <= 100:
                self.brightness = brightness
                await asyncio.sleep(0.05)
                return True
            return False
        else:
            pass
    
    async def blink(self, times: int = 3, interval: float = 0.5) -> bool:
        """
        LED闪烁
        :param times: 闪烁次数
        :param interval: 闪烁间隔(秒)
        :return: 执行结果
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """获取LED状态"""
        if self.mock:
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'status': 'on' if self.led_status else 'off',
                'brightness': self.brightness,
                'base_url': self.base_url
            }
        else:
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock