"""
方法控制API参数验证器
Method Control API Validators
"""

# 从Models层导入验证模型
from models.api_models import (
    CreateMethodRequest,
    UpdateMethodRequest,
    MethodListRequest,
    MethodListResponse,
    ValidateMethodRequest,
    ValidateMethodResponse
)

from models.method_models import (
    AnalysisMethod,
    MethodValidation,
    MethodTemplate,
    MethodHistory,
    MethodType,
    MethodStatus
)

from models.gradient_models import (
    GradientProgram,
    GradientStep,
    GradientCurve,
    GradientExecution,
    GradientProfile,
    FlowControlType
)

from models.tube_models import (
    TubeSequence,
    TubeInfo,
    TubePosition,
    TubeRack,
    TubeBatch,
    TubeStatus,
    TubeType
)

# 导出所有验证模型供路由使用
__all__ = [
    "CreateMethodRequest",
    "UpdateMethodRequest",
    "MethodListRequest",
    "MethodListResponse",
    "ValidateMethodRequest",
    "ValidateMethodResponse",
    "AnalysisMethod",
    "MethodValidation",
    "MethodTemplate",
    "MethodHistory",
    "MethodType",
    "MethodStatus",
    "GradientProgram",
    "GradientStep",
    "GradientCurve",
    "GradientExecution",
    "GradientProfile",
    "FlowControlType",
    "TubeSequence",
    "TubeInfo",
    "TubePosition",
    "TubeRack",
    "TubeBatch",
    "TubeStatus",
    "TubeType"
]

# 由于数据验证已经统一到Models层，这个文件主要作为模型的重新导出
# 实际的参数验证由FastAPI和Pydantic自动处理