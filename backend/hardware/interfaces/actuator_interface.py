"""
执行器接口
定义所有执行器(泵、阀门、继电器等)的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .device_interface import DeviceInterface


class ActuatorInterface(DeviceInterface, ABC):
    """执行器接口抽象类"""
    
    def __init__(self, device_id: str, actuator_type: str):
        super().__init__(device_id, 'actuator')
        self.actuator_type = actuator_type
        self.operation_mode = 'manual'  # manual/automatic
        self.safety_lock = False
    
    @abstractmethod
    async def activate(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """激活执行器"""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """停用执行器"""
        pass
    
    @abstractmethod
    async def set_position(self, position: Any) -> bool:
        """设置位置"""
        pass
    
    @abstractmethod
    async def get_position(self) -> Any:
        """获取当前位置"""
        pass
    
    @abstractmethod
    async def move_to(self, target: Any, speed: Optional[float] = None) -> bool:
        """
        移动到目标位置
        :param target: 目标位置
        :param speed: 移动速度
        :return: 操作结果
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止动作"""
        pass
    
    @abstractmethod
    async def home(self) -> bool:
        """回归原点"""
        pass
    
    @abstractmethod
    async def set_speed(self, speed: float) -> bool:
        """设置速度"""
        pass
    
    @abstractmethod
    async def get_speed(self) -> float:
        """获取当前速度"""
        pass
    
    async def enable_safety_lock(self) -> bool:
        """启用安全锁"""
        self.safety_lock = True
        return True
    
    async def disable_safety_lock(self) -> bool:
        """禁用安全锁"""
        self.safety_lock = False
        return True
    
    async def is_moving(self) -> bool:
        """检查是否正在移动"""
        status = await self.get_status()
        return status.get('is_moving', False)
    
    async def set_mode(self, mode: str) -> bool:
        """
        设置操作模式
        :param mode: manual/automatic
        :return: 设置结果
        """
        if mode in ['manual', 'automatic']:
            self.operation_mode = mode
            return True
        return False