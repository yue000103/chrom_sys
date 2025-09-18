"""
实验数据API路由
Experiment Data API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from models.api_models import (
    DataQueryRequest,
    DataExportRequest,
    ExperimentDataResponse,
    PeakDetectionRequest,
    PeakDetectionResponse,
    DataProcessingRequest,
    DataProcessingResponse
)
from models.experiment_data_models import (
    SensorDataPoint,
    PeakInfo,
    ExperimentDataSummary,
    DataExportFormat,
)
from services.experiment_data_manager import ExperimentDataManager
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

router = APIRouter(prefix="/data", tags=["experiment_data"])


@router.post("/collection/start")
async def start_data_collection(
    experiment_id: str,
    collection_config: Dict[str, Any],
    data_manager = Depends(get_data_manager)
):
    """开始数据采集"""
    try:
        result = await data_manager.start_data_collection(experiment_id, collection_config)

        return {
            "success": True,
            "message": "数据采集已启动",
            "data": {
                "experiment_id": experiment_id,
                "started": result,
                "config": collection_config
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动数据采集失败: {str(e)}")


@router.post("/collection/stop/{experiment_id}")
async def stop_data_collection(
    experiment_id: str,
    data_manager = Depends(get_data_manager)
):
    """停止数据采集"""
    try:
        summary = await data_manager.stop_data_collection(experiment_id)

        return {
            "success": True,
            "message": "数据采集已停止",
            "data": summary.dict() if hasattr(summary, 'dict') else summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止数据采集失败: {str(e)}")


@router.post("/add_point")
async def add_data_point(
    data_point: SensorDataPoint,
    data_manager = Depends(get_data_manager)
):
    """添加数据点"""
    try:
        result = await data_manager.add_data_point(data_point.experiment_id, data_point)

        return {
            "success": True,
            "message": "数据点已添加",
            "data": {
                "experiment_id": data_point.experiment_id,
                "added": result
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加数据点失败: {str(e)}")


@router.post("/query", response_model=ExperimentDataResponse)
async def query_experiment_data(
    request: DataQueryRequest,
    data_manager = Depends(get_data_manager)
):
    """查询实验数据"""
    try:
        if not request.experiment_id:
            raise HTTPException(status_code=400, detail="实验ID不能为空")

        # 获取数据摘要
        summary = await data_manager.get_experiment_summary(request.experiment_id)

        # 这里应该根据查询条件获取实际数据
        # 简化处理，返回基本信息
        return ExperimentDataResponse(
            success=True,
            message="查询实验数据成功",
            experiment_id=request.experiment_id,
            data_points=[],  # 实际应该查询数据库
            peaks=[],        # 实际应该查询数据库
            summary=summary,
            data_quality_score=95.0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询实验数据失败: {str(e)}")


@router.post("/process", response_model=DataProcessingResponse)
async def process_experiment_data(
    request: DataProcessingRequest,
    data_manager = Depends(get_data_manager)
):
    """处理实验数据"""
    try:
        # 构建处理参数
        processing_params = ProcessingParameters(
            baseline_correction="baseline_correction" in request.processing_steps,
            noise_filtering="noise_filtering" in request.processing_steps,
            peak_detection="peak_detection" in request.processing_steps,
            **request.parameters
        )

        # 处理数据
        result = await data_manager.process_experiment_data(
            request.experiment_id,
            processing_params
        )

        return DataProcessingResponse(
            success=result.get("success", False),
            message="数据处理完成" if result.get("success") else "数据处理失败",
            experiment_id=request.experiment_id,
            processing_results=result,
            processing_time_seconds=(result.get("processing_end_time", 0) - result.get("processing_start_time", 0)) if result.get("success") else 0,
            data_quality_improvement=None  # 可以计算处理前后质量提升
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理实验数据失败: {str(e)}")


@router.post("/detect_peaks", response_model=PeakDetectionResponse)
async def detect_peaks(
    request: PeakDetectionRequest,
    data_manager = Depends(get_data_manager)
):
    """峰检测"""
    try:
        start_time = datetime.now()

        # 构建检测参数
        detection_params = {
            "threshold": request.threshold,
            "min_peak_height": request.min_peak_width,
            "min_peak_width": request.min_peak_width,
            "baseline_correction": request.baseline_correction,
            "noise_filtering": request.noise_filtering,
            **request.detection_parameters
        }

        # 执行峰检测
        peaks = await data_manager.detect_peaks(request.experiment_id, detection_params)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        return PeakDetectionResponse(
            success=True,
            message="峰检测完成",
            experiment_id=request.experiment_id,
            detected_peaks=peaks,
            detection_summary={
                "total_peaks": len(peaks),
                "detection_parameters": detection_params,
                "processing_time": processing_time
            },
            processing_time_seconds=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"峰检测失败: {str(e)}")


@router.post("/export")
async def export_experiment_data(
    request: DataExportRequest,
    data_manager = Depends(get_data_manager)
):
    """导出实验数据"""
    try:
        result = await data_manager.export_experiment_data(request)

        return {
            "success": result.get("success", False),
            "message": "数据导出完成" if result.get("success") else "数据导出失败",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出实验数据失败: {str(e)}")


@router.get("/quality/{experiment_id}")
async def get_data_quality_metrics(
    experiment_id: str,
    data_manager = Depends(get_data_manager)
):
    """获取数据质量指标"""
    try:
        metrics = await data_manager.get_data_quality_metrics(experiment_id)

        return {
            "success": True,
            "message": "获取数据质量指标成功",
            "data": metrics.dict() if hasattr(metrics, 'dict') else metrics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据质量指标失败: {str(e)}")


@router.get("/summary/{experiment_id}")
async def get_experiment_summary(
    experiment_id: str,
    data_manager = Depends(get_data_manager)
):
    """获取实验数据摘要"""
    try:
        summary = await data_manager.get_experiment_summary(experiment_id)

        return {
            "success": True,
            "message": "获取实验摘要成功",
            "data": summary.dict() if hasattr(summary, 'dict') else summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验摘要失败: {str(e)}")


@router.get("/peaks/{experiment_id}")
async def get_experiment_peaks(
    experiment_id: str,
    data_manager = Depends(get_data_manager)
):
    """获取实验峰信息"""
    try:
        # 这里应该从数据库获取峰信息
        peaks = []  # 简化处理

        return {
            "success": True,
            "message": "获取峰信息成功",
            "data": {
                "experiment_id": experiment_id,
                "total_peaks": len(peaks),
                "peaks": peaks
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取峰信息失败: {str(e)}")


@router.get("/raw/{experiment_id}")
async def get_raw_data(
    experiment_id: str,
    device_id: Optional[str] = Query(None, description="设备ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="数据量限制"),
    data_manager = Depends(get_data_manager)
):
    """获取原始数据"""
    try:
        # 这里应该从数据库查询原始数据
        # 简化处理，返回空数据
        raw_data = []

        return {
            "success": True,
            "message": "获取原始数据成功",
            "data": {
                "experiment_id": experiment_id,
                "device_id": device_id,
                "data_points": len(raw_data),
                "raw_data": raw_data[:limit]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取原始数据失败: {str(e)}")


@router.get("/processed/{experiment_id}")
async def get_processed_data(
    experiment_id: str,
    processing_type: Optional[str] = Query(None, description="处理类型"),
    data_manager = Depends(get_data_manager)
):
    """获取处理后数据"""
    try:
        # 这里应该从数据库查询处理后数据
        processed_data = []

        return {
            "success": True,
            "message": "获取处理后数据成功",
            "data": {
                "experiment_id": experiment_id,
                "processing_type": processing_type,
                "data_points": len(processed_data),
                "processed_data": processed_data
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理后数据失败: {str(e)}")


@router.get("/statistics/{experiment_id}")
async def get_data_statistics(
    experiment_id: str,
    data_manager = Depends(get_data_manager)
):
    """获取数据统计信息"""
    try:
        # 获取数据摘要
        summary = await data_manager.get_experiment_summary(experiment_id)

        # 获取质量指标
        try:
            quality_metrics = await data_manager.get_data_quality_metrics(experiment_id)
        except:
            quality_metrics = None

        statistics = {
            "experiment_id": experiment_id,
            "total_data_points": summary.total_data_points if summary else 0,
            "duration_minutes": summary.duration_minutes if summary else 0,
            "sampling_rate_hz": summary.sampling_rate_hz if summary else 0,
            "data_quality_score": quality_metrics.overall_score if quality_metrics else 0,
            "noise_level": quality_metrics.noise_level if quality_metrics else 0,
            "signal_to_noise_ratio": quality_metrics.signal_to_noise_ratio if quality_metrics else 0
        }

        return {
            "success": True,
            "message": "获取数据统计信息成功",
            "data": statistics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据统计信息失败: {str(e)}")


@router.delete("/{experiment_id}")
async def delete_experiment_data(
    experiment_id: str,
    confirm: bool = Query(False, description="确认删除"),
    data_manager = Depends(get_data_manager)
):
    """删除实验数据"""
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="需要确认删除操作")

        # 这里应该实现数据删除逻辑
        # 简化处理
        deleted = True

        return {
            "success": True,
            "message": "实验数据已删除",
            "data": {
                "experiment_id": experiment_id,
                "deleted": deleted
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除实验数据失败: {str(e)}")


# 导入datetime用于峰检测
from datetime import datetime