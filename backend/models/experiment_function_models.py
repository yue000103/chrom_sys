"""
实验功能模型
Experiment function models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ExperimentPhase(str, Enum):
    """实验阶段枚举"""
    PRE_EXPERIMENT = "pre_experiment"
    DURING_EXPERIMENT = "during_experiment"
    POST_EXPERIMENT = "post_experiment"


class ExperimentStatus(str, Enum):
    """实验状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentConfig(BaseModel):
    """实验配置模型"""
    experiment_id: str
    experiment_name: str
    method_id: str
    sample_id: str
    user_id: str
    priority: int = Field(default=1, ge=1, le=5)  # 1-5优先级
    created_at: datetime = Field(default_factory=datetime.now)
    scheduled_start: Optional[datetime] = None
    notes: Optional[str] = None


class ExperimentProgress(BaseModel):
    """实验进度模型"""
    experiment_id: str
    current_phase: ExperimentPhase
    current_status: ExperimentStatus
    progress_percentage: float = Field(ge=0, le=100)
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    current_step: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0


class ExperimentControl(BaseModel):
    """实验控制模型"""
    experiment_id: str
    control_action: str  # "start", "pause", "resume", "stop", "cancel"
    user_id: str
    reason: Optional[str] = None
    force: bool = False  # 强制执行


class ExperimentResult(BaseModel):
    """实验结果模型"""
    experiment_id: str
    final_status: ExperimentStatus
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_data_points: int
    detected_peaks: int
    success_rate: float = Field(ge=0, le=1)
    error_messages: List[str] = []
    result_summary: Dict[str, Any] = {}


class ExperimentQueue(BaseModel):
    """实验队列模型"""
    queue_id: str
    experiments: List[ExperimentConfig]
    current_experiment_index: int = 0
    queue_status: str  # "idle", "running", "paused", "completed"
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_total_time: Optional[float] = None