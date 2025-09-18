"""
API请求/响应模型
API request/response models - 统一数据校验
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base_models import BaseResponse
from .gradient_models import GradientProgram
from .tube_models import TubeSequence, TubePosition, TubeInfo, TubeOperation
from .experiment_data_models import SensorDataPoint, PeakInfo, ExperimentDataSummary, DataExportFormat
from .method_models import AnalysisMethod
from .base_models import DeviceStatus


# === 功能控制API模型 ===
class FunctionControlRequest(BaseModel):
    """功能控制请求模型"""
    function_type: str  # "start_experiment", "stop_experiment", "pause_experiment", "resume_experiment"
    experiment_id: Optional[str] = None
    parameters: Dict[str, Any] = {}
    user_id: str
    reason: Optional[str] = None
    force: bool = False


class FunctionControlResponse(BaseResponse):
    """功能控制响应模型"""
    function_type: str
    experiment_id: Optional[str] = None
    result: Dict[str, Any] = {}
    execution_time_seconds: Optional[float] = None


class SystemStatusRequest(BaseModel):
    """系统状态查询请求"""
    include_devices: bool = True
    include_experiments: bool = True
    include_resources: bool = False


class SystemStatusResponse(BaseResponse):
    """系统状态响应"""
    total_devices: int
    active_devices: int
    inactive_devices: int
    error_devices: int
    current_experiments: int
    queued_experiments: int
    system_uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_percent: float


# === 方法控制API模型 ===
class CreateMethodRequest(BaseModel):
    """创建方法请求"""
    method_name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=1000)
    gradient_program: GradientProgram
    tube_sequence: TubeSequence
    detection_parameters: Dict[str, Any]
    column_parameters: Dict[str, Any] = {}
    created_by: str


class UpdateMethodRequest(BaseModel):
    """更新方法请求"""
    method_id: str
    method_name: Optional[str] = None
    description: Optional[str] = None
    gradient_program: Optional[GradientProgram] = None
    tube_sequence: Optional[TubeSequence] = None
    detection_parameters: Optional[Dict[str, Any]] = None
    column_parameters: Optional[Dict[str, Any]] = None
    modified_by: str


class MethodListRequest(BaseModel):
    """方法列表查询请求"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search_term: Optional[str] = None
    method_type: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class MethodListResponse(BaseResponse):
    """方法列表响应"""
    methods: List[AnalysisMethod]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ValidateMethodRequest(BaseModel):
    """方法验证请求"""
    method_id: str
    validation_type: str = "basic"  # "basic", "full", "compliance"
    validation_parameters: Dict[str, Any] = {}


class ValidateMethodResponse(BaseResponse):
    """方法验证响应"""
    method_id: str
    validation_status: str  # "valid", "invalid", "warning"
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    estimated_run_time: Optional[float] = None


# === 试管控制API模型 ===
class TubeControlRequest(BaseModel):
    """试管控制请求"""
    operation_type: str  # "pickup", "inject", "wash", "replace", "move"
    tube_id: str
    source_position: Optional[TubePosition] = None
    target_position: Optional[TubePosition] = None
    volume_ul: Optional[float] = Field(None, gt=0)
    speed: Optional[float] = Field(None, gt=0, le=100)
    parameters: Dict[str, Any] = {}
    operator: str


class BatchTubeControlRequest(BaseModel):
    """批量试管控制请求"""
    operations: List[TubeControlRequest]
    sequence_id: str
    execute_sequentially: bool = True
    stop_on_error: bool = True
    estimated_duration_minutes: Optional[float] = None


class TubeStatusRequest(BaseModel):
    """试管状态查询请求"""
    tube_ids: Optional[List[str]] = None
    rack_id: Optional[str] = None
    position_range: Optional[Dict[str, int]] = None
    include_history: bool = False


class TubeStatusResponse(BaseResponse):
    """试管状态响应"""
    tubes: List[TubeInfo]
    total_tubes: int
    operations_in_progress: List[TubeOperation] = []


class CreateTubeSequenceRequest(BaseModel):
    """创建试管序列请求"""
    sequence_name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    tubes: List[TubeInfo]
    injection_volume_ul: float = Field(default=10.0, gt=0)
    wash_volume_ul: float = Field(default=50.0, gt=0)
    created_by: str


# === 实验数据API模型 ===
class DataQueryRequest(BaseModel):
    """数据查询请求"""
    experiment_id: Optional[str] = None
    device_id: Optional[str] = None
    data_type: Optional[str] = None  # "pressure", "detector", "bubble", "flow"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)
    include_raw_data: bool = False
    include_processed_data: bool = True
    quality_filter: Optional[str] = None  # "good", "acceptable", "all"


class DataExportRequest(BaseModel):
    """数据导出请求"""
    experiment_id: str
    export_format: DataExportFormat
    include_peaks: bool = True
    include_raw_data: bool = True
    include_metadata: bool = True
    include_plots: bool = False
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    compression: bool = False
    requested_by: str


class ExperimentDataResponse(BaseResponse):
    """实验数据响应"""
    experiment_id: str
    data_points: List[SensorDataPoint] = []
    peaks: List[PeakInfo] = []
    summary: ExperimentDataSummary
    data_quality_score: float = Field(ge=0, le=100)


class PeakDetectionRequest(BaseModel):
    """峰检测请求"""
    experiment_id: str
    detection_parameters: Dict[str, Any] = {}
    threshold: float = Field(default=0.01, gt=0)
    min_peak_width: float = Field(default=0.1, gt=0)
    max_peak_width: float = Field(default=10.0, gt=0)
    baseline_correction: bool = True
    noise_filtering: bool = True


class PeakDetectionResponse(BaseResponse):
    """峰检测响应"""
    experiment_id: str
    detected_peaks: List[PeakInfo]
    detection_summary: Dict[str, Any] = {}
    processing_time_seconds: float


class DataProcessingRequest(BaseModel):
    """数据处理请求"""
    experiment_id: str
    processing_steps: List[str]  # "baseline_correction", "noise_filtering", "peak_detection"
    parameters: Dict[str, Any] = {}
    overwrite_existing: bool = False


class DataProcessingResponse(BaseResponse):
    """数据处理响应"""
    experiment_id: str
    processing_results: Dict[str, Any]
    processing_time_seconds: float
    data_quality_improvement: Optional[float] = None


# === 通用响应模型 ===
class DeviceStatusResponse(BaseResponse):
    """设备状态响应"""
    device_id: str
    device_name: str
    device_status: DeviceStatus
    last_update: datetime
    uptime_seconds: Optional[float] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = {}


class PaginatedResponse(BaseResponse):
    """分页响应基础模型"""
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
    total_items: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class FileDownloadResponse(BaseResponse):
    """文件下载响应"""
    file_id: str
    file_name: str
    file_size_bytes: int
    download_url: str
    expires_at: datetime
    content_type: str


class BatchOperationResponse(BaseResponse):
    """批量操作响应"""
    total_operations: int
    successful_operations: int
    failed_operations: int
    operation_results: List[Dict[str, Any]] = []
    partial_success: bool = False