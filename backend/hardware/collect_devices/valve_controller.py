"""
阀门控制器
控制电1-电6、泵3、双3等8个设备
"""

from typing import Dict, Any, List, Optional
import asyncio
from ..hardware_config import MockDataGenerator, is_mock_mode


class ValveController:
    """阀门控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'valve_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.valves = {
            '电1': {'name': '进样阀', 'status': 'closed'},
            '电2': {'name': '冲洗阀', 'status': 'closed'},
            '电3': {'name': '废液阀', 'status': 'closed'},
            '电4': {'name': '备用阀', 'status': 'closed'},
            '电5': {'name': '备用阀', 'status': 'closed'},
            '电6': {'name': '备用阀', 'status': 'closed'},
            '泵3': {'name': '辅助泵', 'status': 'stopped'},
            '双3': {'name': '双向阀', 'status': 'position_1'}
        }
    
    async def control_valve(self, valve_id: str, action: str) -> bool:
        """
        控制阀门
        :param valve_id: 阀门ID
        :param action: 操作(open/close/position_1/position_2)
        :return: 操作结果
        """
        if self.mock:
            if valve_id in self.valves:
                if action in ['open', 'close']:
                    self.valves[valve_id]['status'] = 'opened' if action == 'open' else 'closed'
                elif action in ['position_1', 'position_2']:
                    self.valves[valve_id]['status'] = action
                elif action in ['start', 'stop'] and valve_id == '泵3':
                    self.valves[valve_id]['status'] = 'running' if action == 'start' else 'stopped'
                await asyncio.sleep(0.1)
                return MockDataGenerator.generate_success_status()
            return False
        else:
            pass
    
    async def batch_control(self, valve_actions: List[Dict[str, str]]) -> bool:
        """
        批量控制阀门
        :param valve_actions: [{valve_id: action}, ...]
        :return: 操作结果
        """
        pass
    
    async def get_status(self, valve_id: str = None) -> Dict[str, Any]:
        """获取阀门状态"""
        if self.mock:
            if valve_id:
                if valve_id in self.valves:
                    return {
                        'device_id': self.device_id,
                        'mode': 'mock',
                        valve_id: self.valves[valve_id].copy()
                    }
                return {}
            else:
                return {
                    'device_id': self.device_id,
                    'mode': 'mock',
                    'valves': self.valves.copy()
                }
        else:
            pass
    
    async def emergency_close_all(self) -> bool:
        """紧急关闭所有阀门"""
        if self.mock:
            for valve_id in self.valves:
                if valve_id == '泵3':
                    self.valves[valve_id]['status'] = 'stopped'
                elif valve_id == '双3':
                    self.valves[valve_id]['status'] = 'position_1'
                else:
                    self.valves[valve_id]['status'] = 'closed'
            await asyncio.sleep(0.2)
            return True
        else:
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock
    
    async def test_valve(self, valve_id: str) -> bool:
        """测试阀门功能"""
        pass