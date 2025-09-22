"""
实验数据相关数据模型
Experiment Data Models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateExperimentRequest(BaseModel):
    """创建实验请求"""
    experiment_name: str = Field(..., min_length=1, max_length=200, description="实验名称")
    experiment_type: Optional[str] = Field("standard", max_length=50, description="实验类型")
    method_id:  Optional[int] = Field(0, ge=0, description="方法id")
    operator: Optional[str] = Field("unknown", max_length=100, description="操作员")
    purge_system: Optional[bool] = Field(False, description="系统清洗")
    purge_column: Optional[bool] = Field(False, description="柱子清洗")
    purge_column_time_min: Optional[int] = Field(0, ge=0, description="柱子清洗时间(分钟)")
    column_balance: Optional[bool] = Field(False, description="柱平衡")
    column_balance_time_min: Optional[int] = Field(0, ge=0, description="柱平衡时间(分钟)")
    is_peak_driven: Optional[bool] = Field(False, description="峰驱动")
    collection_volume_ml: Optional[float] = Field(0.0, ge=0, description="收集体积(毫升)")
    wash_volume_ml: Optional[float] = Field(0.0, ge=0, description="清洗体积(毫升)")
    wash_cycles: Optional[int] = Field(0, ge=0, description="清洗周期")
    column_conditioning_solution: Optional[int] = Field(None, description="润柱溶液")
    scheduled_start_time: Optional[datetime] = Field(None, description="计划开始时间")
    priority: Optional[int] = Field(1, ge=1, le=10, description="优先级(1-10)")
    description: Optional[str] = Field(None, description="描述")
    experiment_description: Optional[str] = Field(None, description="实验描述")

    class Config:
        schema_extra = {
            "example": {
                "experiment_name": "测试实验001",
                "experiment_type": "standard",
                "method_id": "METHOD_001",
                "operator": "张三",
                "purge_system": True,
                "purge_column": True,
                "purge_column_time_min": 5,
                "column_balance": True,
                "column_balance_time_min": 10,
                "is_peak_driven": False,
                "collection_volume_ml": 2.0,
                "wash_volume_ml": 1.0,
                "wash_cycles": 3,
                "column_conditioning_solution": 1,
                "priority": 1,
                "description": "标准测试实验"
            }
        }


class UpdateExperimentRequest(BaseModel):
    """更新实验请求（不包含method_id）"""
    experiment_name: Optional[str] = Field(None, min_length=1, max_length=200, description="实验名称")
    experiment_type: Optional[str] = Field(None, max_length=50, description="实验类型")
    operator: Optional[str] = Field(None, max_length=100, description="操作员")
    purge_system: Optional[bool] = Field(None, description="系统清洗")
    purge_column: Optional[bool] = Field(None, description="柱子清洗")
    purge_column_time_min: Optional[int] = Field(None, ge=0, description="柱子清洗时间(分钟)")
    column_balance: Optional[bool] = Field(None, description="柱平衡")
    column_balance_time_min: Optional[int] = Field(None, ge=0, description="柱平衡时间(分钟)")
    is_peak_driven: Optional[bool] = Field(None, description="峰驱动")
    collection_volume_ml: Optional[float] = Field(None, ge=0, description="收集体积(毫升)")
    wash_volume_ml: Optional[float] = Field(None, ge=0, description="清洗体积(毫升)")
    wash_cycles: Optional[int] = Field(None, ge=0, description="清洗周期")
    column_conditioning_solution: Optional[int] = Field(None, description="润柱溶液")
    scheduled_start_time: Optional[datetime] = Field(None, description="计划开始时间")
    priority: Optional[int] = Field(None, ge=1, le=10, description="优先级(1-10)")
    description: Optional[str] = Field(None, description="描述")
    experiment_description: Optional[str] = Field(None, description="实验描述")
    status: Optional[str] = Field(None, max_length=20, description="状态")

    class Config:
        schema_extra = {
            "example": {
                "experiment_name": "更新的实验名称",
                "operator": "李四",
                "priority": 2,
                "status": "running"
            }
        }


class ExperimentResponse(BaseModel):
    """实验响应"""
    success: bool = True
    message: str = "操作成功"
    experiment: Optional[dict] = None


class ExperimentListResponse(BaseModel):
    """实验列表响应"""
    success: bool = True
    message: str = "获取实验列表成功"
    experiments: list = []
    total_count: int = 0