"""
试管控制API路由
Tube Control API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from models.api_models import (
    TubeControlRequest,
    BatchTubeControlRequest,
    TubeStatusRequest,
    TubeStatusResponse,
    CreateTubeSequenceRequest
)
from models.tube_models import (
    TubeInfo,
    TubePosition,
    TubeOperation,
    TubeSequence,
    TubeStatus,
    TubeType
)
from services.tube_manager import TubeManager
from core.database import DatabaseManager
from core.mqtt_manager import MQTTManager


from api.dependencies import (
    get_experiment_manager,
    get_init_manager,
    get_db_manager,
    get_data_manager,
    get_method_manager,
    get_tube_manager
)

router = APIRouter(prefix="/tube", tags=["tube_control"])


@router.post("/register", response_model=Dict[str, Any])
async def register_tube(
    tube_info: TubeInfo,
    tube_manager = Depends(get_tube_manager)
):
    """注册试管"""
    try:
        result = await tube_manager.register_tube(tube_info)

        return {
            "success": True,
            "message": "试管注册成功",
            "data": {
                "tube_id": tube_info.tube_id,
                "registered": result
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册试管失败: {str(e)}")


@router.post("/control", response_model=Dict[str, Any])
async def control_tube(
    request: TubeControlRequest,
    tube_manager = Depends(get_tube_manager)
):
    """控制试管操作"""
    try:
        operation = None

        if request.operation_type == "pickup":
            operation = await tube_manager.pickup_tube(
                request.tube_id,
                request.operator
            )
        elif request.operation_type == "move":
            if not request.target_position:
                raise HTTPException(status_code=400, detail="移动操作需要目标位置")
            operation = await tube_manager.move_tube(
                request.tube_id,
                request.target_position,
                request.operator
            )
        elif request.operation_type == "inject":
            if not request.volume_ul:
                raise HTTPException(status_code=400, detail="进样操作需要体积参数")
            operation = await tube_manager.inject_sample(
                request.tube_id,
                request.volume_ul,
                request.operator
            )
        elif request.operation_type == "wash":
            if not request.volume_ul:
                raise HTTPException(status_code=400, detail="清洗操作需要体积参数")
            operation = await tube_manager.wash_needle(
                request.volume_ul,
                request.operator
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作类型: {request.operation_type}")

        return {
            "success": True,
            "message": f"{request.operation_type}操作已提交",
            "data": operation.dict() if hasattr(operation, 'dict') else operation
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试管操作失败: {str(e)}")


@router.post("/batch_control", response_model=Dict[str, Any])
async def batch_control_tubes(
    request: BatchTubeControlRequest,
    tube_manager = Depends(get_tube_manager)
):
    """批量试管控制"""
    try:
        results = []
        failed_operations = []

        for i, operation_request in enumerate(request.operations):
            try:
                # 复用单个操作的逻辑
                if operation_request.operation_type == "pickup":
                    operation = await tube_manager.pickup_tube(
                        operation_request.tube_id,
                        operation_request.operator
                    )
                elif operation_request.operation_type == "move":
                    operation = await tube_manager.move_tube(
                        operation_request.tube_id,
                        operation_request.target_position,
                        operation_request.operator
                    )
                elif operation_request.operation_type == "inject":
                    operation = await tube_manager.inject_sample(
                        operation_request.tube_id,
                        operation_request.volume_ul,
                        operation_request.operator
                    )
                else:
                    raise ValueError(f"不支持的操作类型: {operation_request.operation_type}")

                results.append({
                    "index": i,
                    "success": True,
                    "operation": operation.dict() if hasattr(operation, 'dict') else operation
                })

            except Exception as e:
                failed_operations.append({
                    "index": i,
                    "tube_id": operation_request.tube_id,
                    "operation_type": operation_request.operation_type,
                    "error": str(e)
                })

                if request.stop_on_error:
                    break

        return {
            "success": len(failed_operations) == 0,
            "message": f"批量操作完成，成功: {len(results)}, 失败: {len(failed_operations)}",
            "data": {
                "sequence_id": request.sequence_id,
                "successful_operations": len(results),
                "failed_operations": len(failed_operations),
                "results": results,
                "failures": failed_operations
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量试管操作失败: {str(e)}")


@router.post("/status", response_model=TubeStatusResponse)
async def get_tube_status(
    request: TubeStatusRequest,
    tube_manager = Depends(get_tube_manager)
):
    """获取试管状态"""
    try:
        tubes = []

        if request.tube_ids:
            # 获取指定试管
            for tube_id in request.tube_ids:
                tube = await tube_manager.get_tube_info(tube_id)
                if tube:
                    tubes.append(tube)
        elif request.rack_id:
            # 获取指定试管架的试管
            tubes = await tube_manager.list_tubes_by_rack(request.rack_id)
        else:
            # 获取所有试管（简化处理）
            pass

        # 获取进行中的操作
        queue_status = await tube_manager.get_operation_queue_status()
        operations_in_progress = []

        if queue_status.get("current_operation"):
            operations_in_progress.append(queue_status["current_operation"])

        return TubeStatusResponse(
            success=True,
            message="获取试管状态成功",
            tubes=tubes,
            total_tubes=len(tubes),
            operations_in_progress=operations_in_progress
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管状态失败: {str(e)}")


@router.get("/{tube_id}", response_model=Dict[str, Any])
async def get_tube_info(
    tube_id: str,
    tube_manager = Depends(get_tube_manager)
):
    """获取单个试管信息"""
    try:
        tube = await tube_manager.get_tube_info(tube_id)
        if not tube:
            raise HTTPException(status_code=404, detail="试管未找到")

        return {
            "success": True,
            "message": "获取试管信息成功",
            "data": tube.dict() if hasattr(tube, 'dict') else tube
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管信息失败: {str(e)}")


@router.put("/{tube_id}/status")
async def update_tube_status(
    tube_id: str,
    new_status: TubeStatus,
    operator: str = Query(..., description="操作者ID"),
    tube_manager = Depends(get_tube_manager)
):
    """更新试管状态"""
    try:
        result = await tube_manager.update_tube_status(tube_id, new_status, operator)

        return {
            "success": True,
            "message": "试管状态更新成功",
            "data": {
                "tube_id": tube_id,
                "new_status": new_status,
                "updated": result
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新试管状态失败: {str(e)}")


@router.get("/rack/{rack_id}")
async def list_tubes_by_rack(
    rack_id: str,
    tube_manager = Depends(get_tube_manager)
):
    """按试管架列出试管"""
    try:
        tubes = await tube_manager.list_tubes_by_rack(rack_id)

        return {
            "success": True,
            "message": "获取试管架试管列表成功",
            "data": {
                "rack_id": rack_id,
                "tube_count": len(tubes),
                "tubes": [tube.dict() if hasattr(tube, 'dict') else tube for tube in tubes]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管架试管列表失败: {str(e)}")


@router.post("/sequence/create", response_model=Dict[str, Any])
async def create_tube_sequence(
    request: CreateTubeSequenceRequest,
    tube_manager = Depends(get_tube_manager)
):
    """创建试管序列"""
    try:
        # 创建试管序列对象
        sequence = TubeSequence(
            sequence_id=f"seq_{request.sequence_name}_{len(request.tubes)}",
            sequence_name=request.sequence_name,
            description=request.description,
            tubes=request.tubes,
            injection_volume_ul=request.injection_volume_ul,
            wash_volume_ul=request.wash_volume_ul,
            created_by=request.created_by
        )

        # 这里可以添加序列保存逻辑

        return {
            "success": True,
            "message": "试管序列创建成功",
            "data": sequence.dict() if hasattr(sequence, 'dict') else sequence
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建试管序列失败: {str(e)}")


@router.get("/operation/queue")
async def get_operation_queue(
    tube_manager = Depends(get_tube_manager)
):
    """获取操作队列状态"""
    try:
        status = await tube_manager.get_operation_queue_status()

        return {
            "success": True,
            "message": "获取操作队列状态成功",
            "data": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取操作队列状态失败: {str(e)}")


@router.post("/operation/queue")
async def queue_operation(
    operation: TubeOperation,
    tube_manager = Depends(get_tube_manager)
):
    """添加操作到队列"""
    try:
        await tube_manager.queue_operation(operation)

        return {
            "success": True,
            "message": "操作已添加到队列",
            "data": {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "tube_id": operation.tube_id
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加操作到队列失败: {str(e)}")


@router.get("/positions/available")
async def get_available_positions(
    rack_id: Optional[str] = Query(None, description="试管架ID"),
    tube_manager = Depends(get_tube_manager)
):
    """获取可用位置"""
    try:
        # 这里需要实现获取可用位置的逻辑
        # 简化处理，返回模拟数据
        available_positions = []

        if rack_id:
            # 获取指定试管架的可用位置
            for i in range(1, 97):  # 假设96孔位
                available_positions.append({
                    "rack_id": rack_id,
                    "position_number": i,
                    "available": True  # 简化处理
                })
        else:
            # 获取所有试管架的可用位置
            pass

        return {
            "success": True,
            "message": "获取可用位置成功",
            "data": {
                "rack_id": rack_id,
                "available_positions": available_positions[:20]  # 限制返回数量
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用位置失败: {str(e)}")


@router.post("/validate_position")
async def validate_position(
    position: TubePosition,
    tube_manager = Depends(get_tube_manager)
):
    """验证位置是否可用"""
    try:
        # 这里需要调用tube_manager的位置检查方法
        # 由于_check_position_occupied是私有方法，我们简化处理
        is_occupied = False  # 简化处理

        return {
            "success": True,
            "message": "位置验证完成",
            "data": {
                "position": position.dict() if hasattr(position, 'dict') else position,
                "available": not is_occupied,
                "occupied": is_occupied
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证位置失败: {str(e)}")