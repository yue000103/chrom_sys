"""
基础通用模型
Base models for the chromatography system
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """设备类型枚举"""
    RELAY = "relay"
    SENSOR = "sensor"
    PUMP = "pump"
    VALVE = "valve"
    DETECTOR = "detector"
    BUBBLE_SENSOR = "bubble_sensor"
    LED = "led"
    MULTI_VALVE = "multi_valve"


class DeviceStatus(str, Enum):
    """设备状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class CommunicationType(str, Enum):
    """通信类型枚举"""
    SERIAL = "serial"
    HTTP = "http"
    MQTT = "mqtt"


class BaseResponse(BaseModel):
    """API响应基础模型"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    error_code: str
    error_details: str = ""
    success: bool = False