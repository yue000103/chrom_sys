"""
预处理模型
Preprocessing models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class CheckType(str, Enum):
    """检查类型枚举"""
    DEVICE = "device"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    CONNECTIVITY = "connectivity"
    FLOW_RATE = "flow_rate"
    DETECTOR = "detector"
    AUTOSAMPLER = "autosampler"
    COLUMN = "column"


class CheckStatus(str, Enum):
    """检查状态枚举"""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    NOT_APPLICABLE = "not_applicable"


class TaskType(str, Enum):
    """任务类型枚举"""
    SYSTEM_CHECK = "system_check"
    CALIBRATION = "calibration"
    CLEANING = "cleaning"
    PRIMING = "priming"
    BASELINE_STABILIZATION = "baseline_stabilization"
    COLUMN_CONDITIONING = "column_conditioning"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class SystemCheckItem(BaseModel):
    """系统检查项"""
    check_id: str
    check_name: str
    check_type: CheckType
    device_id: Optional[str] = None
    expected_value: Any
    actual_value: Optional[Any] = None
    tolerance: Optional[float] = None
    units: Optional[str] = None
    status: CheckStatus = CheckStatus.PENDING
    message: Optional[str] = None
    check_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    auto_retry: bool = False
    retry_count: int = 0
    max_retries: int = 3


class PreprocessingTask(BaseModel):
    """预处理任务"""
    task_id: str
    task_name: str
    task_type: TaskType
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    prerequisites: List[str] = []  # 前置任务ID列表
    estimated_duration_seconds: Optional[float] = None
    actual_duration_seconds: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    progress_percentage: float = Field(default=0.0, ge=0, le=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    assigned_devices: List[str] = []
    error_message: Optional[str] = None
    logs: List[str] = []
    auto_continue: bool = True
    user_confirmation_required: bool = False


class SystemCalibration(BaseModel):
    """系统校准模型"""
    calibration_id: str
    device_id: str
    calibration_type: str  # "pressure", "flow", "detector", "autosampler"
    calibration_standard: str
    reference_values: List[float]
    measured_values: List[float] = []
    calibration_curve: Optional[Dict[str, Any]] = None
    r_squared: Optional[float] = None
    calibration_status: str = "pending"  # "pending", "running", "completed", "failed"
    calibration_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None


class CleaningProtocol(BaseModel):
    """清洗协议模型"""
    protocol_id: str
    protocol_name: str
    cleaning_type: str  # "routine", "deep", "solvent_change", "maintenance"
    steps: List[PreprocessingTask]
    total_duration_minutes: float = Field(gt=0)
    required_solvents: List[str] = []
    required_volumes_ml: List[float] = []
    temperature_celsius: Optional[float] = None
    flow_rate_ml_min: Optional[float] = None
    success_criteria: Dict[str, Any] = {}
    safety_warnings: List[str] = []


class BaselineStabilization(BaseModel):
    """基线稳定化模型"""
    stabilization_id: str
    detector_id: str
    target_baseline: float
    baseline_tolerance: float = 0.001
    stabilization_time_minutes: float = Field(default=10.0, gt=0)
    current_baseline: Optional[float] = None
    baseline_drift: Optional[float] = None
    is_stable: bool = False
    start_time: Optional[datetime] = None
    stabilization_achieved_at: Optional[datetime] = None
    baseline_history: List[float] = []


class PreprocessingResult(BaseModel):
    """预处理结果"""
    result_id: str
    experiment_id: str
    preprocessing_start_time: datetime
    preprocessing_end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None

    # 检查结果
    system_checks: List[SystemCheckItem] = []
    checks_passed: int = 0
    checks_failed: int = 0
    checks_with_warnings: int = 0

    # 任务结果
    preprocessing_tasks: List[PreprocessingTask] = []
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0

    # 校准结果
    calibrations_performed: List[SystemCalibration] = []
    calibrations_successful: int = 0

    # 总体状态
    all_checks_passed: bool = False
    critical_failures: List[str] = []
    warnings: List[str] = []
    ready_for_experiment: bool = False
    requires_manual_intervention: bool = False

    # 质量评分
    system_readiness_score: float = Field(default=0.0, ge=0, le=100)
    confidence_level: str = "low"  # "low", "medium", "high"

    # 推荐操作
    recommended_actions: List[str] = []
    estimated_fix_time_minutes: Optional[float] = None

    performed_by: str
    reviewed_by: Optional[str] = None
    approved_for_experiment: bool = False