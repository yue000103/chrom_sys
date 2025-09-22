"""
实验数据管理API
Experiment Data Management API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging

from models.experiment_models import (
    CreateExperimentRequest,
    UpdateExperimentRequest,
    ExperimentResponse,
    ExperimentListResponse
)
from data.database_utils import ChromatographyDB

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== 依赖注入 =====

def get_database() -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB()

# ===== 实验数据管理API =====

@router.get("/", response_model=ExperimentListResponse)
async def get_all_experiments(
    limit: Optional[int] = 100,
    db: ChromatographyDB = Depends(get_database)
):
    """获取所有实验信息"""
    try:
        # 查询所有实验数据
        experiments = db.query_data(
            "experiments",
            order_by="experiment_id DESC",
            limit=limit
        )

        total_count = len(experiments)

        return ExperimentListResponse(
            success=True,
            message="获取实验列表成功",
            experiments=experiments,
            total_count=total_count
        )

    except Exception as e:
        logger.error(f"获取实验列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实验列表失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "message": "实验数据管理API运行正常",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment_by_id(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """根据ID获取实验详情"""
    try:
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]

        return ExperimentResponse(
            success=True,
            message="获取实验信息成功",
            experiment=experiment
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实验信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实验信息失败: {str(e)}")


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """新增实验数据"""
    try:
        # 准备数据
        experiment_data = {
            'experiment_name': request.experiment_name,
            'experiment_type': request.experiment_type or 'standard',
            'method_id': request.method_id,
            'operator': request.operator or 'unknown',
            'status': 'pending',  # 默认状态为待执行
            'description': request.description,
            'experiment_description': request.experiment_description,
            'purge_system': 1 if request.purge_system else 0,
            'purge_column': 1 if request.purge_column else 0,
            'purge_column_time_min': request.purge_column_time_min or 0,
            'column_balance': 1 if request.column_balance else 0,
            'column_balance_time_min': request.column_balance_time_min or 0,
            'is_peak_driven': 1 if request.is_peak_driven else 0,
            'collection_volume_ml': request.collection_volume_ml or 0.0,
            'wash_volume_ml': request.wash_volume_ml or 0.0,
            'wash_cycles': request.wash_cycles or 0,
            'column_conditioning_solution': request.column_conditioning_solution,
            'scheduled_start_time': request.scheduled_start_time.isoformat() if request.scheduled_start_time else None,
            'priority': request.priority or 1,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 插入数据库
        success = db.insert_data("experiments", experiment_data)

        if not success:
            raise HTTPException(status_code=500, detail="实验数据创建失败")

        # 获取新创建的实验ID
        new_experiments = db.query_data(
            "experiments",
            where_condition="experiment_name = ? AND created_at = ?",
            where_params=(experiment_data['experiment_name'], experiment_data['created_at']),
            order_by="experiment_id DESC",
            limit=1
        )

        if new_experiments:
            experiment_data['experiment_id'] = new_experiments[0]['experiment_id']

        logger.info(f"创建实验成功: {experiment_data.get('experiment_id', 'unknown')}")

        return ExperimentResponse(
            success=True,
            message=f"实验创建成功: {request.experiment_name}",
            experiment=experiment_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建实验失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建实验失败: {str(e)}")


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: int,
    request: UpdateExperimentRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """修改实验数据（不包含method_id）"""
    try:
        # 检查实验是否存在
        existing_experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not existing_experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        # 准备更新数据（只更新提供的字段）
        update_data = {"updated_at": datetime.now().isoformat()}

        if request.experiment_name is not None:
            update_data['experiment_name'] = request.experiment_name

        if request.experiment_type is not None:
            update_data['experiment_type'] = request.experiment_type

        if request.operator is not None:
            update_data['operator'] = request.operator

        if request.purge_system is not None:
            update_data['purge_system'] = 1 if request.purge_system else 0

        if request.purge_column is not None:
            update_data['purge_column'] = 1 if request.purge_column else 0

        if request.purge_column_time_min is not None:
            update_data['purge_column_time_min'] = request.purge_column_time_min

        if request.column_balance is not None:
            update_data['column_balance'] = 1 if request.column_balance else 0

        if request.column_balance_time_min is not None:
            update_data['column_balance_time_min'] = request.column_balance_time_min

        if request.is_peak_driven is not None:
            update_data['is_peak_driven'] = 1 if request.is_peak_driven else 0

        if request.collection_volume_ml is not None:
            update_data['collection_volume_ml'] = request.collection_volume_ml

        if request.wash_volume_ml is not None:
            update_data['wash_volume_ml'] = request.wash_volume_ml

        if request.wash_cycles is not None:
            update_data['wash_cycles'] = request.wash_cycles

        if request.column_conditioning_solution is not None:
            update_data['column_conditioning_solution'] = request.column_conditioning_solution

        if request.scheduled_start_time is not None:
            update_data['scheduled_start_time'] = request.scheduled_start_time.isoformat()

        if request.priority is not None:
            update_data['priority'] = request.priority

        if request.description is not None:
            update_data['description'] = request.description

        if request.experiment_description is not None:
            update_data['experiment_description'] = request.experiment_description

        if request.status is not None:
            update_data['status'] = request.status

        # 执行更新
        affected = db.update_data(
            "experiments",
            update_data,
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="实验数据更新失败")

        # 获取更新后的数据
        updated_experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        logger.info(f"更新实验成功: {experiment_id}")

        return ExperimentResponse(
            success=True,
            message=f"实验更新成功: {experiment_id}",
            experiment=updated_experiments[0] if updated_experiments else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实验失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新实验失败: {str(e)}")


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """删除实验数据"""
    try:
        # 检查实验是否存在
        existing_experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not existing_experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = existing_experiments[0]

        # 删除实验
        affected = db.delete_data(
            "experiments",
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="实验数据删除失败")

        logger.info(f"删除实验成功: {experiment_id}")

        return {
            "success": True,
            "message": f"实验删除成功: {experiment.get('experiment_name', experiment_id)}",
            "experiment_id": experiment_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除实验失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除实验失败: {str(e)}")