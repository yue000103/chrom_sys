"""
传感器接口
定义所有传感器的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from .device_interface import DeviceInterface


class SensorInterface(DeviceInterface, ABC):
    """传感器接口抽象类"""
    
    def __init__(self, device_id: str, sensor_type: str):
        super().__init__(device_id, 'sensor')
        self.sensor_type = sensor_type
        self.calibration_data = {}
        self.measurement_range = {}
        self.last_reading = None
    
    @abstractmethod
    async def read_value(self) -> Any:
        """读取传感器值"""
        pass
    
    @abstractmethod
    async def calibrate(self, calibration_params: Dict[str, Any]) -> bool:
        """校准传感器"""
        pass
    
    @abstractmethod
    async def zero_calibration(self) -> bool:
        """零点校准"""
        pass
    
    @abstractmethod
    async def set_range(self, min_value: float, max_value: float) -> bool:
        """设置测量范围"""
        pass
    
    @abstractmethod
    async def get_range(self) -> Dict[str, float]:
        """获取测量范围"""
        pass
    
    @abstractmethod
    async def start_continuous_reading(self, callback: Callable, interval: float = 1.0):
        """
        开始连续读取
        :param callback: 数据回调函数
        :param interval: 读取间隔(秒)
        """
        pass
    
    @abstractmethod
    async def stop_continuous_reading(self) -> bool:
        """停止连续读取"""
        pass
    
    @abstractmethod
    async def get_accuracy(self) -> float:
        """获取传感器精度"""
        pass
    
    @abstractmethod
    async def get_unit(self) -> str:
        """获取测量单位"""
        pass
    
    async def validate_reading(self, value: Any) -> bool:
        """验证读数是否有效"""
        if self.measurement_range:
            min_val = self.measurement_range.get('min', float('-inf'))
            max_val = self.measurement_range.get('max', float('inf'))
            return min_val <= value <= max_val
        return True