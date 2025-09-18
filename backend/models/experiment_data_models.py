"""
实验数据模型
Experiment data models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DataType(str, Enum):
    """数据类型枚举"""
    PRESSURE = "pressure"
    DETECTOR = "detector"
    BUBBLE = "bubble"
    FLOW = "flow"
    TEMPERATURE = "temperature"
    UV = "uv"
    FLUORESCENCE = "fluorescence"


class DataQuality(str, Enum):
    """数据质量枚举"""
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"


class SensorDataPoint(BaseModel):
    """传感器数据点"""
    data_id: str
    device_id: str
    experiment_id: str
    timestamp: datetime
    value: float
    unit: str
    data_type: DataType
    quality: DataQuality = DataQuality.GOOD
    raw_value: Optional[float] = None
    calibration_factor: float = 1.0
    notes: Optional[str] = None


class PeakType(str, Enum):
    """峰类型枚举"""
    UNKNOWN = "unknown"
    ANALYTE = "analyte"
    IMPURITY = "impurity"
    SOLVENT = "solvent"
    ARTIFACT = "artifact"


class PeakInfo(BaseModel):
    """峰信息模型"""
    peak_id: str
    experiment_id: str
    peak_number: int
    retention_time: float = Field(gt=0, description="保留时间(分钟)")
    area: float = Field(ge=0, description="峰面积")
    height: float = Field(ge=0, description="峰高")
    width_at_half_height: float = Field(gt=0, description="半峰宽")
    asymmetry_factor: Optional[float] = Field(None, gt=0, description="不对称因子")
    theoretical_plates: Optional[int] = Field(None, gt=0, description="理论塔板数")
    peak_type: PeakType = PeakType.UNKNOWN
    compound_name: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1, description="识别置信度")
    integration_method: str = "automatic"
    baseline_start: Optional[float] = None
    baseline_end: Optional[float] = None
    signal_to_noise: Optional[float] = None


class ChromatogramMetadata(BaseModel):
    """色谱图元数据"""
    sampling_rate_hz: float = Field(gt=0, description="采样频率")
    data_points_count: int = Field(ge=0, description="数据点数量")
    acquisition_time_minutes: float = Field(gt=0, description="采集时间")
    detector_wavelength_nm: Optional[float] = None
    detector_bandwidth_nm: Optional[float] = None
    temperature_celsius: Optional[float] = None
    pressure_bar: Optional[float] = None
    flow_rate_ml_min: Optional[float] = None


class ChromatogramData(BaseModel):
    """色谱图数据"""
    chromatogram_id: str
    experiment_id: str
    sample_id: str
    method_id: str
    data_points: List[SensorDataPoint]
    peaks: List[PeakInfo] = []
    metadata: ChromatogramMetadata
    baseline_corrected: bool = False
    noise_filtered: bool = False
    peak_integration_complete: bool = False
    analysis_software: str = "ChromatographySystem"
    analysis_version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None


class DataProcessingStep(BaseModel):
    """数据处理步骤"""
    step_id: str
    step_name: str
    step_type: str  # "baseline_correction", "noise_filtering", "peak_detection"
    parameters: Dict[str, Any]
    applied_at: datetime = Field(default_factory=datetime.now)
    applied_by: str
    processing_time_seconds: float
    success: bool = True
    error_message: Optional[str] = None


class ExperimentDataSummary(BaseModel):
    """实验数据汇总"""
    experiment_id: str
    total_data_points: int = Field(ge=0)
    total_peaks: int = Field(ge=0)
    data_size_mb: float = Field(ge=0, description="数据大小(MB)")
    acquisition_duration_minutes: float = Field(ge=0)
    processing_steps: List[DataProcessingStep] = []
    analysis_complete: bool = False
    data_quality_score: float = Field(default=0.0, ge=0, le=100)
    major_peaks_count: int = Field(default=0, ge=0)
    minor_peaks_count: int = Field(default=0, ge=0)
    identified_compounds: int = Field(default=0, ge=0)
    last_updated: datetime = Field(default_factory=datetime.now)


class DataExportFormat(str, Enum):
    """数据导出格式枚举"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    PDF_REPORT = "pdf_report"


class DataExportRequest(BaseModel):
    """数据导出请求"""
    export_id: str
    experiment_id: str
    export_format: DataExportFormat
    include_raw_data: bool = True
    include_processed_data: bool = True
    include_peaks: bool = True
    include_metadata: bool = True
    include_plots: bool = False
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.now)


class DataBackup(BaseModel):
    """数据备份记录"""
    backup_id: str
    experiment_ids: List[str]
    backup_type: str  # "manual", "automatic", "scheduled"
    backup_path: str
    backup_size_mb: float
    compression_ratio: float = 1.0
    backup_status: str = "completed"  # "pending", "running", "completed", "failed"
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    checksum: Optional[str] = None

class DataQualityMetrics(BaseModel):
    """数据质量指标"""
    experiment_id: str
    signal_to_noise_ratio: Optional[float] = None
    baseline_drift: Optional[float] = None
    peak_symmetry: Optional[float] = None
    retention_time_reproducibility: Optional[float] = None
    detector_linearity: Optional[float] = None
    data_completeness_percentage: float = Field(default=100.0, ge=0, le=100)
    last_evaluated: datetime = Field(default_factory=datetime.now)
    evaluator: Optional[str] = None
    comments: Optional[str] = None

class ProcessingParameters(BaseModel):
    """数据处理参数"""
    baseline_correction_method: str = "automatic"  # "automatic", "manual", "none"
    noise_filtering_method: str = "moving_average"  # "moving_average", "gaussian", "none"
    peak_detection_algorithm: str = "threshold"  # "threshold", "derivative", "wavelet"
    peak_detection_threshold: float = Field(default=0.01, gt=0)
    min_peak_width: float = Field(default=0.1, gt=0)
    max_peak_width: float = Field(default=10.0, gt=0)
    smoothing_window_size: int = Field(default=5, ge=1)
    calibration_curve: Optional[Dict[str, float]] = None  # e.g., {"slope": 1.0, "intercept": 0.0}
    user_notes: Optional[str] = None

class BaselineInfo(BaseModel):
    """基线信息"""
    experiment_id: str
    initial_baseline: Optional[float] = None
    final_baseline: Optional[float] = None
    baseline_drift: Optional[float] = None
    drift_rate_per_minute: Optional[float] = None
    baseline_stability: bool = False
    evaluated_at: datetime = Field(default_factory=datetime.now)
    evaluator: Optional[str] = None
    comments: Optional[str] = None
