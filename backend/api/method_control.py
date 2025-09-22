"""
方法控制API
Method Control API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
import logging

from pydantic import BaseModel, Field
from data.database_utils import ChromatographyDB

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== 数据模型 =====

class CreateMethodRequest(BaseModel):
    """创建方法请求"""
    method_name: str = Field(..., min_length=1, max_length=100, description="方法名称")
    column_id: int = Field(..., description="色谱柱ID")
    flow_rate_ml_min: int = Field(..., gt=0, description="流速(ml/min)")
    run_time_min: int = Field(..., gt=0, description="运行时间(分钟)")
    detector_wavelength: str = Field(..., description="检测器波长")
    peak_driven: bool = Field(False, description="是否峰驱动")
    gradient_elution_mode: str = Field("manual", description="梯度洗脱模式")
    gradient_time_table: Optional[str] = Field(None, description="梯度时间表")
    auto_gradient_params: Optional[str] = Field(None, description="自动梯度参数")

    class Config:
        schema_extra = {
            "example": {
                "method_name": "标准分析方法",
                "column_id": 1,
                "flow_rate_ml_min": 10,
                "run_time_min": 30,
                "detector_wavelength": "254nm",
                "peak_driven": False,
                "gradient_elution_mode": "manual",
                "gradient_time_table": "0:100,10:50,20:0",
                "auto_gradient_params": "linear"
            }
        }


class UpdateMethodRequest(BaseModel):
    """更新方法请求"""
    method_name: Optional[str] = Field(None, min_length=1, max_length=100, description="方法名称")
    column_id: Optional[int] = Field(None, description="色谱柱ID")
    flow_rate_ml_min: Optional[int] = Field(None, gt=0, description="流速(ml/min)")
    run_time_min: Optional[int] = Field(None, gt=0, description="运行时间(分钟)")
    detector_wavelength: Optional[str] = Field(None, description="检测器波长")
    peak_driven: Optional[bool] = Field(None, description="是否峰驱动")
    gradient_elution_mode: Optional[str] = Field(None, description="梯度洗脱模式")
    gradient_time_table: Optional[str] = Field(None, description="梯度时间表")
    auto_gradient_params: Optional[str] = Field(None, description="自动梯度参数")

    class Config:
        schema_extra = {
            "example": {
                "method_name": "更新的分析方法",
                "flow_rate_ml_min": 15,
                "run_time_min": 45
            }
        }


class MethodResponse(BaseModel):
    """方法响应"""
    success: bool = True
    message: str = "操作成功"
    method: Optional[dict] = None


class MethodListResponse(BaseModel):
    """方法列表响应"""
    success: bool = True
    message: str = "获取方法列表成功"
    methods: List[dict] = []
    total_count: int = 0


# ===== 依赖注入 =====

def get_database() -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB()


# ===== 方法管理API =====

@router.post("/", response_model=MethodResponse)
async def create_method(
    request: CreateMethodRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """创建新方法"""
    try:
        logger.info(f"创建新方法: {request.method_name}")

        # 调用数据库工具类添加方法
        success = db.add_method(
            method_name=request.method_name,
            column_id=request.column_id,
            flow_rate_ml_min=request.flow_rate_ml_min,
            run_time_min=request.run_time_min,
            detector_wavelength=request.detector_wavelength,
            peak_driven=request.peak_driven,
            gradient_elution_mode=request.gradient_elution_mode,
            gradient_time_table=request.gradient_time_table,
            auto_gradient_params=request.auto_gradient_params
        )

        if not success:
            raise HTTPException(status_code=500, detail="方法创建失败")

        # 获取新创建的方法信息
        methods = db.get_methods()
        new_method = methods[-1] if methods else None

        logger.info(f"方法创建成功: {request.method_name}")

        return MethodResponse(
            success=True,
            message=f"方法 '{request.method_name}' 创建成功",
            method=new_method
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建方法失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建方法失败: {str(e)}")


@router.get("/", response_model=MethodListResponse)
async def get_methods(
    method_name: Optional[str] = None,
    gradient_mode: Optional[str] = None,
    limit: Optional[int] = 50,
    db: ChromatographyDB = Depends(get_database)
):
    """获取方法列表"""
    try:
        logger.info(f"获取方法列表: name={method_name}, gradient_mode={gradient_mode}")

        # 获取方法列表
        methods = db.get_methods(
            method_name=method_name,
            gradient_mode=gradient_mode
        )

        # 应用限制
        if limit and len(methods) > limit:
            methods = methods[:limit]

        return MethodListResponse(
            success=True,
            message="获取方法列表成功",
            methods=methods,
            total_count=len(methods)
        )

    except Exception as e:
        logger.error(f"获取方法列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取方法列表失败: {str(e)}")


@router.get("/{method_id}", response_model=MethodResponse)
async def get_method_by_id(
    method_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """根据ID获取方法详情"""
    try:
        logger.info(f"获取方法详情: {method_id}")

        methods = db.get_methods(method_id=method_id)

        if not methods:
            raise HTTPException(status_code=404, detail=f"方法未找到: {method_id}")

        method = methods[0]

        return MethodResponse(
            success=True,
            message="获取方法详情成功",
            method=method
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取方法详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取方法详情失败: {str(e)}")


@router.put("/{method_id}", response_model=MethodResponse)
async def update_method(
    method_id: int,
    request: UpdateMethodRequest,
    db: ChromatographyDB = Depends(get_database)
):
    """更新方法"""
    try:
        logger.info(f"更新方法: {method_id}")

        # 检查方法是否存在
        existing_methods = db.get_methods(method_id=method_id)
        if not existing_methods:
            raise HTTPException(status_code=404, detail=f"方法未找到: {method_id}")

        # 准备更新数据（只更新提供的字段）
        update_data = {}

        if request.method_name is not None:
            update_data['method_name'] = request.method_name
        if request.column_id is not None:
            update_data['column_id'] = request.column_id
        if request.flow_rate_ml_min is not None:
            update_data['flow_rate_ml_min'] = request.flow_rate_ml_min
        if request.run_time_min is not None:
            update_data['run_time_min'] = request.run_time_min
        if request.detector_wavelength is not None:
            update_data['detector_wavelength'] = request.detector_wavelength
        if request.peak_driven is not None:
            update_data['peak_driven'] = 1 if request.peak_driven else 0
        if request.gradient_elution_mode is not None:
            update_data['gradient_elution_mode'] = request.gradient_elution_mode
        if request.gradient_time_table is not None:
            update_data['gradient_time_table'] = request.gradient_time_table
        if request.auto_gradient_params is not None:
            update_data['auto_gradient_params'] = request.auto_gradient_params

        # 添加更新时间
        update_data['updated_at'] = datetime.now().isoformat()

        # 执行更新
        success = db.update_method(method_id, **update_data)

        if not success:
            raise HTTPException(status_code=500, detail="方法更新失败")

        # 获取更新后的方法信息
        updated_methods = db.get_methods(method_id=method_id)
        updated_method = updated_methods[0] if updated_methods else None

        logger.info(f"方法更新成功: {method_id}")

        return MethodResponse(
            success=True,
            message=f"方法更新成功",
            method=updated_method
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新方法失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新方法失败: {str(e)}")


@router.delete("/{method_id}")
async def delete_method(
    method_id: int,
    db: ChromatographyDB = Depends(get_database)
):
    """删除方法"""
    try:
        logger.info(f"删除方法: {method_id}")

        # 检查方法是否存在
        existing_methods = db.get_methods(method_id=method_id)
        if not existing_methods:
            raise HTTPException(status_code=404, detail=f"方法未找到: {method_id}")

        method = existing_methods[0]

        # 删除方法
        success = db.delete_method(method_id)

        if not success:
            raise HTTPException(status_code=500, detail="方法删除失败")

        logger.info(f"方法删除成功: {method_id}")

        return {
            "success": True,
            "message": f"方法 '{method.get('method_name', method_id)}' 删除成功",
            "method_id": method_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除方法失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除方法失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "方法控制API运行正常"}