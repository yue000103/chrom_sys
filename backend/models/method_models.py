"""
方法管理模型
Method management models
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .gradient_models import GradientProgram
from .tube_models import TubeSequence


class MethodType(str, Enum):
    """方法类型枚举"""
    ANALYTICAL = "analytical"
    PREPARATIVE = "preparative"
    CLEANUP = "cleanup"
    CALIBRATION = "calibration"
    QC = "qc"


class MethodStatus(str, Enum):
    """方法状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"


class DetectionParameters(BaseModel):
    """检测参数模型"""
    detector_type: str  # "UV", "Fluorescence", "MS"
    wavelength_nm: Optional[float] = None
    bandwidth_nm: Optional[float] = None
    sensitivity: str = "medium"  # "low", "medium", "high"
    sampling_rate_hz: float = Field(default=10.0, gt=0)
    filter_settings: Dict[str, Any] = {}
    calibration_curve: Optional[Dict[str, Any]] = None


class ColumnParameters(BaseModel):
    """色谱柱参数模型"""
    column_id: str
    column_name: str
    column_type: str  # "C18", "C8", "Phenyl"
    length_mm: float = Field(gt=0)
    diameter_mm: float = Field(gt=0)
    particle_size_um: float = Field(gt=0)
    manufacturer: str
    part_number: str
    installation_date: Optional[datetime] = None
    usage_hours: float = Field(default=0.0, ge=0)
    max_pressure_bar: float = Field(gt=0)
    temperature_range: Dict[str, float] = {"min": 15, "max": 60}


class AnalysisMethod(BaseModel):
    """分析方法模型"""
    method_id: str
    method_name: str
    method_type: MethodType
    method_status: MethodStatus = MethodStatus.DRAFT
    version: str = "1.0"
    description: str

    # 方法组件
    gradient_program: GradientProgram
    tube_sequence: TubeSequence
    detection_parameters: DetectionParameters
    column_parameters: ColumnParameters

    # 运行参数
    injection_volume_ul: float = Field(default=10.0, gt=0)
    column_temperature_celsius: float = Field(default=30.0, ge=4, le=80)
    autosampler_temperature_celsius: Optional[float] = None
    run_time_minutes: float = Field(gt=0)
    post_run_time_minutes: float = Field(default=2.0, ge=0)

    # 数据处理参数
    baseline_correction: bool = True
    noise_filtering: bool = True
    peak_detection_threshold: float = Field(default=0.01, gt=0)
    integration_parameters: Dict[str, Any] = {}

    # 方法元数据
    application: str  # "Pharmaceutical", "Environmental", "Food"
    target_compounds: List[str] = []
    matrix_type: str = "aqueous"
    regulatory_compliance: List[str] = []  # "FDA", "ICH", "USP"

    # 审计信息
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # 使用统计
    usage_count: int = Field(default=0, ge=0)
    last_used: Optional[datetime] = None

    @validator('run_time_minutes')
    def validate_run_time(cls, v, values):
        """验证运行时间与梯度程序一致"""
        if 'gradient_program' in values:
            gradient_time = values['gradient_program'].total_duration
            if v < gradient_time:
                raise ValueError('运行时间不能小于梯度程序时间')
        return v


class MethodValidation(BaseModel):
    """方法验证模型"""
    validation_id: str
    method_id: str
    validation_type: str  # "analytical", "system_suitability", "robustness"
    validation_status: str  # "valid", "invalid", "pending", "expired"
    validation_criteria: Dict[str, Any]
    validation_results: Dict[str, Any] = {}
    validation_errors: List[str] = []
    validation_warnings: List[str] = []

    # 验证参数
    linearity_r2: Optional[float] = Field(None, ge=0, le=1)
    precision_rsd: Optional[float] = Field(None, ge=0, le=100)
    accuracy_recovery: Optional[float] = Field(None, ge=0, le=200)
    limit_of_detection: Optional[float] = None
    limit_of_quantification: Optional[float] = None

    # 审计信息
    validated_by: str
    validated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    review_required: bool = False
    next_validation_due: Optional[datetime] = None


class MethodTemplate(BaseModel):
    """方法模板模型"""
    template_id: str
    template_name: str
    category: str
    base_method: AnalysisMethod
    customizable_parameters: List[str] = []
    parameter_ranges: Dict[str, Dict[str, float]] = {}
    description: str
    usage_instructions: str
    is_public: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    download_count: int = Field(default=0, ge=0)


class MethodComparison(BaseModel):
    """方法比较模型"""
    comparison_id: str
    method_ids: List[str]
    comparison_type: str  # "performance", "parameters", "results"
    comparison_criteria: List[str]
    comparison_results: Dict[str, Any] = {}
    recommended_method: Optional[str] = None
    comparison_notes: Optional[str] = None
    compared_by: str
    compared_at: datetime = Field(default_factory=datetime.now)


class MethodHistory(BaseModel):
    """方法历史记录"""
    history_id: str
    method_id: str
    action_type: str  # "created", "modified", "validated", "archived"
    action_description: str
    changes_made: Dict[str, Any] = {}
    previous_version: Optional[str] = None
    new_version: Optional[str] = None
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.now)
    reason: Optional[str] = None