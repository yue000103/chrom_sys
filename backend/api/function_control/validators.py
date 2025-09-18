"""
功能控制API参数验证器
Function Control API Validators
"""

# 从Models层导入验证模型
from models.api_models import (
    FunctionControlRequest,
    FunctionControlResponse,
    SystemStatusRequest,
    SystemStatusResponse
)

from models.experiment_function_models import (
    ExperimentConfig,
    ExperimentProgress,
    ExperimentControl,
    ExperimentResult,
    ExperimentQueue,
    ExperimentStatus,
    ExperimentPhase
)

from models.initialization_models import (
    SystemInitConfig,
    DeviceConfig,
    DeviceInitResult,
    InitializationResult
)

# 导出所有验证模型供路由使用
__all__ = [
    "FunctionControlRequest",
    "FunctionControlResponse",
    "SystemStatusRequest",
    "SystemStatusResponse",
    "ExperimentConfig",
    "ExperimentProgress",
    "ExperimentControl",
    "ExperimentResult",
    "ExperimentQueue",
    "ExperimentStatus",
    "ExperimentPhase",
    "SystemInitConfig",
    "DeviceConfig",
    "DeviceInitResult",
    "InitializationResult"
]

# 由于数据验证已经统一到Models层，这个文件主要作为模型的重新导出
# 实际的参数验证由FastAPI和Pydantic自动处理