"""
隔膜泵控制器
泵4控制
"""

from typing import Dict, Any, Optional
import asyncio
import requests
from ..hardware_config import MockDataGenerator, is_mock_mode


class SprayPumpController:
    """隔膜泵(喷雾泵)控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'spray_pump_controller'
        self.device_name = '泵4'  # 设备名称
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)

        # 硬件控制参数
        self.freq = 1000  # 频率
        self.duty = 1000  # 速度

        self.pump_status = {
            'status': 'stopped',
            'flow_rate': 0.0,
            'pressure': 0.0,
            'runtime': 0,
            'total_volume': 0.0,
            'freq': self.freq,
            'duty': self.duty
        }
    
    async def start_pump(self, flow_rate: Optional[float] = None) -> bool:
        """
        启动隔膜泵
        :param flow_rate: 流速(mL/min)
        :return: 启动结果
        """
        if self.mock:
            self.pump_status['status'] = 'running'
            self.pump_status['flow_rate'] = flow_rate if flow_rate else MockDataGenerator.generate_flow_rate(0.5, 3.0)
            self.pump_status['pressure'] = MockDataGenerator.generate_pressure(0.5, 5.0)
            await asyncio.sleep(0.2)
            return True
        else:
            try:
                url = f"{self.base_url}/pump/switch"
                params = {
                    'ifon': 1,  # 1代表开启
                    'freq': self.freq,
                    'duty': self.duty
                }

                # 使用asyncio.to_thread将同步请求转为异步
                response = await asyncio.to_thread(requests.get, url, params=params)

                if response.status_code == 200:
                    self.pump_status['status'] = 'running'
                    if flow_rate:
                        self.pump_status['flow_rate'] = flow_rate
                    return True
                return False
            except Exception as e:
                print(f"启动{self.device_name}失败: {e}")
                return False
    
    async def stop_pump(self) -> bool:
        """停止隔膜泵"""
        if self.mock:
            self.pump_status['status'] = 'stopped'
            self.pump_status['flow_rate'] = 0.0
            self.pump_status['pressure'] = 0.0
            await asyncio.sleep(0.1)
            return True
        else:
            try:
                url = f"{self.base_url}/pump/switch"
                params = {
                    'ifon': 0,  # 0代表关闭
                    'freq': self.freq,
                    'duty': self.duty
                }

                # 使用asyncio.to_thread将同步请求转为异步
                response = await asyncio.to_thread(requests.get, url, params=params)

                if response.status_code == 200:
                    self.pump_status['status'] = 'stopped'
                    self.pump_status['flow_rate'] = 0.0
                    self.pump_status['pressure'] = 0.0
                    return True
                return False
            except Exception as e:
                print(f"停止{self.device_name}失败: {e}")
                return False
    
    async def set_flow_rate(self, flow_rate: float) -> bool:
        """
        设置流速
        :param flow_rate: 流速(mL/min)
        :return: 设置结果
        """
        if self.mock:
            if 0 <= flow_rate <= 10:
                if self.pump_status['status'] == 'running':
                    self.pump_status['flow_rate'] = flow_rate
                await asyncio.sleep(0.1)
                return True
            return False
        else:
            pass
    
    async def pulse_mode(self, pulse_params: Dict[str, Any]) -> bool:
        """
        脉冲模式
        :param pulse_params: 脉冲参数
        :return: 设置结果
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """获取泵状态"""
        if self.mock:
            status = self.pump_status.copy()
            if status['status'] == 'running':
                status['runtime'] += 1
                status['total_volume'] += status['flow_rate'] / 60
                status['pressure'] = MockDataGenerator.generate_pressure(0.5, 5.0)
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'pump': status
            }
        else:
            pass
    
    async def prime_pump(self) -> bool:
        """泵预填充"""
        pass
    
    async def calibrate_pump(self, calibration_params: Dict[str, Any]) -> bool:
        """泵校准"""
        pass
    
    async def emergency_stop(self) -> bool:
        """紧急停止"""
        if self.mock:
            return await self.stop_pump()
        else:
            pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock

    def set_pump_parameters(self, freq: int = None, duty: int = None):
        """
        设置泵参数
        :param freq: 频率
        :param duty: 速度
        """
        if freq is not None:
            self.freq = freq
            self.pump_status['freq'] = freq
        if duty is not None:
            self.duty = duty
            self.pump_status['duty'] = duty

    async def pump_control(self, ifon: int, freq: int = None, duty: int = None) -> bool:
        """
        直接控制泵开关（底层方法）
        :param ifon: 开关（0关闭，1开启）
        :param freq: 频率
        :param duty: 速度
        :return: 控制结果
        """
        # 更新参数
        if freq is not None:
            self.freq = freq
        if duty is not None:
            self.duty = duty

        if self.mock:
            if ifon == 1:
                self.pump_status['status'] = 'running'
                self.pump_status['flow_rate'] = MockDataGenerator.generate_flow_rate(0.5, 3.0)
                self.pump_status['pressure'] = MockDataGenerator.generate_pressure(0.5, 5.0)
            else:
                self.pump_status['status'] = 'stopped'
                self.pump_status['flow_rate'] = 0.0
                self.pump_status['pressure'] = 0.0

            self.pump_status['freq'] = self.freq
            self.pump_status['duty'] = self.duty
            await asyncio.sleep(0.1)
            return True
        else:
            try:
                url = f"{self.base_url}/pump/switch"
                params = {
                    'ifon': ifon,
                    'freq': self.freq,
                    'duty': self.duty
                }

                response = await asyncio.to_thread(requests.get, url, params=params)

                if response.status_code == 200:
                    if ifon == 1:
                        self.pump_status['status'] = 'running'
                    else:
                        self.pump_status['status'] = 'stopped'
                        self.pump_status['flow_rate'] = 0.0
                        self.pump_status['pressure'] = 0.0

                    self.pump_status['freq'] = self.freq
                    self.pump_status['duty'] = self.duty
                    return True
                return False
            except Exception as e:
                print(f"控制{self.device_name}失败: {e}")
                return False

    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'base_url': self.base_url,
            'freq': self.freq,
            'duty': self.duty,
            'mock_mode': self.mock
        }