"""
API层统一入口
API Layer Main Entry
"""

from fastapi import APIRouter

# 导入各个API模块的路由
from .function_control import router as function_control_router
from .method_control import router as method_control_router
from .tube_control import router as tube_control_router
from .experiment_data import router as experiment_data_router

# 创建主路由器
main_router = APIRouter(prefix="/api/v1")

# 注册各个模块的路由
main_router.include_router(function_control_router, tags=["功能控制"])
main_router.include_router(method_control_router, tags=["方法控制"])
main_router.include_router(tube_control_router, tags=["试管控制"])
main_router.include_router(experiment_data_router, tags=["实验数据"])

# 导出主路由器和各个子路由器
__all__ = [
    "main_router",
    "function_control_router",
    "method_control_router",
    "tube_control_router",
    "experiment_data_router"
]