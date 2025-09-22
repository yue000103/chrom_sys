"""
试管控制API
Tube Control API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging

from models.tube_control_models import (
    TubeSwitchRequest,
    TubeSwitchResponse,
    TubeCalculationResponse,
    DirectTubeSwitchRequest
)
from services.tube_manager import TubeManager, TubeCollectionManager
from data.database_utils import ChromatographyDB

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== 依赖注入 =====

def get_database() -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB()

def get_tube_collection_manager() -> TubeCollectionManager:
    """
    获取试管收集管理器实例
    使用默认参数：流速1.0ml/min，收集体积2.0ml
    """
    return TubeCollectionManager(flow_rate_ml_min=1.0, collection_volume_ml=2.0)

# ===== 试管控制API =====



@router.post("/switch", response_model=TubeSwitchResponse)
async def switch_tube(
    request: TubeSwitchRequest,
    collection_manager: TubeCollectionManager = Depends(get_tube_collection_manager)
):
    """
    切换试管
    根据试管ID自动计算模块号和试管号，然后执行试管切换
    """
    try:
        tube_id = request.tube_id



        # 记录开始时间
        start_time = datetime.now()

        # 使用TubeCollectionManager执行试管切换
        success = await collection_manager.switch_to_tube(tube_id)

        # 计算执行时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        if success:
            logger.info(f"试管切换成功: {tube_id}, 耗时: {execution_time:.3f}秒")
        else:
            logger.error(f"试管切换失败: {tube_id}")

        return TubeSwitchResponse(
            success=success,
            message=f"试管切换{'成功' if success else '失败'}",
            tube_id=tube_id,
            total_steps=1,  # 简化：一步操作
            success_steps=1 if success else 0,
            execution_time=execution_time,
            step_results=[{
                "step": 1,
                "action": f"switch_to_tube_{tube_id}",
                "success": success,
                "execution_time": execution_time,
            }]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试管切换异常: {e}")
        raise HTTPException(status_code=500, detail=f"试管切换失败: {str(e)}")




@router.get("/collection/status")
async def get_collection_status(
    collection_manager: TubeCollectionManager = Depends(get_tube_collection_manager)
):
    """获取试管收集状态信息"""
    try:
        status_info = collection_manager.get_status_info()

        return {
            "success": True,
            "message": "获取收集状态成功",
            "collection_status": status_info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收集状态失败: {str(e)}")


@router.get("/collection/progress")
async def get_collection_progress(
    current_tube_id: int,
    tube_start_time: float,
    current_time: float,
    collection_manager: TubeCollectionManager = Depends(get_tube_collection_manager)
):
    """
    获取试管收集进度

    Args:
        current_tube_id: 当前试管ID
        tube_start_time: 当前试管开始时间(相对于实验开始的秒数)
        current_time: 当前时间(相对于实验开始的秒数)
    """
    try:
        # 检查当前试管是否收集完成
        is_complete = collection_manager.is_collection_complete(tube_start_time, current_time)

        # 获取收集进度
        progress = collection_manager.get_collection_progress(current_time, tube_start_time)

        # 估算剩余时间
        remaining_time = collection_manager.estimate_remaining_time(
            current_tube_id, tube_start_time, current_time
        )

        return {
            "success": True,
            "message": "获取收集进度成功",
            "current_tube_id": current_tube_id,
            "is_collection_complete": is_complete,
            "progress_percent": progress,
            "remaining_time_sec": remaining_time,
            "collection_time_per_tube_sec": collection_manager.get_collection_time_per_tube(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收集进度失败: {str(e)}")


@router.post("/collection/validate")
async def validate_collection_parameters(
    flow_rate: float,
    collection_volume: float
):
    """验证试管收集参数"""
    try:
        is_valid = TubeCollectionManager.validate_tube_parameters(flow_rate, collection_volume)

        if is_valid:
            # 计算收集时间
            collection_time = (collection_volume / flow_rate) * 60
            total_time = collection_time * 40  # 40个试管

            return {
                "success": True,
                "message": "参数验证成功",
                "parameters": {
                    "flow_rate_ml_min": flow_rate,
                    "collection_volume_ml": collection_volume,
                    "collection_time_per_tube_sec": collection_time,
                    "total_collection_time_sec": total_time,
                    "total_collection_time_min": total_time / 60
                },
                "valid": True
            }
        else:
            return {
                "success": False,
                "message": "参数验证失败",
                "parameters": {
                    "flow_rate_ml_min": flow_rate,
                    "collection_volume_ml": collection_volume
                },
                "valid": False,
                "error": "流速和收集体积必须大于0"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数验证失败: {str(e)}")


# ===== 工具接口 =====


@router.get("/status/{tube_id}")
async def get_tube_status(
    tube_id: int,
    collection_manager: TubeCollectionManager = Depends(get_tube_collection_manager)
):
    """获取试管状态信息"""
    try:
        # 验证tube_id
        if not collection_manager._validate_tube_id(tube_id):
            raise HTTPException(status_code=400, detail=f"试管ID无效: {tube_id} (有效范围: 1-40)")


        return {
            "success": True,
            "message": f"试管状态查询成功: {tube_id}",
            "tube_id": tube_id,

            "valid": True,
            "collection_manager_info": collection_manager.get_status_info(),
            "can_switch": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管状态失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "message": "试管控制API运行正常",
        "timestamp": datetime.now().isoformat()
    }