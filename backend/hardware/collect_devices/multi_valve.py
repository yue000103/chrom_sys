"""
多向阀控制器
多1-多11 (11个多向阀)
"""

from typing import Dict, Any, List, Optional
import asyncio
import requests
from ..hardware_config import MockDataGenerator, is_mock_mode


class MultiValveController:
    """多向阀控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'multi_valve_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)

        # 阀站配置映射：多向阀ID -> 阀站号
        self.valve_station_mapping = {
            '多1': 9,
            '多2': 4,
            '多3': 2,
            '多4': 1,
            '多5': 2,
            '多6': 11,  # 0B
            '多7': 10,  # 0A
            '多8': 7,
            '多9': 8,
            '多10': 5,
            '多11': 6
        }

        self.valves = {}
        # 初始化11个多向阀
        for i in range(1, 12):
            self.valves[f'多{i}'] = {
                'positions': 6,  # 六位阀
                'current_position': 1,
                'status': 'idle',
                'station_num': self.valve_station_mapping[f'多{i}']
            }

    def _switch_valve_hardware(self, station_num: int, valve_position: str) -> bool:
        """
        调用硬件接口切换阀门位置
        :param station_num: 阀站号
        :param valve_position: 阀门位置 (A, B, C, D, E, F)
        :return: 切换结果
        """
        try:
            url = f"{self.base_url}/valve/switch"
            params = {'num': station_num, 'valve_num': valve_position}
            response = requests.get(url, params=params, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"硬件调用失败: {e}")
            return False

    def _position_to_valve_num(self, position: int) -> str:
        """
        将数字位置转换为阀门位置标识符
        :param position: 位置 (1-6)
        :return: 阀门位置 (A-F)
        """
        position_map = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F'}
        return position_map.get(position, 'A')

    async def set_position(self, valve_id: str, position: int) -> bool:
        """
        设置阀门位置
        :param valve_id: 阀门ID(多1-多11)
        :param position: 目标位置(1-6)
        :return: 设置结果
        """
        if valve_id not in self.valves:
            return False

        if not (1 <= position <= self.valves[valve_id]['positions']):
            return False

        if self.mock:
            # Mock模式：直接模拟设置
            self.valves[valve_id]['current_position'] = position
            self.valves[valve_id]['status'] = 'moving'
            await asyncio.sleep(0.2)
            self.valves[valve_id]['status'] = 'idle'
            return True
        else:
            # 实际硬件模式：调用硬件接口
            station_num = self.valve_station_mapping[valve_id]
            valve_position = self._position_to_valve_num(position)

            self.valves[valve_id]['status'] = 'moving'
            success = self._switch_valve_hardware(station_num, valve_position)

            if success:
                self.valves[valve_id]['current_position'] = position
                self.valves[valve_id]['status'] = 'idle'
            else:
                self.valves[valve_id]['status'] = 'error'

            return success
    
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
        if valve_id in self.valves:
            return self.valves[valve_id]['current_position']
        return 0
    
    async def batch_set_positions(self, positions: Dict[str, int]) -> bool:
        """
        批量设置位置
        :param positions: {valve_id: position, ...}
        :return: 设置结果
        """
        results = []
        for valve_id, position in positions.items():
            result = await self.set_position(valve_id, position)
            results.append(result)
        return all(results)
    
    async def reset_all_valves(self) -> bool:
        """重置所有阀门到初始位置"""
        if self.mock:
            for valve_id in self.valves:
                self.valves[valve_id]['current_position'] = 1
                self.valves[valve_id]['status'] = 'idle'
            await asyncio.sleep(0.5)
            return True
        else:
            # 实际硬件模式：将所有阀门重置到位置1(A)
            results = []
            for valve_id in self.valves:
                result = await self.set_position(valve_id, 1)
                results.append(result)
            return all(results)
    
    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有阀门状态"""
        return {
            'device_id': self.device_id,
            'mode': 'mock' if self.mock else 'hardware',
            'base_url': self.base_url,
            'valve_station_mapping': self.valve_station_mapping,
            'valves': self.valves.copy()
        }

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock
    
    async def configure_valve(self, valve_id: str, config: Dict[str, Any]) -> bool:
        """配置阀门参数"""
        if valve_id not in self.valves:
            return False

        # 更新阀门配置
        for key, value in config.items():
            if key in ['positions', 'current_position', 'status']:
                self.valves[valve_id][key] = value

        return True

    def get_valve_station_number(self, valve_id: str) -> int:
        """获取阀门对应的阀站号"""
        return self.valve_station_mapping.get(valve_id, 0)

    def get_all_valve_ids(self) -> List[str]:
        """获取所有阀门ID列表"""
        return list(self.valves.keys())

    async def test_connection(self) -> bool:
        """测试与硬件的连接"""
        if self.mock:
            return True
        else:
            # 测试连接：尝试获取一个简单的阀门状态
            try:
                url = f"{self.base_url}/valve/switch"
                params = {'num': 1, 'valve_num': 'A'}  # 测试请求
                response = requests.get(url, params=params, timeout=3)
                return response.status_code == 200
            except Exception:
                return False