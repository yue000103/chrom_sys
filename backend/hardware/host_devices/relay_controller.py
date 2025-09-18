"""
继电器控制器
控制双2(低压电磁阀)、双1(高压电磁阀)、泵2(气泵)
"""

from typing import Dict, Any, Optional
import asyncio
from ..hardware_config import MockDataGenerator, is_mock_mode


class RelayController:
    """继电器控制器类"""

    def __init__(self, mock: Optional[bool] = None):
        self.device_id = 'relay_controller'
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.connection = None
        self.relays = {
            '双2': {'name': '低压电磁阀', 'status': False},
            '双1': {'name': '高压电磁阀', 'status': False},
            '泵2': {'name': '气泵', 'status': False}
        }

    async def initialize(self) -> bool:
        """初始化继电器"""
        if self.mock:
            # Mock模式下直接返回成功
            await asyncio.sleep(0.1)  # 模拟初始化延时
            return True
        else:
            # 实际硬件初始化
            pass

    async def control_relay(self, relay_id: str, action: str) -> bool:
        """
        控制继电器
        :param relay_id: 继电器ID(双2/双1/泵2)
        :param action: 操作(on/off)
        :return: 操作结果
        """
        if self.mock:
            # Mock模式下模拟控制
            if relay_id in self.relays:
                self.relays[relay_id]['status'] = (action == 'on')
                await asyncio.sleep(0.05)  # 模拟控制延时
                return MockDataGenerator.generate_success_status()
            return False
        else:
            # 实际硬件控制
            pass

    async def get_status(self) -> Dict[str, Any]:
        """获取所有继电器状态"""
        if self.mock:
            # Mock模式下返回当前状态
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'relays': self.relays.copy(),
                'status': MockDataGenerator.generate_device_status()
            }
        else:
            # 实际硬件状态读取
            pass

    async def emergency_stop(self) -> bool:
        """紧急停止所有继电器"""
        if self.mock:
            # Mock模式下关闭所有继电器
            for relay_id in self.relays:
                self.relays[relay_id]['status'] = False
            await asyncio.sleep(0.1)  # 模拟操作延时
            return True
        else:
            # 实际硬件紧急停止
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock