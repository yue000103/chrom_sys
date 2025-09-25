"""
实验控制API
Experiment Control API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import uuid
import logging
from data.database_utils import ChromatographyDB
from models.experiment_control_models import (
    UpdateExperimentStatusRequest,
    ExperimentStatusResponse
)
from models.experiment_function_models import ExperimentConfig
from services.experiment_function_manager import ExperimentFunctionManager
from core.mqtt_manager import MQTTManager

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== 全局实验管理器实例 =====
_experiment_manager: Optional[ExperimentFunctionManager] = None

def get_experiment_manager() -> ExperimentFunctionManager:
    """获取实验管理器实例"""
    global _experiment_manager
    if _experiment_manager is None:
        mqtt_manager = MQTTManager()
        _experiment_manager = ExperimentFunctionManager(mqtt_manager)
    return _experiment_manager

# ===== 依赖注入 =====

def get_database() -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB()


# ===== 实验管理API =====

@router.get("/status/{experiment_id}", response_model=ExperimentStatusResponse)
async def get_experiment_status(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """获取实验实时状态"""
    try:
        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]

        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 尝试从运行时状态获取详细信息
        progress = await exp_manager.get_experiment_progress(str(experiment_id))

        if progress:
            # 实验正在运行，返回实时状态
            status_mapping = {
                "RUNNING": "running",
                "PAUSED": "paused",
                "COMPLETED": "completed",
                "FAILED": "failed",
                "CANCELLED": "terminated"
            }
            mapped_status = status_mapping.get(progress.current_status.value, "running")
            is_paused = progress.current_status.value == "PAUSED"

            return ExperimentStatusResponse(
                success=True,
                message="获取实验状态成功",
                experiment_id=experiment_id,
                status=mapped_status,
                current_step=progress.current_step,
                step_status="in_progress" if progress.current_status.value == "RUNNING" else "paused",
                is_paused=is_paused,
                timestamp=datetime.now(),
                progress_percentage=progress.progress_percentage,
                phase=progress.current_phase.value if progress.current_phase else None
            )
        else:
            # 实验不在运行时状态，从数据库获取基础状态
            base_status = experiment.get("status", "pending")
            status_mapping = {
                "pending": "pending",
                "未结束": "pending",
                "pretreatment": "pretreatment",
                "running": "running",
                "运行中": "running",
                "paused": "paused",
                "已暂停": "paused",
                "completed": "completed",
                "已完成": "completed",
                "terminated": "terminated"
            }
            mapped_status = status_mapping.get(base_status, "pending")

            return ExperimentStatusResponse(
                success=True,
                message="获取实验状态成功",
                experiment_id=experiment_id,
                status=mapped_status,
                current_step=None,
                step_status=None,
                is_paused=False,
                timestamp=datetime.now()
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验状态失败: {str(e)}")


@router.post("/start/{experiment_id}")
async def start_experiment(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """启动实验（前端调用的接口）"""
    try:
        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]
        print("实验信息:", experiment)

        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 检查系统是否忙碌
        if exp_manager.is_experiment_running():
            raise HTTPException(status_code=400, detail="系统正在运行其他实验，无法启动新实验")

        # 创建实验配置
        config = ExperimentConfig(
            experiment_id=str(experiment_id),
            experiment_name=experiment.get('experiment_name', f'实验_{experiment_id}'),
            method_id=str(experiment.get('method_id', '')),
            sample_id=str(experiment.get('sample_id', '')),
            user_id=experiment.get('created_by', 'system'),
            priority=experiment.get('priority', 1),
            notes=experiment.get('description', '')
        )

        # 启动实验
        progress = await exp_manager.start_experiment(config)

        # 更新数据库状态
        affected = db.update_data(
            "experiments",
            {
                "status": "running",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            # 如果数据库更新失败，尝试停止已启动的实验
            try:
                await exp_manager.stop_experiment(str(experiment_id), "system", "数据库更新失败")
            except:
                pass
            raise HTTPException(status_code=500, detail="启动实验失败：数据库更新失败")

        return {
            "success": True,
            "message": f"实验启动成功: {experiment.get('experiment_name')}",
            "experiment_id": experiment_id,
            "status": "running",
            "current_step": progress.current_step,
            "progress_percentage": progress.progress_percentage
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动实验失败: {str(e)}")


@router.post("/pause/{experiment_id}")
async def pause_experiment(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """暂停实验"""
    try:
        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 检查实验是否正在运行
        if not exp_manager.is_experiment_running():
            raise HTTPException(status_code=400, detail="当前没有正在运行的实验")

        current_exp_id = exp_manager.get_current_experiment_id()
        if current_exp_id != str(experiment_id):
            raise HTTPException(status_code=400, detail=f"实验 {experiment_id} 不是当前正在运行的实验")

        # 暂停实验
        success = await exp_manager.pause_experiment(str(experiment_id), "api_user", "用户手动暂停")

        if not success:
            raise HTTPException(status_code=500, detail="暂停实验失败")

        # 更新数据库状态
        affected = db.update_data(
            "experiments",
            {
                "status": "paused",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            logger.warning(f"数据库状态更新失败，但实验已暂停: {experiment_id}")

        # 获取实验信息
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )
        experiment = experiments[0] if experiments else {}

        return {
            "success": True,
            "message": f"实验暂停成功: {experiment.get('experiment_name', experiment_id)}",
            "experiment_id": experiment_id,
            "status": "paused"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停实验失败: {str(e)}")


@router.post("/resume/{experiment_id}")
async def resume_experiment(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """继续实验"""
    try:
        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]

        # 检查实验是否可以恢复
        progress = await exp_manager.get_experiment_progress(str(experiment_id))
        if not progress:
            raise HTTPException(status_code=400, detail=f"实验 {experiment_id} 不在运行状态，无法恢复")

        # 恢复实验
        success = await exp_manager.resume_experiment(str(experiment_id), "api_user")

        if not success:
            raise HTTPException(status_code=500, detail="恢复实验失败")

        # 更新数据库状态
        affected = db.update_data(
            "experiments",
            {
                "status": "running",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            logger.warning(f"数据库状态更新失败，但实验已恢复: {experiment_id}")

        return {
            "success": True,
            "message": f"实验恢复成功: {experiment.get('experiment_name')}",
            "experiment_id": experiment_id,
            "status": "running"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复实验失败: {str(e)}")


@router.post("/terminate/{experiment_id}")
async def terminate_experiment(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """终止实验"""
    try:
        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]
        current_status = experiment.get("status")

        # 检查实验是否正在运行
        progress = await exp_manager.get_experiment_progress(str(experiment_id))
        if progress:
            # 停止实验
            result = await exp_manager.stop_experiment(str(experiment_id), "api_user", "用户手动终止")
            logger.info(f"实验终止结果: {result}")

        # 更新数据库状态
        affected = db.update_data(
            "experiments",
            {
                "status": "terminated",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            logger.warning(f"数据库状态更新失败，但实验已终止: {experiment_id}")

        return {
            "success": True,
            "message": f"实验终止成功: {experiment.get('experiment_name')}",
            "experiment_id": experiment_id,
            "previous_status": current_status,
            "new_status": "terminated"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"终止实验失败: {str(e)}")





@router.put("/{experiment_id}/status")
async def update_experiment_status(
    experiment_id: str,
    request: UpdateExperimentStatusRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """更新实验状态"""
    try:
        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        # 更新状态
        affected = db.update_data(
            "experiments",
            {
                "status": request.status,
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (experiment_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=500, detail="状态更新失败")

        return {
            "success": True,
            "message": f"实验状态更新成功: {request.status}",
            "experiment_id": experiment_id,
            "new_status": request.status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实验状态失败: {str(e)}")




# ===== 高级功能API =====





@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "实验控制API运行正常"}


# ==================== 实验运行时控制API ====================


# 运行时控制相关的Pydantic模型
from pydantic import BaseModel, Field

class ExperimentStartRuntimeRequest(BaseModel):
    """启动实验运行时请求"""
    experiment_id: int = Field(..., description="实验ID")
    method_id: int = Field(..., description="方法ID")
    start_time: datetime = Field(..., description="开始时间")
    start_tube_number: int = Field(..., ge=1, description="开始试管号")

class ExperimentStopRuntimeRequest(BaseModel):
    """停止实验运行时请求"""
    experiment_id: int = Field(..., description="实验ID")

class ExperimentResumeRuntimeRequest(BaseModel):
    """继续实验运行时请求"""
    experiment_id: int = Field(..., description="实验ID")

class ExperimentRuntimeResponse(BaseModel):
    """实验运行时响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime


@router.post("/runtime/start", response_model=ExperimentRuntimeResponse)
async def start_experiment_runtime(
    request: ExperimentStartRuntimeRequest
):
    """
    启动实验运行时
    """
    try:
        # 从数据库获取实验信息
        db = ChromatographyDB()
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(request.experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail="实验未找到")

        experiment = experiments[0]

        # TODO: 实现实验启动逻辑
        # 这里暂时返回成功响应，具体实现稍后完成

        # 更新数据库中的实验状态
        db.update_data(
            "experiments",
            {"status": "运行中", "updated_at": datetime.now().isoformat()},
            "experiment_id = ?",
            (request.experiment_id,)
        )

        return ExperimentRuntimeResponse(
            success=True,
            message="实验运行时启动成功",
            data={
                "experiment_id": request.experiment_id,
                "method_id": request.method_id,
                "start_time": request.start_time.isoformat(),
                "start_tube_number": request.start_tube_number,
                "status": "running"
            },
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动实验运行时失败: {str(e)}")


@router.post("/runtime/stop", response_model=ExperimentRuntimeResponse)
async def stop_experiment_runtime(
    request: ExperimentStopRuntimeRequest
):
    """
    停止实验运行时
    """
    try:
        # 检查实验是否存在
        db = ChromatographyDB()
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(request.experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail="实验未找到")

        # TODO: 实现实验停止逻辑
        # 这里暂时返回成功响应，具体实现稍后完成

        # 更新数据库中的实验状态
        db.update_data(
            "experiments",
            {
                "status": "已完成",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (request.experiment_id,)
        )

        return ExperimentRuntimeResponse(
            success=True,
            message="实验停止成功",
            data={
                "experiment_id": request.experiment_id,
                "final_status": "stopped"
            },
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止实验运行时失败: {str(e)}")


@router.post("/runtime/resume", response_model=ExperimentRuntimeResponse)
async def resume_experiment_runtime(
    request: ExperimentResumeRuntimeRequest
):
    """
    继续实验运行时
    """
    try:
        # 检查实验是否存在
        db = ChromatographyDB()
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(request.experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail="实验未找到")

        experiment = experiments[0]
        current_status = experiment.get("status")

        # 检查实验是否可以继续（必须是已暂停或已停止状态）
        if current_status not in ["已暂停", "已停止", "已完成"]:
            raise HTTPException(status_code=400, detail=f"实验状态为'{current_status}'，无法继续")

        # TODO: 实现实验继续逻辑
        # 这里暂时返回成功响应，具体实现稍后完成

        # 更新数据库中的实验状态
        db.update_data(
            "experiments",
            {
                "status": "运行中",
                "updated_at": datetime.now().isoformat()
            },
            "experiment_id = ?",
            (request.experiment_id,)
        )

        return ExperimentRuntimeResponse(
            success=True,
            message="实验继续成功",
            data={
                "experiment_id": request.experiment_id,
                "status": "running",
                "previous_status": current_status
            },
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"继续实验运行时失败: {str(e)}")




@router.get("/runtime/status/{experiment_id}", response_model=ExperimentRuntimeResponse)
async def get_experiment_runtime_status(
    experiment_id: int
):
    """
    获取实验运行时状态
    """
    try:
        # TODO: 实现获取实验运行时状态的逻辑

        # 检查实验是否存在
        db = ChromatographyDB()
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail="实验未找到")

        experiment = experiments[0]

        return ExperimentRuntimeResponse(
            success=True,
            message="获取实验运行时状态成功",
            data={
                "experiment_id": experiment_id,
                "status": experiment.get("status", "unknown"),
                "progress_percentage": 0,  # TODO: 实现进度计算
                "current_step": "初始化"  # TODO: 实现步骤跟踪
            },
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验运行时状态失败: {str(e)}")


@router.get("/runtime/current", response_model=ExperimentRuntimeResponse)
async def get_current_experiment_runtime():
    """
    获取当前正在运行的实验信息
    """
    try:
        # TODO: 实现获取当前运行实验的逻辑

        db = ChromatographyDB()
        running_experiments = db.query_data(
            "experiments",
            where_condition="status = ?",
            where_params=("运行中",),
            limit=1
        )

        if not running_experiments:
            return ExperimentRuntimeResponse(
                success=True,
                message="当前没有运行中的实验",
                data={"current_experiment_id": None, "is_running": False},
                timestamp=datetime.now()
            )

        current_experiment = running_experiments[0]

        return ExperimentRuntimeResponse(
            success=True,
            message="获取当前实验成功",
            data={
                "current_experiment_id": current_experiment.get("experiment_id"),
                "is_running": True,
                "status": "running",
                "experiment_name": current_experiment.get("experiment_name")
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前实验失败: {str(e)}")


@router.get("/gradient/{experiment_id}")
async def get_experiment_gradient_table(
    experiment_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """
    获取指定实验对应方法的梯度时间表
    """
    try:
        # 检查实验是否存在
        experiments = db.query_data(
            "experiments",
            where_condition="experiment_id = ?",
            where_params=(experiment_id,)
        )

        if not experiments:
            raise HTTPException(status_code=404, detail=f"实验未找到: {experiment_id}")

        experiment = experiments[0]
        method_id = experiment.get('method_id')

        if not method_id:
            raise HTTPException(status_code=400, detail=f"实验 {experiment_id} 没有关联的方法")

        # 查询方法信息
        methods = db.query_data(
            "methods",
            where_condition="method_id = ?",
            where_params=(method_id,)
        )

        if not methods:
            raise HTTPException(status_code=404, detail=f"方法未找到: {method_id}")

        method = methods[0]
        gradient_time_table = method.get('gradient_time_table')

        # 如果gradient_time_table是JSON字符串，尝试解析
        if isinstance(gradient_time_table, str):
            try:
                import json
                gradient_time_table = json.loads(gradient_time_table)
            except json.JSONDecodeError:
                logger.warning(f"方法 {method_id} 的gradient_time_table JSON解析失败")
                gradient_time_table = {}

        return {
            "success": True,
            "message": "获取梯度时间表成功",
            "experiment_id": experiment_id,
            "method_id": method_id,
            "method_name": method.get('method_name'),
            "gradient_time_table": gradient_time_table or {},
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取梯度时间表失败: {str(e)}")


@router.get("/current/gradient")
async def get_current_experiment_gradient_table(
    db: ChromatographyDB = Depends(get_database)
):
    """
    获取当前正在运行的实验的梯度时间表
    """
    try:
        # 获取实验管理器
        exp_manager = get_experiment_manager()

        # 检查是否有实验正在运行
        if not exp_manager.is_experiment_running():
            raise HTTPException(status_code=400, detail="当前没有正在运行的实验")

        current_exp_id = exp_manager.get_current_experiment_id()

        if not current_exp_id:
            raise HTTPException(status_code=400, detail="无法获取当前实验ID")

        # 调用上面的接口获取梯度时间表
        return await get_experiment_gradient_table(int(current_exp_id), db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前实验梯度时间表失败: {str(e)}")




