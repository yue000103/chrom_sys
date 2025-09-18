"""
试管管理模型
Tube management models
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TubeStatus(str, Enum):
    """试管状态枚举"""
    EMPTY = "empty"
    FILLED = "filled"
    IN_USE = "in_use"
    PROCESSED = "processed"
    ERROR = "error"


class TubeType(str, Enum):
    """试管类型枚举"""
    SAMPLE = "sample"
    STANDARD = "standard"
    BLANK = "blank"
    QC = "qc"
    CALIBRATION = "calibration"


class RackType(str, Enum):
    """试管架类型枚举"""
    AUTOSAMPLER = "autosampler"
    COLLECTION = "collection"
    STORAGE = "storage"


class TubePosition(BaseModel):
    """试管位置模型"""
    rack_id: str
    rack_type: RackType
    position_number: int = Field(ge=1, description="位置编号")
    row: Optional[str] = None  # A, B, C...
    column: Optional[int] = None  # 1, 2, 3...
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    z_coordinate: Optional[float] = None

    @validator('position_number')
    def validate_position(cls, v, values):
        """验证位置编号的合理性"""
        if v < 1 or v > 384:  # 假设最大384个位置
            raise ValueError('位置编号必须在1-384之间')
        return v


class TubeInfo(BaseModel):
    """试管信息模型"""
    tube_id: str
    sample_id: str
    tube_type: TubeType
    tube_status: TubeStatus
    position: TubePosition
    volume_ul: float = Field(gt=0, description="体积(微升)")
    remaining_volume_ul: Optional[float] = None
    sample_type: str
    concentration: Optional[float] = None
    concentration_unit: Optional[str] = "mg/L"
    preparation_date: datetime
    expiry_date: Optional[datetime] = None
    prepared_by: str
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @validator('remaining_volume_ul')
    def validate_remaining_volume(cls, v, values):
        """验证剩余体积不超过总体积"""
        if v is not None and 'volume_ul' in values:
            if v > values['volume_ul']:
                raise ValueError('剩余体积不能超过总体积')
        return v


class TubeSequence(BaseModel):
    """试管序列模型"""
    sequence_id: str
    sequence_name: str
    description: Optional[str] = None
    tubes: List[TubeInfo]
    current_tube_index: int = 0
    total_tubes: int = Field(ge=0)
    injection_volume_ul: float = Field(gt=0, default=10.0)
    wash_volume_ul: float = Field(gt=0, default=50.0)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_duration_minutes: Optional[float] = None

    @validator('total_tubes')
    def validate_tube_count(cls, v, values):
        """验证试管数量与列表长度一致"""
        if 'tubes' in values and len(values['tubes']) != v:
            raise ValueError('试管数量与试管列表长度不一致')
        return v

    @validator('current_tube_index')
    def validate_current_index(cls, v, values):
        """验证当前试管索引的有效性"""
        if 'total_tubes' in values and v >= values['total_tubes']:
            raise ValueError('当前试管索引超出范围')
        return v


class TubeOperation(BaseModel):
    """试管操作模型"""
    operation_id: str
    tube_id: str
    operation_type: str  # "pickup", "inject", "wash", "replace", "move"
    source_position: Optional[TubePosition] = None
    target_position: Optional[TubePosition] = None
    volume_ul: Optional[float] = None
    speed: Optional[float] = None  # 操作速度
    parameters: Dict[str, Any] = {}
    status: str = "pending"  # "pending", "running", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    operator: str
    timestamp: datetime = Field(default_factory=datetime.now)


class TubeRack(BaseModel):
    """试管架模型"""
    rack_id: str
    rack_name: str
    rack_type: RackType
    total_positions: int = Field(gt=0)
    occupied_positions: int = Field(ge=0)
    rows: int = Field(gt=0)
    columns: int = Field(gt=0)
    position_spacing_mm: float = Field(gt=0)
    description: Optional[str] = None
    location: Optional[str] = None
    barcode: Optional[str] = None
    last_calibrated: Optional[datetime] = None

    @validator('occupied_positions')
    def validate_occupied_positions(cls, v, values):
        """验证占用位置数不超过总位置数"""
        if 'total_positions' in values and v > values['total_positions']:
            raise ValueError('占用位置数不能超过总位置数')
        return v


class TubeBatch(BaseModel):
    """试管批次模型"""
    batch_id: str
    batch_name: str
    tube_sequences: List[TubeSequence]
    total_tubes: int
    processing_order: List[str]  # sequence_id列表
    batch_status: str = "pending"  # "pending", "running", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)