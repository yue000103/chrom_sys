"""
色谱柱管理模型
Column management models
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .base_models import BaseResponse


class ColumnStatus(str, Enum):
    """色谱柱状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    DAMAGED = "damaged"


class ColumnType(str, Enum):
    """色谱柱类型枚举"""
    C18 = "C18"
    C8 = "C8"
    PHENYL = "Phenyl"
    CN = "CN"
    NH2 = "NH2"
    HILIC = "HILIC"
    ION_EXCHANGE = "Ion Exchange"
    SIZE_EXCLUSION = "Size Exclusion"
    CHIRAL = "Chiral"
    OTHER = "Other"


class ColumnInfo(BaseModel):
    """色谱柱信息模型 - 与数据库表结构匹配"""
    column_id: Optional[int] = None
    column_code: str = Field(..., min_length=1, max_length=50, description="色谱柱编码")
    specification_g: Optional[int] = Field(None, description="规格(g)")
    max_pressure_bar: Optional[int] = Field(None, gt=0, description="最大压力(bar)")
    flow_rate_ml_min: Optional[float] = Field(None, gt=0, description="流速(ml/min)")
    column_volume_cv_ml: Optional[float] = Field(None, gt=0, description="柱体积(ml)")
    sample_load_amount: Optional[str] = Field(None, description="样品载量")

    # 审计信息
    created_at: Optional[str] = None

    @validator('column_code')
    def validate_column_code(cls, v):
        """验证色谱柱编码"""
        if not v or not v.strip():
            raise ValueError('色谱柱编码不能为空')
        return v.strip()

    @validator('max_pressure_bar')
    def validate_pressure(cls, v):
        """验证压力范围"""
        if v is not None and v > 1000:
            raise ValueError('最大压力不能超过1000 bar')
        return v

    @validator('flow_rate_ml_min')
    def validate_flow_rate(cls, v):
        """验证流速范围"""
        if v is not None and v > 50:
            raise ValueError('流速不能超过50 ml/min')
        return v


class CreateColumnRequest(BaseModel):
    """创建色谱柱请求模型 - 与数据库表结构匹配"""
    column_code: str = Field(..., min_length=1, max_length=50, description="色谱柱编码")
    specification_g: Optional[int] = Field(None, description="规格(g)")
    max_pressure_bar: Optional[int] = Field(None, gt=0, description="最大压力(bar)")
    flow_rate_ml_min: Optional[float] = Field(None, gt=0, description="流速(ml/min)")
    column_volume_cv_ml: Optional[float] = Field(None, gt=0, description="柱体积(ml)")
    sample_load_amount: Optional[str] = Field(None, description="样品载量")


class UpdateColumnRequest(BaseModel):
    """更新色谱柱请求模型 - 与数据库表结构匹配"""
    column_code: Optional[str] = Field(None, min_length=1, max_length=50)
    specification_g: Optional[int] = None
    max_pressure_bar: Optional[int] = Field(None, gt=0)
    flow_rate_ml_min: Optional[float] = Field(None, gt=0)
    column_volume_cv_ml: Optional[float] = Field(None, gt=0)
    sample_load_amount: Optional[str] = None


class ColumnResponse(BaseResponse):
    """色谱柱响应模型"""
    column: Dict[str, Any]


class ColumnListResponse(BaseResponse):
    """色谱柱列表响应模型"""
    columns: List[Dict[str, Any]]
    total_count: int


class ColumnUsageInfo(BaseModel):
    """色谱柱使用情况模型 - 与数据库表结构匹配"""
    column_id: int
    column_code: str
    max_pressure_bar: Optional[int]
    methods_using_this_column: int
    method_names: List[str]
    created_at: Optional[str]


class ColumnUsageResponse(BaseResponse):
    """色谱柱使用情况响应模型"""
    usage_info: ColumnUsageInfo


class ColumnStatistics(BaseModel):
    """色谱柱统计信息模型"""
    total_columns: int
    status_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    total_usage_hours: float
    average_usage_hours: float
    columns_in_use: int
    most_used_column_id: Optional[int]
    timestamp: str


class ColumnStatisticsResponse(BaseResponse):
    """色谱柱统计响应模型"""
    statistics: ColumnStatistics


class ColumnSearchQuery(BaseModel):
    """色谱柱搜索查询模型 - 与数据库表结构匹配"""
    search_term: Optional[str] = Field(None, description="搜索关键词(编码、规格)")
    min_pressure: Optional[int] = Field(None, gt=0, description="最小压力(bar)")
    max_pressure: Optional[int] = Field(None, gt=0, description="最大压力(bar)")
    min_flow_rate: Optional[float] = Field(None, gt=0, description="最小流速(ml/min)")
    max_flow_rate: Optional[float] = Field(None, gt=0, description="最大流速(ml/min)")

    @validator('max_pressure')
    def validate_pressure_range(cls, v, values):
        """验证压力范围"""
        if v is not None and 'min_pressure' in values and values['min_pressure'] is not None:
            if v < values['min_pressure']:
                raise ValueError('最大压力不能小于最小压力')
        return v

    @validator('max_flow_rate')
    def validate_flow_rate_range(cls, v, values):
        """验证流速范围"""
        if v is not None and 'min_flow_rate' in values and values['min_flow_rate'] is not None:
            if v < values['min_flow_rate']:
                raise ValueError('最大流速不能小于最小流速')
        return v


class ColumnValidation(BaseModel):
    """色谱柱验证模型"""
    validation_id: Optional[str] = None
    column_id: int
    validation_type: str = Field(..., description="验证类型: performance, pressure, flow")
    validation_status: str = Field(..., description="验证状态: valid, invalid, pending")
    validation_date: str
    next_validation_due: Optional[str] = None
    validation_results: Dict[str, Any] = {}
    validation_notes: Optional[str] = None
    validated_by: str

    # 性能验证参数
    pressure_test_result: Optional[float] = None
    flow_test_result: Optional[float] = None
    resolution_test_result: Optional[float] = None
    efficiency_test_result: Optional[float] = None

    # 验证标准
    pressure_limit: Optional[float] = None
    flow_rate_target: Optional[float] = None
    min_resolution: Optional[float] = None
    min_efficiency: Optional[float] = None


class ColumnMaintenanceRecord(BaseModel):
    """色谱柱维护记录模型"""
    maintenance_id: Optional[str] = None
    column_id: int
    maintenance_type: str = Field(..., description="维护类型: cleaning, regeneration, inspection")
    maintenance_date: str
    maintenance_description: str
    performed_by: str
    duration_hours: Optional[float] = Field(None, ge=0)
    materials_used: Optional[List[str]] = []
    before_performance: Optional[Dict[str, float]] = {}
    after_performance: Optional[Dict[str, float]] = {}
    maintenance_cost: Optional[float] = Field(None, ge=0)
    next_maintenance_due: Optional[str] = None
    notes: Optional[str] = None