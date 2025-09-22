"""
色谱仪API路由
Chromatography API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from services.method_manager import MethodManager
from models.base_models import BaseResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ===== 请求模型 =====

class CreateMethodRequest(BaseModel):
    """创建方法请求模型"""
    method_name: str = Field(..., min_length=1, max_length=100, description="方法名称")
    column_id: int = Field(..., description="色谱柱ID")
    flow_rate_ml_min: int = Field(..., gt=0, description="流速 (ml/min)")
    run_time_min: int = Field(..., gt=0, description="运行时间 (分钟)")
    detector_wavelength: str = Field(..., description="检测器波长")
    peak_driven: bool = Field(default=False, description="是否峰驱动")
    gradient_elution_mode: str = Field(default="manual", description="梯度洗脱模式")
    gradient_time_table: Optional[str] = Field(None, description="梯度时间表")
    auto_gradient_params: Optional[str] = Field(None, description="自动梯度参数")

class UpdateMethodRequest(BaseModel):
    """更新方法请求模型"""
    method_name: Optional[str] = Field(None, min_length=1, max_length=100)
    column_id: Optional[int] = None
    flow_rate_ml_min: Optional[int] = Field(None, gt=0)
    run_time_min: Optional[int] = Field(None, gt=0)
    detector_wavelength: Optional[str] = None
    peak_driven: Optional[bool] = None
    gradient_elution_mode: Optional[str] = None
    gradient_time_table: Optional[str] = None
    auto_gradient_params: Optional[str] = None

class MethodListQuery(BaseModel):
    """方法列表查询参数"""
    method_name: Optional[str] = None
    gradient_mode: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

# ===== 响应模型 =====

class MethodResponse(BaseResponse):
    """方法响应模型"""
    method: Dict[str, Any]

class MethodListResponse(BaseResponse):
    """方法列表响应模型"""
    methods: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int

# ===== 依赖注入 =====

def get_method_manager() -> MethodManager:
    """获取方法管理器实例"""
    return MethodManager()

# ===== API路由 =====

@router.post("/method/create", response_model=BaseResponse)
async def create_method(
    request: CreateMethodRequest,
    method_manager: MethodManager = Depends(get_method_manager)
):
    """创建新方法"""
    try:
        logger.info(f"创建新方法: {request.method_name}")

        # 转换请求数据为字典
        method_data = request.dict(exclude_unset=True)

        # 调用服务层创建方法
        success = method_manager.create_method(method_data)

        if success:
            return BaseResponse(
                success=True,
                message=f"方法 '{request.method_name}' 创建成功"
            )
        else:
            raise HTTPException(status_code=400, detail="方法创建失败")

    except Exception as e:
        logger.error(f"创建方法时出错: {e}")
        raise HTTPException(status_code=500, detail=f"创建方法失败: {str(e)}")

@router.get("/method/list", response_model=MethodListResponse)
async def list_methods(
    method_name: Optional[str] = None,
    gradient_mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    method_manager: MethodManager = Depends(get_method_manager)
):
    """获取方法列表"""
    try:
        logger.info(f"查询方法列表: name={method_name}, gradient_mode={gradient_mode}")

        # 调用服务层获取方法列表
        methods = method_manager.list_methods(
            method_name=method_name,
            gradient_mode=gradient_mode,
            limit=limit,
            offset=offset
        )

        return MethodListResponse(
            success=True,
            message="获取方法列表成功",
            methods=methods,
            total_count=len(methods),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"获取方法列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取方法列表失败: {str(e)}")

@router.get("/method/{method_id}", response_model=MethodResponse)
async def get_method(
    method_id: int,
    method_manager: MethodManager = Depends(get_method_manager)
):
    """获取特定方法"""
    try:
        logger.info(f"获取方法: {method_id}")

        # 调用服务层获取方法
        method = method_manager.get_method(method_id)

        if method:
            return MethodResponse(
                success=True,
                message="获取方法成功",
                method=method
            )
        else:
            raise HTTPException(status_code=404, detail=f"方法不存在: {method_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取方法时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取方法失败: {str(e)}")

@router.put("/method/{method_id}", response_model=BaseResponse)
async def update_method(
    method_id: int,
    request: UpdateMethodRequest,
    method_manager: MethodManager = Depends(get_method_manager)
):
    """更新方法"""
    try:
        logger.info(f"更新方法: {method_id}")

        # 转换请求数据为字典，排除None值
        updates = request.dict(exclude_unset=True, exclude_none=True)

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        # 调用服务层更新方法
        success = method_manager.update_method(method_id, updates)

        if success:
            return BaseResponse(
                success=True,
                message=f"方法 {method_id} 更新成功"
            )
        else:
            raise HTTPException(status_code=400, detail="方法更新失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新方法时出错: {e}")
        raise HTTPException(status_code=500, detail=f"更新方法失败: {str(e)}")

@router.delete("/method/{method_id}", response_model=BaseResponse)
async def delete_method(
    method_id: int,
    method_manager: MethodManager = Depends(get_method_manager)
):
    """删除方法"""
    try:
        logger.info(f"删除方法: {method_id}")

        # 调用服务层删除方法
        success = method_manager.delete_method(method_id)

        if success:
            return BaseResponse(
                success=True,
                message=f"方法 {method_id} 删除成功"
            )
        else:
            raise HTTPException(status_code=400, detail="方法删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除方法时出错: {e}")
        raise HTTPException(status_code=500, detail=f"删除方法失败: {str(e)}")

# ===== 原有接口 (保持兼容性) =====

@router.post("/workflow/start")
async def start_chromatography_workflow(workflow_params: Dict[str, Any]):
    """开始色谱工作流"""
    # ChromatographyWorkflow.start implementation
    return {"status": "started", "workflow_id": "workflow_001"}

@router.post("/sample/inject")
async def inject_sample(sample_params: Dict[str, Any]):
    """注射样品"""
    # ChromatographyWorkflow.run_sample_injection implementation
    return {"status": "injected", "sample_id": sample_params.get("sample_id")}