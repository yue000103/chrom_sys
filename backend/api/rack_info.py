"""
试管架信息管理API
Rack Info Management API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging

from models.rack_info_models import (
    CreateRackInfoRequest,
    UpdateRackInfoRequest,
    UpdateRackStatusRequest,
    RackInfoResponse,
    RackInfoListResponse,
    RackInfoStatisticsResponse
)
from data.database_utils import ChromatographyDB

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== 依赖注入 =====

def get_database() -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB()

# ===== 试管架信息管理API =====

@router.post("/", response_model=RackInfoResponse)
async def create_rack_info(
    request: CreateRackInfoRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """创建试管架信息"""
    try:
        # 获取下一个自增rack_id
        max_id_result = db.execute_custom_query("SELECT MAX(rack_id) as max_id FROM rack_info")
        max_id = max_id_result[0]['max_id'] if max_id_result and max_id_result[0]['max_id'] is not None else 0
        new_rack_id = max_id + 1

        # 准备数据
        rack_data = {
            'rack_id': new_rack_id,
            'rack_name': request.rack_name,
            'tube_volume_ml': request.tube_volume_ml,
            'tube_count': request.tube_count,
            'status': request.status,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 插入数据库
        success = db.insert_data("rack_info", rack_data)

        if not success:
            raise HTTPException(status_code=500, detail="试管架信息创建失败")

        logger.info(f"创建试管架信息成功: {new_rack_id}")

        return RackInfoResponse(
            success=True,
            message=f"试管架信息创建成功: {new_rack_id}",
            rack_info=rack_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建试管架信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建试管架信息失败: {str(e)}")


@router.get("/", response_model=RackInfoListResponse)
async def get_rack_info_list(
    limit: Optional[int] = 50,
    db: ChromatographyDB = Depends(get_database)
):
    """获取试管架信息列表"""
    try:
        # 查询试管架信息
        rack_list = db.query_data(
            "rack_info",
            order_by="rack_id ASC",
            limit=limit
        )

        # 计算统计信息
        total_count = len(rack_list)

        return RackInfoListResponse(
            success=True,
            message="获取试管架信息列表成功",
            rack_list=rack_list,
            total_count=total_count,
            active_count=0,
            total_capacity=0,
            total_occupied=0
        )

    except Exception as e:
        logger.error(f"获取试管架信息列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取试管架信息列表失败: {str(e)}")


@router.get("/{rack_id}", response_model=RackInfoResponse)
async def get_rack_info_by_id(
    rack_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """根据ID获取试管架信息详情"""
    try:
        rack_list = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        if not rack_list:
            raise HTTPException(status_code=404, detail=f"试管架未找到: {rack_id}")

        rack_info = rack_list[0]

        return RackInfoResponse(
            success=True,
            message="获取试管架信息成功",
            rack_info=rack_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试管架信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取试管架信息失败: {str(e)}")


@router.put("/{rack_id}", response_model=RackInfoResponse)
async def update_rack_info(
    rack_id: int,
    request: UpdateRackInfoRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """更新试管架信息"""
    try:
        # 检查试管架是否存在
        existing_racks = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        if not existing_racks:
            raise HTTPException(status_code=404, detail=f"试管架未找到: {rack_id}")

        # 准备更新数据（只更新提供的字段）
        update_data = {"updated_at": datetime.now().isoformat()}

        if request.tube_volume_ml is not None:
            update_data['tube_volume_ml'] = request.tube_volume_ml

        if request.tube_count is not None:
            update_data['tube_count'] = request.tube_count

        if request.rack_name is not None:
            update_data['rack_name'] = request.rack_name

        if request.status is not None:
            update_data['status'] = request.status

        # 执行更新
        affected = db.update_data(
            "rack_info",
            update_data,
            "rack_id = ?",
            (rack_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="试管架信息更新失败")

        # 获取更新后的数据
        updated_racks = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        logger.info(f"更新试管架信息成功: {rack_id}")

        return RackInfoResponse(
            success=True,
            message=f"试管架信息更新成功: {rack_id}",
            rack_info=updated_racks[0] if updated_racks else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新试管架信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新试管架信息失败: {str(e)}")


@router.patch("/{rack_id}/status", response_model=RackInfoResponse)
async def update_rack_status(
    rack_id: int,
    request: UpdateRackStatusRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """更新试管架状态"""
    try:
        # 检查试管架是否存在
        existing_racks = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        if not existing_racks:
            raise HTTPException(status_code=404, detail=f"试管架未找到: {rack_id}")


        # 更新状态
        update_data = {
            "status": request.status,
            "updated_at": datetime.now().isoformat()
        }

        affected = db.update_data(
            "rack_info",
            update_data,
            "rack_id = ?",
            (rack_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="试管架状态更新失败")

        # 获取更新后的数据
        updated_racks = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        logger.info(f"更新试管架状态成功: {rack_id} -> {request.status}")

        return RackInfoResponse(
            success=True,
            message=f"试管架状态更新成功: {request.status}",
            rack_info=updated_racks[0] if updated_racks else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新试管架状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新试管架状态失败: {str(e)}")


@router.delete("/{rack_id}")
async def delete_rack_info(
    rack_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """删除试管架信息"""
    try:
        # 检查试管架是否存在
        existing_racks = db.query_data(
            "rack_info",
            where_condition="rack_id = ?",
            where_params=(rack_id,)
        )

        if not existing_racks:
            raise HTTPException(status_code=404, detail=f"试管架未找到: {rack_id}")

        rack_info = existing_racks[0]

        # 直接删除，不检查占用状态

        # 删除试管架
        affected = db.delete_data(
            "rack_info",
            "rack_id = ?",
            (rack_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="试管架信息删除失败")

        logger.info(f"删除试管架信息成功: {rack_id}")

        return {
            "success": True,
            "message": f"试管架信息删除成功: {rack_info.get('rack_name', rack_id)}",
            "rack_id": rack_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除试管架信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除试管架信息失败: {str(e)}")




@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "message": "试管架信息管理API运行正常",
        "timestamp": datetime.now().isoformat()
    }