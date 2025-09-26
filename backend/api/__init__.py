"""
API层统一入口
API Layer Main Entry
"""

from fastapi import APIRouter

# 导入各个API模块的路由
from .function_control import router as function_control_router
from .method_control import router as method_control_router
from .tube_control import router as tube_control_router
from .experiment_control import router as experiment_data_router
from .rack_info import router as rack_info_router
from .experiment_management import router as experiment_management_router
from .valve_path import router as valve_path_router
from .column_management import router as column_management_router
from .smiles_management import router as smiles_management_router

# 创建主路由器
main_router = APIRouter(prefix="/api")

# 注册各个模块的路由
main_router.include_router(function_control_router, tags=["功能控制"])
main_router.include_router(method_control_router, prefix="/methods", tags=["方法控制"])
main_router.include_router(tube_control_router, prefix="/tubes", tags=["试管控制"])
main_router.include_router(experiment_data_router, prefix="/experiments", tags=["实验11管理"])
main_router.include_router(rack_info_router, prefix="/racks", tags=["试管架管理"])
main_router.include_router(experiment_management_router, prefix="/experiment_mgmt", tags=["实验数据管理"])
main_router.include_router(valve_path_router, prefix="/valve-paths", tags=["阀门路径管理"])
main_router.include_router(column_management_router, prefix="/columns", tags=["色谱柱管理"])
main_router.include_router(smiles_management_router, prefix="/smiles", tags=["SMILES分子管理"])

# 导出主路由器和各个子路由器
__all__ = [
    "main_router",
    "function_control_router",
    "method_control_router",
    "tube_control_router",
    "experiment_data_router",
    "rack_info_router",
    "experiment_management_router",
    "valve_path_router",
    "column_management_router",
    "smiles_management_router"
]