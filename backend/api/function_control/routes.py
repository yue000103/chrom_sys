"""
功能控制API路由
Function Control API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime

import sys
from pathlib import Path

# 确保项目根目录在Python路径中
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.api_models import (
    FunctionControlRequest,
    FunctionControlResponse,
    SystemStatusRequest,
    SystemStatusResponse
)
from api.dependencies import (
    get_experiment_manager,
    get_init_manager,
    get_db_manager
)

router = APIRouter(prefix="/function", tags=["function_control"])


@router.post("/start_experiment", response_model=FunctionControlResponse)
async def start_experiment(
    request: FunctionControlRequest,
    experiment_manager = Depends(get_experiment_manager),
    db_manager = Depends(get_db_manager)
):
    """启动实验"""
    try:
        if request.function_type != "start_experiment":
            raise HTTPException(status_code=400, detail="功能类型错误")

        experiment_config = request.parameters.get("experiment_config")
        if not experiment_config:
            raise HTTPException(status_code=400, detail="缺少实验配置")

        # 启动实验
        result = await experiment_manager.start_experiment(experiment_config)

        return FunctionControlResponse(
            success=True,
            message="实验启动成功",
            function_type=request.function_type,
            experiment_id=experiment_config.get("experiment_id"),
            result=result.dict() if hasattr(result, 'dict') else result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动实验失败: {str(e)}")


@router.post("/stop_experiment", response_model=FunctionControlResponse)
async def stop_experiment(
    request: FunctionControlRequest,
    experiment_manager = Depends(get_experiment_manager)
):
    """停止实验"""
    try:
        if request.function_type != "stop_experiment":
            raise HTTPException(status_code=400, detail="功能类型错误")

        if not request.experiment_id:
            raise HTTPException(status_code=400, detail="缺少实验ID")

        # 停止实验
        result = await experiment_manager.stop_experiment(
            request.experiment_id,
            request.user_id,
            request.reason
        )

        return FunctionControlResponse(
            success=True,
            message="实验停止成功",
            function_type=request.function_type,
            experiment_id=request.experiment_id,
            result=result.dict() if hasattr(result, 'dict') else result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止实验失败: {str(e)}")


@router.post("/pause_experiment", response_model=FunctionControlResponse)
async def pause_experiment(
    request: FunctionControlRequest,
    experiment_manager = Depends(get_experiment_manager)
):
    """暂停实验"""
    try:
        if request.function_type != "pause_experiment":
            raise HTTPException(status_code=400, detail="功能类型错误")

        if not request.experiment_id:
            raise HTTPException(status_code=400, detail="缺少实验ID")

        # 暂停实验
        result = await experiment_manager.pause_experiment(
            request.experiment_id,
            request.user_id,
            request.reason
        )

        return FunctionControlResponse(
            success=True,
            message="实验暂停成功",
            function_type=request.function_type,
            experiment_id=request.experiment_id,
            result={"paused": result}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停实验失败: {str(e)}")


@router.post("/resume_experiment", response_model=FunctionControlResponse)
async def resume_experiment(
    request: FunctionControlRequest,
    experiment_manager = Depends(get_experiment_manager)
):
    """恢复实验"""
    try:
        if request.function_type != "resume_experiment":
            raise HTTPException(status_code=400, detail="功能类型错误")

        if not request.experiment_id:
            raise HTTPException(status_code=400, detail="缺少实验ID")

        # 恢复实验
        result = await experiment_manager.resume_experiment(
            request.experiment_id,
            request.user_id
        )

        return FunctionControlResponse(
            success=True,
            message="实验恢复成功",
            function_type=request.function_type,
            experiment_id=request.experiment_id,
            result={"resumed": result}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复实验失败: {str(e)}")


@router.get("/experiment_progress/{experiment_id}")
async def get_experiment_progress(
    experiment_id: str,
    experiment_manager = Depends(get_experiment_manager)
):
    """获取实验进度"""
    try:
        progress = await experiment_manager.get_experiment_progress(experiment_id)
        if not progress:
            raise HTTPException(status_code=404, detail="实验未找到")

        return {
            "success": True,
            "message": "获取进度成功",
            "data": progress.dict() if hasattr(progress, 'dict') else progress
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验进度失败: {str(e)}")


@router.get("/running_experiments")
async def list_running_experiments(
    experiment_manager = Depends(get_experiment_manager)
):
    """列出运行中的实验"""
    try:
        experiments = await experiment_manager.list_running_experiments()

        return {
            "success": True,
            "message": "获取运行实验列表成功",
            "data": [exp.dict() if hasattr(exp, 'dict') else exp for exp in experiments]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运行实验列表失败: {str(e)}")


@router.get("/queue_status")
async def get_queue_status(
    experiment_manager = Depends(get_experiment_manager)
):
    """获取实验队列状态"""
    try:
        status = await experiment_manager.get_queue_status()

        return {
            "success": True,
            "message": "获取队列状态成功",
            "data": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")


@router.post("/add_to_queue")
async def add_experiment_to_queue(
    experiment_config: Dict[str, Any],
    experiment_manager = Depends(get_experiment_manager)
):
    """添加实验到队列"""
    try:
        position = await experiment_manager.add_to_queue(experiment_config)

        return {
            "success": True,
            "message": "实验已添加到队列",
            "data": {"queue_position": position}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加实验到队列失败: {str(e)}")


@router.delete("/queue/{experiment_id}")
async def remove_from_queue(
    experiment_id: str,
    experiment_manager = Depends(get_experiment_manager)
):
    """从队列中移除实验"""
    try:
        result = await experiment_manager.remove_from_queue(experiment_id)

        return {
            "success": True,
            "message": "实验已从队列移除" if result else "实验不在队列中",
            "data": {"removed": result}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"从队列移除实验失败: {str(e)}")


@router.post("/system_status", response_model=SystemStatusResponse)
async def get_system_status(
    request: SystemStatusRequest,
    init_manager = Depends(get_init_manager)
):
    """获取系统状态"""
    try:
        # 获取初始化状态
        init_status = await init_manager.get_initialization_status()

        # 模拟系统资源使用情况
        return SystemStatusResponse(
            success=True,
            message="获取系统状态成功",
            total_devices=init_status.get("device_count", 0),
            active_devices=init_status.get("device_count", 0),
            inactive_devices=0,
            error_devices=0,
            current_experiments=0,  # 需要从实验管理器获取
            queued_experiments=0,   # 需要从实验管理器获取
            system_uptime_seconds=0.0,  # 需要计算系统运行时间
            memory_usage_mb=256.0,      # 模拟数据
            cpu_usage_percent=15.0,     # 模拟数据
            disk_usage_percent=45.0     # 模拟数据
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.post("/system_initialize")
async def initialize_system(
    config: Dict[str, Any],
    init_manager = Depends(get_init_manager)
):
    """初始化系统"""
    try:
        # 这里需要将config转换为SystemInitConfig对象
        result = await init_manager.initialize_system(config)

        return {
            "success": True,
            "message": "系统初始化完成",
            "data": result.dict() if hasattr(result, 'dict') else result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统初始化失败: {str(e)}")


@router.post("/system_shutdown")
async def shutdown_system(
    init_manager = Depends(get_init_manager)
):
    """关闭系统"""
    try:
        await init_manager.shutdown_system()

        return {
            "success": True,
            "message": "系统已关闭"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统关闭失败: {str(e)}")


@router.get("/system_readiness")
async def check_system_readiness(
    init_manager = Depends(get_init_manager)
):
    """检查系统就绪状态"""
    try:
        status = await init_manager.get_initialization_status()

        return {
            "success": True,
            "message": "获取系统就绪状态成功",
            "data": {
                "system_ready": status.get("system_ready", False),
                "components_status": status.get("status", {}),
                "initialized_devices": status.get("initialized_devices", [])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查系统就绪状态失败: {str(e)}")