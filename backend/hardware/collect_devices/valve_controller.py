"""
阀门控制器
控制电1-电6、泵3、双3等8个设备
"""

from typing import Dict, Any, List, Optional
import asyncio
import requests
from ..hardware_config import MockDataGenerator, is_mock_mode


class ValveController:
    """阀门控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'valve_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.valves = {
            '电1': {'name': '进样阀', 'status': 'closed', 'type': '电磁阀', 'pin_num': 13},
            '电2': {'name': '冲洗阀', 'status': 'closed', 'type': '电磁阀', 'pin_num': 10},
            '电3': {'name': '废液阀', 'status': 'closed', 'type': '电磁阀', 'pin_num': 11},
            '电4': {'name': '备用阀', 'status': 'closed', 'type': '电磁阀', 'pin_num': 12},
            '电5': {'name': '备用阀', 'status': 'closed', 'type': '二通阀', 'pin_num': 9},
            '电6': {'name': '备用阀', 'status': 'closed', 'type': '二通阀', 'pin_num': 8},
            '泵3': {'name': '辅助泵', 'status': 'stopped', 'type': '电磁阀', 'pin_num': 14},
            '双3': {'name': '双向阀', 'status': 'position_1', 'type': '电磁阀', 'pin_num': 15}
        }

    def _single_valve_control(self, pin_num: int, value: int) -> bool:
        """调用硬件单向阀控制接口"""
        try:
            url = f"{self.base_url}/device/on"
            params = {'pin_num': pin_num, 'value': value}
            response = requests.get(url, params=params, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def control_valve(self, valve_id: str, action: str) -> bool:
        """
        控制阀门
        :param valve_id: 阀门ID
        :param action: 操作(open/close/position_1/position_2/start/stop)
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
            if valve_id not in self.valves:
                return False

            valve_info = self.valves[valve_id]
            pin_num = valve_info['pin_num']

            # 根据动作确定value值
            value = 0  # 默认值
            if action == 'open':
                value = 1
                self.valves[valve_id]['status'] = 'opened'
            elif action == 'close':
                value = 0
                self.valves[valve_id]['status'] = 'closed'
            elif action == 'start' and valve_id == '泵3':
                value = 1
                self.valves[valve_id]['status'] = 'running'
            elif action == 'stop' and valve_id == '泵3':
                value = 0
                self.valves[valve_id]['status'] = 'stopped'
            elif action == 'position_1':
                value = 0
                self.valves[valve_id]['status'] = 'position_1'
            elif action == 'position_2':
                value = 1
                self.valves[valve_id]['status'] = 'position_2'
            else:
                return False

            # 调用硬件接口
            success = self._single_valve_control(pin_num, value)

            # 如果硬件操作失败，恢复状态
            if not success:
                # 这里可以添加状态回滚逻辑
                pass

            await asyncio.sleep(0.1)
            return success
    
    async def batch_control(self, valve_actions: List[Dict[str, str]]) -> bool:
        """
        批量控制阀门
        :param valve_actions: [{'valve_id': 'valve_id', 'action': 'action'}, ...]
        :return: 操作结果
        """
        if not valve_actions:
            return True

        success_count = 0
        for valve_action in valve_actions:
            valve_id = valve_action.get('valve_id')
            action = valve_action.get('action')

            if valve_id and action:
                success = await self.control_valve(valve_id, action)
                if success:
                    success_count += 1

        # 如果所有操作都成功，返回True
        return success_count == len(valve_actions)
    
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
            # 在真实硬件模式下，返回当前存储的状态
            # 注意：硬件可能没有状态查询接口，所以依赖内部状态跟踪
            if valve_id:
                if valve_id in self.valves:
                    return {
                        'device_id': self.device_id,
                        'mode': 'hardware',
                        valve_id: self.valves[valve_id].copy()
                    }
                return {}
            else:
                return {
                    'device_id': self.device_id,
                    'mode': 'hardware',
                    'valves': self.valves.copy()
                }
    
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
            success_count = 0
            total_valves = len(self.valves)

            for valve_id in self.valves:
                try:
                    if valve_id == '泵3':
                        success = await self.control_valve(valve_id, 'stop')
                    elif valve_id == '双3':
                        success = await self.control_valve(valve_id, 'position_1')
                    else:
                        success = await self.control_valve(valve_id, 'close')

                    if success:
                        success_count += 1
                except Exception:
                    continue

            await asyncio.sleep(0.2)
            return success_count == total_valves

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock
    
    async def test_valve(self, valve_id: str) -> bool:
        """测试阀门功能"""
        if valve_id not in self.valves:
            return False

        try:
            # 获取当前状态
            current_status = await self.get_status(valve_id)
            original_status = current_status.get(valve_id, {}).get('status', 'closed')

            # 执行测试序列
            if valve_id == '泵3':
                # 测试泵：启动->停止
                await self.control_valve(valve_id, 'start')
                await asyncio.sleep(1)
                await self.control_valve(valve_id, 'stop')
            elif valve_id == '双3':
                # 测试双向阀：position_1->position_2->position_1
                await self.control_valve(valve_id, 'position_1')
                await asyncio.sleep(1)
                await self.control_valve(valve_id, 'position_2')
                await asyncio.sleep(1)
                await self.control_valve(valve_id, 'position_1')
            else:
                # 测试普通阀门：关闭->打开->关闭
                await self.control_valve(valve_id, 'close')
                await asyncio.sleep(1)
                await self.control_valve(valve_id, 'open')
                await asyncio.sleep(1)
                await self.control_valve(valve_id, 'close')

            return True

        except Exception:
            return False