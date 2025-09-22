"""
试管架信息相关数据模型
Rack Info Data Models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class CreateRackInfoRequest(BaseModel):
    """创建试管架信息请求"""
    tube_volume_ml: int = Field(..., ge=1, le=100, description="试管容量(毫升)")
    tube_count: int = Field(..., ge=1, le=200, description="试管数量")
    rack_name: str = Field(..., min_length=1, max_length=100, description="试管架名称")
    status: Optional[str] = Field("未使用", description="试管架状态：使用/未使用")

    class Config:
        schema_extra = {
            "example": {
                "tube_volume_ml": 10,
                "tube_count": 40,
                "rack_name": "主试管架1",
                "status": "未使用"
            }
        }


class UpdateRackInfoRequest(BaseModel):
    """更新试管架信息请求"""
    tube_volume_ml: Optional[int] = Field(None, ge=1, le=100, description="试管容量(毫升)")
    tube_count: Optional[int] = Field(None, ge=1, le=200, description="试管数量")
    rack_name: Optional[str] = Field(None, min_length=1, max_length=100, description="试管架名称")
    status: Optional[str] = Field(None, description="试管架状态：使用/未使用")

    class Config:
        schema_extra = {
            "example": {
                "tube_volume_ml": 15,
                "tube_count": 50,
                "rack_name": "更新的试管架名称",
                "status": "使用"
            }
        }


class RackInfoResponse(BaseModel):
    """试管架信息响应"""
    success: bool = True
    message: str = "操作成功"
    rack_info: Optional[dict] = None


class RackInfoListResponse(BaseModel):
    """试管架信息列表响应"""
    success: bool = True
    message: str = "获取试管架列表成功"
    rack_list: list = []
    total_count: int = 0
    active_count: int = 0
    total_capacity: int = 0
    total_occupied: int = 0


class UpdateRackStatusRequest(BaseModel):
    """更新试管架状态请求"""
    status: str = Field(..., description="试管架状态：使用/未使用")

    class Config:
        schema_extra = {
            "example": {
                "status": "使用"
            }
        }


class RackInfoStatisticsResponse(BaseModel):
    """试管架统计信息响应"""
    success: bool = True
    message: str = "获取试管架统计信息成功"
    statistics: dict = {}


