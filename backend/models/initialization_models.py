"""
初始化相关模型
Initialization related models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_models import DeviceType, CommunicationType


class DeviceConfig(BaseModel):
    """设备配置模型"""
    device_id: str
    device_name: str
    device_type: DeviceType
    communication_type: CommunicationType
    connection_params: Dict[str, Any]
    is_enabled: bool = True
    description: Optional[str] = None


class SystemInitConfig(BaseModel):
    """系统初始化配置"""
    mqtt_broker: str = "broker.emqx.io"
    mqtt_port: int = 1883
    database_path: str = "data/database/chromatography.db"
    host_devices: List[DeviceConfig] = []
    collect_devices: List[DeviceConfig] = []
    enable_hardware: bool = True
    enable_mqtt: bool = True
    debug_mode: bool = False


class DeviceInitResult(BaseModel):
    """单个设备初始化结果"""
    device_id: str
    device_name: str
    success: bool
    error_message: Optional[str] = None
    initialization_time: float


class InitializationResult(BaseModel):
    """系统初始化结果"""
    total_devices: int
    initialized_devices: int
    failed_devices: List[str] = []
    device_results: List[DeviceInitResult] = []
    initialization_time: float
    success: bool
    mqtt_connected: bool = False
    database_ready: bool = False