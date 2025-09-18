"""
多向阀控制器
多1-多11 (11个多向阀)
"""

from typing import Dict, Any, List, Optional
import asyncio
from ..hardware_config import MockDataGenerator, is_mock_mode


class MultiValveController:
    """多向阀控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'multi_valve_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.valves = {}
        # 初始化11个多向阀
        for i in range(1, 12):
            self.valves[f'多{i}'] = {
                'positions': 6,  # 六位阀
                'current_position': 1,
                'status': 'idle'
            }
    
    async def set_position(self, valve_id: str, position: int) -> bool:
        """
        设置阀门位置
        :param valve_id: 阀门ID(多1-多11)
        :param position: 目标位置(1-6)
        :return: 设置结果
        """
        if self.mock:
            if valve_id in self.valves and 1 <= position <= self.valves[valve_id]['positions']:
                self.valves[valve_id]['current_position'] = position
                self.valves[valve_id]['status'] = 'moving'
                await asyncio.sleep(0.2)
                self.valves[valve_id]['status'] = 'idle'
                return True
            return False
        else:
            pass
    
    async def rotate_valve(self, valve_id: str, direction: str = 'clockwise') -> bool:
        """
        旋转阀门
        :param valve_id: 阀门ID
        :param direction: 旋转方向(clockwise/counterclockwise)
        :return: 旋转结果
        """
        pass
    
    async def get_position(self, valve_id: str) -> int:
        """获取当前位置"""
        if self.mock:
            if valve_id in self.valves:
                return self.valves[valve_id]['current_position']
            return 0
        else:
            pass
    
    async def batch_set_positions(self, positions: Dict[str, int]) -> bool:
        """
        批量设置位置
        :param positions: {valve_id: position, ...}
        :return: 设置结果
        """
        pass
    
    async def reset_all_valves(self) -> bool:
        """重置所有阀门到初始位置"""
        if self.mock:
            for valve_id in self.valves:
                self.valves[valve_id]['current_position'] = 1
                self.valves[valve_id]['status'] = 'idle'
            await asyncio.sleep(0.5)
            return True
        else:
            pass
    
    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有阀门状态"""
        if self.mock:
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'valves': self.valves.copy()
            }
        else:
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock
    
    async def configure_valve(self, valve_id: str, config: Dict[str, Any]) -> bool:
        """配置阀门参数"""
        pass