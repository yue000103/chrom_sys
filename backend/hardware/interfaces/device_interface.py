"""
设备通用接口
定义所有设备的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..hardware_config import is_mock_mode


class DeviceInterface(ABC):
    """设备通用接口抽象类"""

    def __init__(self, device_id: str, device_type: str, mock: Optional[bool] = None):
        self.device_id = device_id
        self.device_type = device_type
        self.status = 'disconnected'
        self.config = {}
        self.mock = mock if mock is not None else is_mock_mode(device_id)
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接设备"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开设备连接"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化设备"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        pass
    
    @abstractmethod
    async def reset(self) -> bool:
        """重置设备"""
        pass
    
    @abstractmethod
    async def self_test(self) -> Dict[str, Any]:
        """设备自检"""
        pass
    
    @abstractmethod
    async def get_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        pass
    
    @abstractmethod
    async def configure(self, config: Dict[str, Any]) -> bool:
        """配置设备"""
        pass
    
    def is_connected(self) -> bool:
        """检查设备是否连接"""
        return self.status == 'connected'

    async def emergency_stop(self) -> bool:
        """紧急停止"""
        return await self.reset()

    def set_mock_mode(self, mock: bool):
        """
        设置mock模式
        :param mock: True为模拟模式，False为联机模式
        """
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """
        检查是否为mock模式
        :return: 是否为mock模式
        """
        return self.mock