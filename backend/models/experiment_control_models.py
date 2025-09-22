"""
实验控制相关数据模型
Experiment Control Data Models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class CreateExperimentRequest(BaseModel):
    """创建实验请求"""
    experiment_name: str = Field(..., min_length=1, max_length=200, description="实验名称")
    experiment_description: Optional[str] = Field(None, description="实验描述")
    operator: str = Field(..., min_length=1, max_length=100, description="操作员")
    method_id: str = Field(..., min_length=1, max_length=100, description="方法ID")
    purge_system: bool = Field(False, description="吹扫系统")
    purge_column: bool = Field(False, description="吹扫柱子")
    purge_column_time_min: Optional[int] = Field(None, ge=0, le=120, description="吹扫柱子时间(分钟)")
    column_balance: bool = Field(False, description="柱平衡")
    column_balance_time_min: Optional[int] = Field(None, ge=0, le=120, description="柱平衡时间(分钟)")
    is_peak_driven: bool = Field(False, description="是否峰驱动")
    collection_volume_ml: Optional[float] = Field(None, ge=0, le=1000, description="收集体积(ml)")
    wash_volume_ml: Optional[float] = Field(None, ge=0, le=1000, description="清洗体积(ml)")
    wash_cycles: Optional[int] = Field(None, ge=0, le=10, description="清洗次数")
    column_conditioning_solution: Optional[int] = Field(None, description="润柱溶液")
    scheduled_start_time: Optional[datetime] = Field(None, description="预计开始时间")
    priority: int = Field(1, ge=1, le=4, description="优先级(1-4，数字越高等级越高)")

    @validator('purge_column_time_min')
    def validate_purge_time(cls, v, values):
        """验证吹扫时间"""
        if values.get('purge_column') and v is None:
            raise ValueError("启用吹扫柱子时必须设置吹扫时间")
        return v

    @validator('column_balance_time_min')
    def validate_balance_time(cls, v, values):
        """验证平衡时间"""
        if values.get('column_balance') and v is None:
            raise ValueError("启用柱平衡时必须设置平衡时间")
        return v

    class Config:
        schema_extra = {
            "example": {
                "experiment_name": "蛋白质分离实验_001",
                "experiment_description": "使用新方法分离目标蛋白质",
                "operator": "张三",
                "method_id": "METHOD_001",
                "purge_system": True,
                "purge_column": True,
                "purge_column_time_min": 10,
                "column_balance": True,
                "column_balance_time_min": 15,
                "is_peak_driven": False,
                "collection_volume_ml": 50.0,
                "wash_volume_ml": 100.0,
                "wash_cycles": 3,
                "column_conditioning_solution": 1,
                "scheduled_start_time": "2025-09-19T09:00:00",
                "priority": 3
            }
        }


class ExperimentResponse(BaseModel):
    """实验响应"""
    success: bool = True
    message: str = "操作成功"
    experiment_id: Optional[str] = None
    experiment: Optional[dict] = None


class ExperimentListResponse(BaseModel):
    """实验列表响应"""
    success: bool = True
    message: str = "获取实验列表成功"
    experiments: list = []
    total_count: int = 0


class UpdateExperimentStatusRequest(BaseModel):
    """更新实验状态请求"""
    status: str = Field(..., regex="^(已结束|未结束)$", description="实验状态")


class ExperimentQueueStatusResponse(BaseModel):
    """实验队列状态响应"""
    success: bool = True
    message: str = "获取实验队列状态成功"
    queue_status: dict = {}


class ExperimentStatisticsResponse(BaseModel):
    """实验统计信息响应"""
    success: bool = True
    message: str = "获取实验统计信息成功"
    statistics: dict = {}


class ExperimentStatusResponse(BaseModel):
    """实验状态查询响应"""
    success: bool = True
    message: str = "获取实验状态成功"
    experiment_id: int
    status: str = Field(..., description="实验状态：pending、pretreatment、running、paused、completed、terminated")
    current_step: Optional[str] = Field(None, description="当前预处理步骤：purge_column、purge_system、column_equilibration")
    step_status: Optional[str] = Field(None, description="步骤状态：started、completed")
    is_paused: bool = False
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "获取实验状态成功",
                "experiment_id": 123,
                "status": "pretreatment",
                "current_step": "purge_column",
                "step_status": "started",
                "is_paused": False,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }