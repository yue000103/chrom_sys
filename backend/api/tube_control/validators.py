"""
试管控制API参数验证器
Tube Control API Validators
"""

# 从Models层导入验证模型
from models.api_models import (
    TubeControlRequest,
    BatchTubeControlRequest,
    TubeStatusRequest,
    TubeStatusResponse,
    CreateTubeSequenceRequest
)

from models.tube_models import (
    TubeInfo,
    TubeSequence,
    TubeOperation,
    TubePosition,
    TubeRack,
    TubeBatch,
    TubeStatus,
    TubeType
)

# 导出所有验证模型供路由使用
__all__ = [
    "TubeControlRequest",
    "BatchTubeControlRequest",
    "TubeStatusRequest",
    "TubeStatusResponse",
    "CreateTubeSequenceRequest",
    "TubeInfo",
    "TubeSequence",
    "TubeOperation",
    "TubePosition",
    "TubeRack",
    "TubeBatch",
    "TubeStatus",
    "TubeType"
]

# 由于数据验证已经统一到Models层，这个文件主要作为模型的重新导出
# 实际的参数验证由FastAPI和Pydantic自动处理