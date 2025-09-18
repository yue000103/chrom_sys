"""
硬件配置管理
控制设备的mock模式和其他配置
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import random


@dataclass
class HardwareConfig:
    """硬件配置类"""
    mock_mode: bool = False  # 是否启用mock模式
    connection_timeout: int = 30  # 连接超时时间
    retry_count: int = 3  # 重试次数
    log_enabled: bool = True  # 是否启用日志


class HardwareManager:
    """硬件管理器 - 管理所有设备的mock模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.config = HardwareConfig()
            self.device_configs: Dict[str, HardwareConfig] = {}
            self.initialized = True

    def set_mock_mode(self, mock: bool) -> bool:
        """
        设置全局mock模式
        :param mock: True为模拟模式，False为联机模式
        :return: 设置结果
        """
        self.config.mock_mode = mock
        return True

    def get_mock_mode(self) -> bool:
        """获取当前mock模式"""
        return self.config.mock_mode

    def set_device_mock_mode(self, device_id: str, mock: bool) -> bool:
        """
        设置特定设备的mock模式
        :param device_id: 设备ID
        :param mock: True为模拟模式，False为联机模式
        :return: 设置结果
        """
        if device_id not in self.device_configs:
            self.device_configs[device_id] = HardwareConfig()
        self.device_configs[device_id].mock_mode = mock
        return True

    def get_device_mock_mode(self, device_id: str) -> bool:
        """
        获取特定设备的mock模式
        :param device_id: 设备ID
        :return: mock模式状态
        """
        if device_id in self.device_configs:
            return self.device_configs[device_id].mock_mode
        return self.config.mock_mode

    def get_config(self) -> HardwareConfig:
        """获取全局配置"""
        return self.config

    def get_device_config(self, device_id: str) -> HardwareConfig:
        """获取设备配置"""
        if device_id in self.device_configs:
            return self.device_configs[device_id]
        return self.config


class MockDataGenerator:
    """Mock数据生成器"""

    @staticmethod
    def generate_pressure(min_val: float = 0.0, max_val: float = 10.0) -> float:
        """生成模拟压力值(MPa)"""
        return round(random.uniform(min_val, max_val), 2)

    @staticmethod
    def generate_flow_rate(min_val: float = 0.1, max_val: float = 5.0) -> float:
        """生成模拟流速(mL/min)"""
        return round(random.uniform(min_val, max_val), 2)

    @staticmethod
    def generate_signal(min_val: float = 0.0, max_val: float = 1000.0) -> float:
        """生成模拟检测器信号"""
        return round(random.uniform(min_val, max_val), 2)

    @staticmethod
    def generate_temperature(min_val: float = 20.0, max_val: float = 80.0) -> float:
        """生成模拟温度(℃)"""
        return round(random.uniform(min_val, max_val), 1)

    @staticmethod
    def generate_bubble_status() -> bool:
        """生成模拟气泡检测状态"""
        return random.choice([True, False])

    @staticmethod
    def generate_valve_position(max_positions: int = 6) -> int:
        """生成模拟阀门位置"""
        return random.randint(1, max_positions)

    @staticmethod
    def generate_success_status(success_rate: float = 0.95) -> bool:
        """生成模拟操作成功状态"""
        return random.random() < success_rate

    @staticmethod
    def generate_device_status() -> str:
        """生成模拟设备状态"""
        return random.choice(['idle', 'running', 'stopped', 'error', 'maintenance'])

    @staticmethod
    def generate_spectrum_data(points: int = 100) -> list:
        """生成模拟光谱数据"""
        return [
            {
                'wavelength': 200 + i * 5,
                'intensity': MockDataGenerator.generate_signal(0, 1000)
            }
            for i in range(points)
        ]


# 创建全局硬件管理器实例
hardware_manager = HardwareManager()

# 导出的函数
def set_global_mock_mode(mock: bool) -> bool:
    """
    设置全局mock模式
    :param mock: True为模拟模式，False为联机模式
    :return: 设置结果
    """
    return hardware_manager.set_mock_mode(mock)


def get_global_mock_mode() -> bool:
    """获取全局mock模式"""
    return hardware_manager.get_mock_mode()


def is_mock_mode(device_id: Optional[str] = None) -> bool:
    """
    检查是否为mock模式
    :param device_id: 设备ID，如果为None则检查全局模式
    :return: 是否为mock模式
    """
    if device_id:
        return hardware_manager.get_device_mock_mode(device_id)
    return hardware_manager.get_mock_mode()


__all__ = [
    'HardwareConfig',
    'HardwareManager',
    'MockDataGenerator',
    'hardware_manager',
    'set_global_mock_mode',
    'get_global_mock_mode',
    'is_mock_mode'
]