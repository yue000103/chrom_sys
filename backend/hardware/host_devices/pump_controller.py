"""
四合一高压恒流泵控制器
ttyAMA2接口，波特率115200
"""

from typing import Dict, Any, Optional
import asyncio
import time
from ..hardware_config import MockDataGenerator, is_mock_mode


class PumpController:
    """高压恒流泵控制器类"""
    
    def __init__(self, port: str = 'ttyAMA2', baudrate: int = 115200, mock: Optional[bool] = None):
        self.device_id = f'pump_controller_{port}'
        self.port = port
        self.baudrate = baudrate
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.connection = None
        self.is_connected = False
        self.pumps = {
            'A': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'B': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'C': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'D': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'}
        }
    
    async def connect(self) -> bool:
        """连接泵控制器"""
        if self.mock:
            await asyncio.sleep(0.2)
            self.is_connected = True
            return True
        else:
            pass
    
    async def set_flow_rate(self, pump_id: str, flow_rate: float) -> bool:
        """
        设置流速
        :param pump_id: 泵ID(A/B/C/D)
        :param flow_rate: 流速(mL/min)
        :return: 设置结果
        """
        if self.mock:
            if pump_id in self.pumps and 0 <= flow_rate <= 10:
                self.pumps[pump_id]['flow_rate'] = flow_rate
                await asyncio.sleep(0.1)
                return True
            return False
        else:
            pass
    
    async def set_gradient(self, gradient_profile: Dict[str, Any]) -> bool:
        """
        设置梯度洗脱
        :param gradient_profile: 梯度参数
        :return: 设置结果
        """
        pass
    
    async def start_pump(self, pump_id: str) -> bool:
        """启动泵"""
        if self.mock:
            if pump_id in self.pumps:
                self.pumps[pump_id]['status'] = 'running'
                self.pumps[pump_id]['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                await asyncio.sleep(0.2)
                return True
            return False
        else:
            pass
    
    async def stop_pump(self, pump_id: str) -> bool:
        """停止泵"""
        if self.mock:
            if pump_id in self.pumps:
                self.pumps[pump_id]['status'] = 'stopped'
                self.pumps[pump_id]['pressure'] = 0.0
                await asyncio.sleep(0.1)
                return True
            return False
        else:
            pass
    
    async def get_status(self, pump_id: Optional[str] = None) -> Dict[str, Any]:
        """获取泵状态"""
        if self.mock:
            if pump_id:
                if pump_id in self.pumps:
                    pump = self.pumps[pump_id].copy()
                    if pump['status'] == 'running':
                        pump['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                    return {'device_id': self.device_id, 'mode': 'mock', pump_id: pump}
                return {}
            else:
                pumps_status = {}
                for pid, pump in self.pumps.items():
                    pump_copy = pump.copy()
                    if pump_copy['status'] == 'running':
                        pump_copy['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                    pumps_status[pid] = pump_copy
                return {'device_id': self.device_id, 'mode': 'mock', 'pumps': pumps_status}
        else:
            pass
    
    async def purge_system(self) -> bool:
        """系统清洗"""
        pass
    
    async def prime_pump(self, pump_id: str) -> bool:
        """泵预填充"""
        pass
    
    async def disconnect(self) -> bool:
        """断开连接"""
        if self.mock:
            for pump_id in self.pumps:
                self.pumps[pump_id]['status'] = 'stopped'
                self.pumps[pump_id]['pressure'] = 0.0
            self.is_connected = False
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