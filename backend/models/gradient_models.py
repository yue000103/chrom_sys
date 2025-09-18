"""
梯度曲线模型
Gradient curve models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GradientType(str, Enum):
    """梯度类型枚举"""
    LINEAR = "linear"
    STEP = "step"
    CURVE = "curve"


class GradientPoint(BaseModel):
    """梯度点模型"""
    time_minutes: float = Field(ge=0, description="时间(分钟)")
    mobile_phase_a_percent: float = Field(ge=0, le=100, description="流动相A百分比")
    mobile_phase_b_percent: float = Field(ge=0, le=100, description="流动相B百分比")
    flow_rate_ml_min: float = Field(gt=0, description="流速(mL/min)")
    gradient_type: GradientType = GradientType.LINEAR

    @validator('mobile_phase_b_percent')
    def validate_phase_percentages(cls, v, values):
        """验证流动相百分比总和为100"""
        if 'mobile_phase_a_percent' in values:
            total = v + values['mobile_phase_a_percent']
            if abs(total - 100.0) > 0.1:  # 允许0.1%的误差
                raise ValueError('流动相A和B的百分比总和必须为100%')
        return v


class GradientProgram(BaseModel):
    """梯度程序模型"""
    program_id: str
    program_name: str
    description: Optional[str] = None
    gradient_points: List[GradientPoint]
    total_duration: float = Field(gt=0, description="总时长(分钟)")
    equilibration_time: float = Field(default=5.0, ge=0, description="平衡时间(分钟)")
    post_run_time: float = Field(default=2.0, ge=0, description="后运行时间(分钟)")
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0"

    @validator('gradient_points')
    def validate_gradient_points(cls, v):
        """验证梯度点"""
        if len(v) < 2:
            raise ValueError('梯度程序至少需要2个梯度点')

        # 验证时间点是否递增
        times = [point.time_minutes for point in v]
        if times != sorted(times):
            raise ValueError('梯度点的时间必须递增')

        # 验证第一个点的时间为0
        if v[0].time_minutes != 0:
            raise ValueError('第一个梯度点的时间必须为0')

        return v


class GradientExecutionStatus(BaseModel):
    """梯度执行状态"""
    program_id: str
    experiment_id: str
    current_time: float = Field(ge=0, description="当前时间(分钟)")
    current_point: GradientPoint
    next_point: Optional[GradientPoint] = None
    is_running: bool = False
    is_paused: bool = False
    completion_percentage: float = Field(ge=0, le=100)
    start_time: Optional[datetime] = None
    estimated_end_time: Optional[datetime] = None
    actual_flow_rate: Optional[float] = None
    actual_phase_a_percent: Optional[float] = None
    actual_phase_b_percent: Optional[float] = None


class GradientValidation(BaseModel):
    """梯度程序验证"""
    program_id: str
    validation_status: str  # "valid", "invalid", "warning"
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    max_pressure_estimate: Optional[float] = None
    min_flow_rate: Optional[float] = None
    max_flow_rate: Optional[float] = None


class GradientTemplate(BaseModel):
    """梯度模板"""
    template_id: str
    template_name: str
    description: str
    category: str  # "analytical", "preparative", "cleanup"
    gradient_points: List[GradientPoint]
    recommended_column_types: List[str] = []
    recommended_applications: List[str] = []
    is_public: bool = True
    created_by: str
    usage_count: int = 0

class GradientStep(BaseModel):
    """梯度步骤"""
    step_id: str
    step_name: str
    step_type: str  # "hold", "ramp", "step"
    duration_minutes: float = Field(gt=0, description="持续时间(分钟)")
    target_phase_a_percent: float = Field(ge=0, le=100, description="目标流动相A百分比")
    target_phase_b_percent: float = Field(ge=0, le=100, description="目标流动相B百分比")
    flow_rate_ml_min: float = Field(gt=0, description="流速(mL/min)")

    @validator('target_phase_b_percent')
    def validate_step_phase_percentages(cls, v, values):
        """验证步骤流动相百分比总和为100"""
        if 'target_phase_a_percent' in values:
            total = v + values['target_phase_a_percent']
            if abs(total - 100.0) > 0.1:  # 允许0.1%的误差
                raise ValueError('步骤中流动相A和B的百分比总和必须为100%')
        return v

class GradientCurve(BaseModel):
    """梯度曲线分析"""
    program_id: str
    experiment_id: str
    retention_time_shifts: List[float] = []
    peak_shape_changes: Dict[str, Any] = {}
    resolution_changes: Dict[str, Any] = {}
    analysis_date: datetime = Field(default_factory=datetime.now)
    analyst: Optional[str] = None
    comments: Optional[str] = None

class GradientExecution(BaseModel):
    """梯度执行日志"""
    log_id: str
    program_id: str
    experiment_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str
    log_level: str  # "info", "warning", "error"
    current_time: Optional[float] = None
    current_phase_a_percent: Optional[float] = None
    current_phase_b_percent: Optional[float] = None
    flow_rate_ml_min: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None

class GradientProfile(BaseModel):
    """梯度配置文件"""
    profile_id: str
    profile_name: str
    description: Optional[str] = None
    gradient_programs: List[GradientProgram]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    tags: List[str] = []

class FlowControlType(str, Enum):
    """流速控制类型枚举"""
    CONSTANT = "constant"
    VARIABLE = "variable"
    PROGRAMMED = "programmed"