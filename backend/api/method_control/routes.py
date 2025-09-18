"""
方法控制API路由
Method Control API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from models.api_models import (
    CreateMethodRequest,
    UpdateMethodRequest,
    MethodListRequest,
    MethodListResponse,
    ValidateMethodRequest,
    ValidateMethodResponse
)
from models.method_models import AnalysisMethod, MethodType, MethodStatus
from services.method_manager import MethodManager
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

router = APIRouter(prefix="/method", tags=["method_control"])


@router.post("/create", response_model=Dict[str, Any])
async def create_method(
    request: CreateMethodRequest,
    method_manager = Depends(get_method_manager)
):
    """创建新的分析方法"""
    try:
        # 构造方法数据
        method_data = {
            "method_name": request.method_name,
            "description": request.description,
            "gradient_program": request.gradient_program.dict(),
            "tube_sequence": request.tube_sequence.dict(),
            "detection_parameters": request.detection_parameters,
            "column_parameters": request.column_parameters
        }

        # 创建方法
        method = await method_manager.create_method(method_data, request.created_by)

        return {
            "success": True,
            "message": "方法创建成功",
            "data": method.dict() if hasattr(method, 'dict') else method
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建方法失败: {str(e)}")


@router.put("/update", response_model=Dict[str, Any])
async def update_method(
    request: UpdateMethodRequest,
    method_manager = Depends(get_method_manager)
):
    """更新分析方法"""
    try:
        # 构造更新数据
        updates = {}
        if request.method_name is not None:
            updates["method_name"] = request.method_name
        if request.description is not None:
            updates["description"] = request.description
        if request.gradient_program is not None:
            updates["gradient_program"] = request.gradient_program.dict()
        if request.tube_sequence is not None:
            updates["tube_sequence"] = request.tube_sequence.dict()
        if request.detection_parameters is not None:
            updates["detection_parameters"] = request.detection_parameters
        if request.column_parameters is not None:
            updates["column_parameters"] = request.column_parameters

        # 更新方法
        method = await method_manager.update_method(
            request.method_id,
            updates,
            request.modified_by
        )

        return {
            "success": True,
            "message": "方法更新成功",
            "data": method.dict() if hasattr(method, 'dict') else method
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新方法失败: {str(e)}")


@router.get("/{method_id}", response_model=Dict[str, Any])
async def get_method(
    method_id: str,
    method_manager = Depends(get_method_manager)
):
    """获取单个方法"""
    try:
        method = await method_manager.get_method(method_id)
        if not method:
            raise HTTPException(status_code=404, detail="方法未找到")

        return {
            "success": True,
            "message": "获取方法成功",
            "data": method.dict() if hasattr(method, 'dict') else method
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取方法失败: {str(e)}")


@router.post("/list", response_model=MethodListResponse)
async def list_methods(
    request: MethodListRequest,
    method_manager = Depends(get_method_manager)
):
    """列出方法"""
    try:
        # 计算偏移量
        offset = (request.page - 1) * request.page_size

        # 转换枚举类型
        method_type = MethodType(request.method_type) if request.method_type else None
        status = MethodStatus(request.status) if request.status else None

        # 获取方法列表
        methods = await method_manager.list_methods(
            method_type=method_type,
            status=status,
            created_by=request.created_by,
            limit=request.page_size,
            offset=offset
        )

        # 获取总数（简化处理）
        total_count = len(methods) + offset

        return MethodListResponse(
            success=True,
            message="获取方法列表成功",
            methods=methods,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取方法列表失败: {str(e)}")


@router.delete("/{method_id}")
async def delete_method(
    method_id: str,
    deleted_by: str = Query(..., description="删除者ID"),
    method_manager = Depends(get_method_manager)
):
    """删除方法"""
    try:
        result = await method_manager.delete_method(method_id, deleted_by)

        return {
            "success": True,
            "message": "方法删除成功",
            "data": {"deleted": result}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除方法失败: {str(e)}")


@router.post("/{method_id}/archive")
async def archive_method(
    method_id: str,
    archived_by: str = Query(..., description="归档者ID"),
    method_manager = Depends(get_method_manager)
):
    """归档方法"""
    try:
        result = await method_manager.archive_method(method_id, archived_by)

        return {
            "success": True,
            "message": "方法归档成功",
            "data": {"archived": result}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归档方法失败: {str(e)}")


@router.post("/validate", response_model=ValidateMethodResponse)
async def validate_method(
    request: ValidateMethodRequest,
    method_manager = Depends(get_method_manager)
):
    """验证方法"""
    try:
        # 获取方法
        method = await method_manager.get_method(request.method_id)
        if not method:
            raise HTTPException(status_code=404, detail="方法未找到")

        # 验证方法
        validation_result = await method_manager.validate_method(method)

        return ValidateMethodResponse(
            success=True,
            message="方法验证完成",
            method_id=request.method_id,
            validation_status="valid" if validation_result["valid"] else "invalid",
            validation_errors=validation_result.get("errors", []),
            validation_warnings=validation_result.get("warnings", []),
            estimated_run_time=method.run_time_minutes if hasattr(method, 'run_time_minutes') else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证方法失败: {str(e)}")


@router.post("/{method_id}/copy")
async def copy_method(
    method_id: str,
    new_name: str = Query(..., description="新方法名称"),
    copied_by: str = Query(..., description="复制者ID"),
    method_manager = Depends(get_method_manager)
):
    """复制方法"""
    try:
        new_method = await method_manager.copy_method(method_id, new_name, copied_by)

        return {
            "success": True,
            "message": "方法复制成功",
            "data": new_method.dict() if hasattr(new_method, 'dict') else new_method
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制方法失败: {str(e)}")


@router.get("/{method_id}/usage_stats")
async def get_method_usage_stats(
    method_id: str,
    method_manager = Depends(get_method_manager)
):
    """获取方法使用统计"""
    try:
        stats = await method_manager.get_method_usage_stats(method_id)

        return {
            "success": True,
            "message": "获取使用统计成功",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取使用统计失败: {str(e)}")


@router.get("/search")
async def search_methods(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    method_manager = Depends(get_method_manager)
):
    """搜索方法"""
    try:
        methods = await method_manager.search_methods(query, limit)

        return {
            "success": True,
            "message": "搜索完成",
            "data": [method.dict() if hasattr(method, 'dict') else method for method in methods]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索方法失败: {str(e)}")


@router.get("/templates")
async def list_method_templates(
    method_manager = Depends(get_method_manager)
):
    """列出方法模板"""
    try:
        # 获取模板类型的方法
        templates = await method_manager.list_methods(
            method_type=MethodType.TEMPLATE,
            limit=50
        )

        return {
            "success": True,
            "message": "获取模板列表成功",
            "data": [method.dict() if hasattr(method, 'dict') else method for method in templates]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.post("/import")
async def import_method(
    method_data: Dict[str, Any],
    imported_by: str = Query(..., description="导入者ID"),
    method_manager = Depends(get_method_manager)
):
    """导入方法"""
    try:
        # 添加导入者信息
        method_data["created_by"] = imported_by
        method_data["imported"] = True

        # 创建方法
        method = await method_manager.create_method(method_data, imported_by)

        return {
            "success": True,
            "message": "方法导入成功",
            "data": method.dict() if hasattr(method, 'dict') else method
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入方法失败: {str(e)}")


@router.get("/{method_id}/export")
async def export_method(
    method_id: str,
    export_format: str = Query("json", description="导出格式"),
    method_manager = Depends(get_method_manager)
):
    """导出方法"""
    try:
        method = await method_manager.get_method(method_id)
        if not method:
            raise HTTPException(status_code=404, detail="方法未找到")

        # 根据格式导出
        if export_format.lower() == "json":
            exported_data = method.dict() if hasattr(method, 'dict') else method
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")

        return {
            "success": True,
            "message": "方法导出成功",
            "data": {
                "method_id": method_id,
                "export_format": export_format,
                "exported_data": exported_data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出方法失败: {str(e)}")