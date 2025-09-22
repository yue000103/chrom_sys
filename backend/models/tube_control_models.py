"""
试管控制相关数据模型
Tube Control Data Models
"""

from pydantic import BaseModel, Field
from typing import Optional


class TubeSwitchRequest(BaseModel):
    """试管切换请求"""
    tube_id: int = Field(..., ge=1, description="试管ID")

    class Config:
        schema_extra = {
            "example": {
                "tube_id": 1
            }
        }


class TubeSwitchResponse(BaseModel):
    """试管切换响应"""
    success: bool = True
    message: str = "试管切换成功"
    tube_id: int
    module_number: int
    tube_number: int
    total_steps: int = 0
    success_steps: int = 0
    execution_time: Optional[float] = None
    step_results: list = []


class TubeCalculationResponse(BaseModel):
    """试管号计算响应"""
    success: bool = True
    message: str = "试管号计算成功"
    tube_id: int
    module_number: int
    tube_number: int


class DirectTubeSwitchRequest(BaseModel):
    """直接试管切换请求"""
    module_number: int = Field(..., ge=1, description="模块号")
    tube_number: int = Field(..., ge=1, le=6, description="试管号")

    class Config:
        schema_extra = {
            "example": {
                "module_number": 1,
                "tube_number": 1
            }
        }