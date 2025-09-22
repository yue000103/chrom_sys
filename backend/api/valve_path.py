"""
试管阀门路径配置API
Tube Valve Path Configuration API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from services.valve_path_manager import ValvePathManager, ValvePathExecutor
from models.valve_path_models import (
    CreateTubePathRequest, UpdateTubePathRequest, TubePathQueryRequest,
    CreateDeviceMappingRequest, UpdateDeviceMappingRequest,
    TubePathResponse, TubePathListResponse, TubePathDetailResponse,
    DeviceMappingResponse, DeviceMappingListResponse,
    PathExecutionResponse, BatchPathExecutionRequest, BatchPathExecutionResponse,
    TubePathSummaryResponse, PathStatisticsResponse, PathStatistics
)

router = APIRouter()

# ===== 依赖注入 =====

def get_valve_path_manager() -> ValvePathManager:
    """获取阀门路径管理器实例"""
    return ValvePathManager()

def get_valve_path_executor(manager: ValvePathManager = Depends(get_valve_path_manager)) -> ValvePathExecutor:
    """获取阀门路径执行器实例"""
    return ValvePathExecutor(manager)

# ===== 试管路径管理API =====

@router.get("/tubes/summary", response_model=TubePathSummaryResponse)
async def get_tube_path_summary(
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """获取试管路径汇总信息"""
    try:
        # 获取统计信息
        stats = manager.get_path_statistics()

        # 获取模块汇总
        all_paths = manager.get_all_tube_paths()
        module_summary = {}

        for path in all_paths:
            module = path['module_number']
            tube = path['tube_number']

            if module not in module_summary:
                module_summary[module] = set()
            module_summary[module].add(tube)

        # 转换为列表格式
        module_list = [
            {
                'module_number': module,
                'tube_count': len(tubes),
                'tube_numbers': sorted(list(tubes))
            }
            for module, tubes in module_summary.items()
        ]

        return TubePathSummaryResponse(
            success=True,
            message="获取试管路径汇总成功",
            total_modules=stats.get('total_modules', 0),
            total_tubes=stats.get('total_tubes', 0),
            total_paths=len(module_summary),
            module_summary=module_list
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管路径汇总失败: {str(e)}")




@router.get("/tubes", response_model=TubePathListResponse)
async def get_tube_paths(
    module_number: Optional[int] = Query(None, description="模块号"),
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """获取试管路径列表"""
    try:
        paths = manager.get_all_tube_paths(module_number=module_number)

        return TubePathListResponse(
            success=True,
            message="获取试管路径列表成功",
            paths=paths,
            total_count=len(paths)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试管路径列表失败: {str(e)}")


@router.post("/tubes/{module_number}/{tube_number}", response_model=TubePathResponse)
async def create_tube_path(
    module_number: int,
    tube_number: int,
    request: CreateTubePathRequest,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """创建试管路径"""
    try:
        # 验证模块号和试管号是否与请求一致
        if (request.module_number != module_number or
            request.tube_number != tube_number):
            raise HTTPException(
                status_code=400,
                detail="URL中的模块号/试管号与请求体不一致"
            )

        success = manager.create_tube_path(
            module_number, tube_number, request.path_steps
        )

        if success:
            return TubePathResponse(
                success=True,
                message=f"试管路径创建成功: 模块{module_number}, 试管{tube_number}"
            )
        else:
            raise HTTPException(status_code=400, detail="试管路径创建失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建试管路径失败: {str(e)}")


@router.put("/tubes/{module_number}/{tube_number}", response_model=TubePathResponse)
async def update_tube_path(
    module_number: int,
    tube_number: int,
    request: UpdateTubePathRequest,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """更新试管路径"""
    try:
        if not request.path_steps:
            raise HTTPException(status_code=400, detail="路径步骤不能为空")

        success = manager.update_tube_path(
            module_number, tube_number, request.path_steps
        )

        if success:
            return TubePathResponse(
                success=True,
                message=f"试管路径更新成功: 模块{module_number}, 试管{tube_number}"
            )
        else:
            raise HTTPException(status_code=400, detail="试管路径更新失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新试管路径失败: {str(e)}")


@router.delete("/tubes/{module_number}/{tube_number}")
async def delete_tube_path(
    module_number: int,
    tube_number: int,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """删除试管路径"""
    try:
        success = manager.delete_tube_path(module_number, tube_number)

        if success:
            return {
                "success": True,
                "message": f"试管路径删除成功: 模块{module_number}, 试管{tube_number}"
            }
        else:
            raise HTTPException(status_code=404, detail="试管路径未找到")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除试管路径失败: {str(e)}")


# ===== 路径执行API =====



@router.post("/tubes/execute/batch", response_model=BatchPathExecutionResponse)
async def execute_multiple_tube_paths(
    request: BatchPathExecutionRequest,
    executor: ValvePathExecutor = Depends(get_valve_path_executor)
):
    """批量执行多个试管路径"""
    try:
        result = await executor.execute_multiple_tube_paths(request.tube_paths)

        return BatchPathExecutionResponse(
            success=result['success'],
            message=result['message'],
            total_paths=result['total_paths'],
            success_paths=result['success_paths'],
            failed_paths=result['failed_paths'],
            execution_results=result['execution_results']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量执行试管路径失败: {str(e)}")


# ===== 设备映射管理API =====

@router.get("/devices", response_model=DeviceMappingListResponse)
async def get_all_device_mappings(
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """获取所有设备映射"""
    try:
        mappings = manager.get_all_device_mappings()

        return DeviceMappingListResponse(
            success=True,
            message="获取设备映射列表成功",
            mappings=mappings,
            total_count=len(mappings)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备映射列表失败: {str(e)}")


@router.get("/devices/{device_code}", response_model=DeviceMappingResponse)
async def get_device_mapping(
    device_code: str,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """获取指定设备映射"""
    try:
        mapping = manager.get_device_mapping(device_code)

        if mapping:
            return DeviceMappingResponse(
                success=True,
                message="获取设备映射成功",
                mapping=mapping
            )
        else:
            raise HTTPException(status_code=404, detail=f"设备映射未找到: {device_code}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备映射失败: {str(e)}")


@router.post("/devices", response_model=DeviceMappingResponse)
async def create_device_mapping(
    request: CreateDeviceMappingRequest,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """创建设备映射"""
    try:
        mapping_data = request.dict(exclude_unset=True)
        success = manager.create_device_mapping(mapping_data)

        if success:
            return DeviceMappingResponse(
                success=True,
                message=f"设备映射创建成功: {request.device_code}"
            )
        else:
            raise HTTPException(status_code=400, detail="设备映射创建失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建设备映射失败: {str(e)}")


@router.put("/devices/{device_code}", response_model=DeviceMappingResponse)
async def update_device_mapping(
    device_code: str,
    request: UpdateDeviceMappingRequest,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """更新设备映射"""
    try:
        updates = request.dict(exclude_unset=True, exclude_none=True)

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        success = manager.update_device_mapping(device_code, updates)

        if success:
            return DeviceMappingResponse(
                success=True,
                message=f"设备映射更新成功: {device_code}"
            )
        else:
            raise HTTPException(status_code=404, detail=f"设备映射未找到: {device_code}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新设备映射失败: {str(e)}")


@router.delete("/devices/{device_code}")
async def delete_device_mapping(
    device_code: str,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """删除设备映射"""
    try:
        success = manager.delete_device_mapping(device_code)

        if success:
            return {
                "success": True,
                "message": f"设备映射删除成功: {device_code}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"设备映射未找到: {device_code}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除设备映射失败: {str(e)}")


# ===== 统计信息API =====

@router.get("/statistics", response_model=PathStatisticsResponse)
async def get_path_statistics(
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """获取路径配置统计信息"""
    try:
        stats_data = manager.get_path_statistics()

        statistics = PathStatistics(
            total_modules=stats_data.get('total_modules', 0),
            total_tubes=stats_data.get('total_tubes', 0),
            total_paths=stats_data.get('total_tubes', 0),  # 路径数等于试管数
            total_steps=stats_data.get('total_steps', 0),
            device_type_stats=stats_data.get('device_type_distribution', {}),
            action_type_stats=stats_data.get('action_type_distribution', {}),
            module_tube_distribution=stats_data.get('module_tube_distribution', {})
        )

        return PathStatisticsResponse(
            success=True,
            message="获取路径统计信息成功",
            statistics=statistics
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取路径统计信息失败: {str(e)}")


# ===== 高级功能API =====

@router.get("/tubes/validate/{module_number}/{tube_number}")
async def validate_tube_path(
    module_number: int,
    tube_number: int,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """验证试管路径配置的完整性"""
    try:
        path_steps = manager.get_tube_path(module_number, tube_number)

        if not path_steps:
            raise HTTPException(
                status_code=404,
                detail=f"试管路径未找到: 模块{module_number}, 试管{tube_number}"
            )

        validation_results = []
        overall_valid = True

        for step in path_steps:
            device_code = step['device_code']
            mapping = manager.device_mappings.get(device_code)

            step_valid = mapping is not None and mapping.get('is_active', True)
            validation_results.append({
                'sequence_order': step['sequence_order'],
                'device_code': device_code,
                'valid': step_valid,
                'mapping_found': mapping is not None,
                'is_active': mapping.get('is_active', False) if mapping else False,
                'physical_id': mapping.get('physical_id') if mapping else None
            })

            if not step_valid:
                overall_valid = False

        return {
            'success': True,
            'message': "路径配置验证完成",
            'module_number': module_number,
            'tube_number': tube_number,
            'overall_valid': overall_valid,
            'total_steps': len(path_steps),
            'valid_steps': sum(1 for r in validation_results if r['valid']),
            'validation_details': validation_results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证试管路径失败: {str(e)}")


@router.post("/tubes/{module_number}/{tube_number}/dry-run")
async def dry_run_tube_path(
    module_number: int,
    tube_number: int,
    manager: ValvePathManager = Depends(get_valve_path_manager)
):
    """试管路径干运行（不实际操作设备）"""
    try:
        path_steps = manager.get_tube_path(module_number, tube_number)

        if not path_steps:
            raise HTTPException(
                status_code=404,
                detail=f"试管路径未找到: 模块{module_number}, 试管{tube_number}"
            )

        dry_run_results = []

        for step in path_steps:
            device_code = step['device_code']
            mapping = manager.device_mappings.get(device_code)

            result = {
                'sequence_order': step['sequence_order'],
                'device_code': device_code,
                'device_type': step['device_type'],
                'action_type': step['action_type'],
                'target_position': step.get('target_position'),
                'description': step.get('description'),
                'would_execute': mapping is not None and mapping.get('is_active', True),
                'physical_id': mapping.get('physical_id') if mapping else None,
                'controller_type': mapping.get('controller_type') if mapping else None,
                'notes': []
            }

            # 添加注意事项
            if not mapping:
                result['notes'].append("设备映射未找到")
            elif not mapping.get('is_active', True):
                result['notes'].append("设备未激活")

            dry_run_results.append(result)

        return {
            'success': True,
            'message': "试管路径干运行完成",
            'module_number': module_number,
            'tube_number': tube_number,
            'total_steps': len(path_steps),
            'executable_steps': sum(1 for r in dry_run_results if r['would_execute']),
            'dry_run_results': dry_run_results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试管路径干运行失败: {str(e)}")