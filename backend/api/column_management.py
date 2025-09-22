"""
色谱柱管理API
Column Management API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from services.column_manager import ColumnManager
from models.column_models import (
    CreateColumnRequest, UpdateColumnRequest, ColumnSearchQuery,
    ColumnResponse, ColumnListResponse, ColumnUsageResponse,
    ColumnStatisticsResponse
)

router = APIRouter()

# ===== 依赖注入 =====

def get_column_manager() -> ColumnManager:
    """获取色谱柱管理器实例"""
    return ColumnManager()

# ===== 色谱柱API路由 =====

@router.get("/", response_model=ColumnListResponse)
async def get_all_columns(
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """获取所有色谱柱信息"""
    try:
        columns = column_manager.get_all_columns()
        return ColumnListResponse(
            success=True,
            message="获取色谱柱列表成功",
            columns=columns,
            total_count=len(columns)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取色谱柱列表失败: {str(e)}")


@router.get("/search", response_model=ColumnListResponse)
async def search_columns(
    search_term: Optional[str] = None,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """搜索色谱柱"""
    try:
        columns = column_manager.search_columns(
            search_term=search_term
        )
        return ColumnListResponse(
            success=True,
            message="搜索色谱柱成功",
            columns=columns,
            total_count=len(columns)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索色谱柱失败: {str(e)}")


@router.get("/statistics", response_model=ColumnStatisticsResponse)
async def get_column_statistics(
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """获取色谱柱统计信息"""
    try:
        statistics = column_manager.get_column_statistics()
        return ColumnStatisticsResponse(
            success=True,
            message="获取色谱柱统计信息成功",
            statistics=statistics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取色谱柱统计信息失败: {str(e)}")


@router.get("/{column_id}", response_model=ColumnResponse)
async def get_column_by_id(
    column_id: int,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """根据ID获取特定色谱柱信息"""
    try:
        column = column_manager.get_column_by_id(column_id)
        if column:
            return ColumnResponse(
                success=True,
                message="获取色谱柱信息成功",
                column=column
            )
        else:
            raise HTTPException(status_code=404, detail=f"色谱柱不存在: {column_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取色谱柱信息失败: {str(e)}")


@router.get("/{column_id}/usage", response_model=ColumnUsageResponse)
async def get_column_usage_info(
    column_id: int,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """获取色谱柱使用情况"""
    try:
        usage_info = column_manager.get_column_usage_info(column_id)
        if usage_info:
            return ColumnUsageResponse(
                success=True,
                message="获取色谱柱使用情况成功",
                usage_info=usage_info
            )
        else:
            raise HTTPException(status_code=404, detail=f"色谱柱不存在: {column_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取色谱柱使用情况失败: {str(e)}")


@router.post("/", response_model=ColumnResponse)
async def create_column(
    request: CreateColumnRequest,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """创建新的色谱柱"""
    try:
        column_data = request.dict(exclude_unset=True)
        success = column_manager.create_column(column_data)

        if success:
            return ColumnResponse(
                success=True,
                message=f"色谱柱 '{request.column_code}' 创建成功",
                column={"column_code": request.column_code}
            )
        else:
            raise HTTPException(status_code=400, detail="色谱柱创建失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建色谱柱失败: {str(e)}")


@router.put("/{column_id}", response_model=ColumnResponse)
async def update_column(
    column_id: int,
    request: UpdateColumnRequest,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """更新色谱柱信息"""
    try:
        updates = request.dict(exclude_unset=True, exclude_none=True)

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        success = column_manager.update_column(column_id, updates)

        if success:
            # 获取更新后的色谱柱信息
            updated_column = column_manager.get_column_by_id(column_id)
            return ColumnResponse(
                success=True,
                message=f"色谱柱 {column_id} 更新成功",
                column=updated_column or {"column_id": column_id}
            )
        else:
            raise HTTPException(status_code=400, detail="色谱柱更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新色谱柱失败: {str(e)}")


@router.delete("/{column_id}")
async def delete_column(
    column_id: int,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """删除色谱柱"""
    try:
        success = column_manager.delete_column(column_id)

        if success:
            return {
                "success": True,
                "message": f"色谱柱 {column_id} 删除成功"
            }
        else:
            raise HTTPException(status_code=400, detail="色谱柱删除失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除色谱柱失败: {str(e)}")


# ===== 高级功能 =====

@router.post("/search/advanced", response_model=ColumnListResponse)
async def advanced_search_columns(
    query: ColumnSearchQuery,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """高级搜索色谱柱"""
    try:
        # 基础搜索
        columns = column_manager.search_columns(
            search_term=query.search_term
        )

        # 根据压力范围过滤
        if query.min_pressure or query.max_pressure:
            min_pressure = query.min_pressure or 0
            max_pressure = query.max_pressure or float('inf')
            columns = [col for col in columns
                      if col.get('max_pressure_bar') and
                      min_pressure <= col.get('max_pressure_bar', 0) <= max_pressure]

        # 根据流速范围过滤
        if query.min_flow_rate or query.max_flow_rate:
            min_flow = query.min_flow_rate or 0
            max_flow = query.max_flow_rate or float('inf')
            columns = [col for col in columns
                      if col.get('flow_rate_ml_min') and
                      min_flow <= col.get('flow_rate_ml_min', 0) <= max_flow]

        return ColumnListResponse(
            success=True,
            message="高级搜索色谱柱成功",
            columns=columns,
            total_count=len(columns)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"高级搜索色谱柱失败: {str(e)}")


@router.get("/{column_id}/methods")
async def get_column_methods(
    column_id: int,
    column_manager: ColumnManager = Depends(get_column_manager)
):
    """获取使用指定色谱柱的所有方法"""
    try:
        # 验证色谱柱是否存在
        column = column_manager.get_column_by_id(column_id)
        if not column:
            raise HTTPException(status_code=404, detail=f"色谱柱不存在: {column_id}")

        # 获取使用此色谱柱的方法
        methods = column_manager.db.get_methods()
        using_methods = [method for method in methods if method.get('column_id') == column_id]

        return {
            "success": True,
            "message": f"获取色谱柱 {column_id} 的方法列表成功",
            "column_id": column_id,
            "column_code": column.get('column_code', 'N/A'),
            "methods": using_methods,
            "total_methods": len(using_methods)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取色谱柱方法列表失败: {str(e)}")