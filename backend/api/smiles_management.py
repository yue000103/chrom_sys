"""
SMILES分子管理API
SMILES Molecule Management API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from services.smiles_manager import SMILESManager
from models.smiles_models import (
    CreateSMILESRequest, UpdateSMILESRequest, SMILESSearchQuery,
    SMILESResponse, SMILESListResponse, SMILESStatisticsResponse,
    SMILESBatch, SMILESBatchResponse
)

router = APIRouter()

# ===== 依赖注入 =====

def get_smiles_manager() -> SMILESManager:
    """获取SMILES分子管理器实例"""
    return SMILESManager()

# ===== SMILES分子API路由 =====

@router.get("/", response_model=SMILESListResponse)
async def get_all_smiles(
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """获取所有SMILES分子信息"""
    try:
        smiles_list = smiles_manager.get_all_smiles()
        return SMILESListResponse(
            success=True,
            message="获取SMILES分子列表成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SMILES分子列表失败: {str(e)}")


@router.get("/search", response_model=SMILESListResponse)
async def search_smiles(
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    compound_name: Optional[str] = Query(None, description="化合物名称"),
    cas_number: Optional[str] = Query(None, description="CAS号"),
    has_smiles_string: Optional[bool] = Query(None, description="是否有SMILES字符串"),
    has_molecular_formula: Optional[bool] = Query(None, description="是否有分子式"),
    min_molecular_weight: Optional[float] = Query(None, ge=0, description="最小分子量"),
    max_molecular_weight: Optional[float] = Query(None, ge=0, description="最大分子量"),
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """搜索SMILES分子"""
    try:
        smiles_list = smiles_manager.search_smiles(
            search_term=search_term,
            compound_name=compound_name,
            cas_number=cas_number,
            has_smiles_string=has_smiles_string,
            has_molecular_formula=has_molecular_formula,
            min_molecular_weight=min_molecular_weight,
            max_molecular_weight=max_molecular_weight
        )
        return SMILESListResponse(
            success=True,
            message="搜索SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索SMILES分子失败: {str(e)}")


@router.get("/statistics", response_model=SMILESStatisticsResponse)
async def get_smiles_statistics(
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """获取SMILES分子统计信息"""
    try:
        statistics = smiles_manager.get_smiles_statistics()
        return SMILESStatisticsResponse(
            success=True,
            message="获取SMILES分子统计信息成功",
            statistics=statistics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SMILES分子统计信息失败: {str(e)}")


@router.get("/{smiles_id}", response_model=SMILESResponse)
async def get_smiles_by_id(
    smiles_id: int,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """根据ID获取特定SMILES分子信息"""
    try:
        smiles = smiles_manager.get_smiles_by_id(smiles_id)
        if smiles:
            return SMILESResponse(
                success=True,
                message="获取SMILES分子信息成功",
                smiles=smiles
            )
        else:
            raise HTTPException(status_code=404, detail=f"SMILES分子不存在: {smiles_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SMILES分子信息失败: {str(e)}")


@router.post("/", response_model=SMILESResponse)
async def create_smiles(
    request: CreateSMILESRequest,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """创建新的SMILES分子"""
    try:
        smiles_data = request.dict(exclude_unset=True)
        success = smiles_manager.create_smiles(smiles_data)

        if success:
            return SMILESResponse(
                success=True,
                message=f"SMILES分子 '{request.smiles_description}' 创建成功",
                smiles={"smiles_description": request.smiles_description}
            )
        else:
            raise HTTPException(status_code=400, detail="SMILES分子创建失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建SMILES分子失败: {str(e)}")


@router.put("/{smiles_id}", response_model=SMILESResponse)
async def update_smiles(
    smiles_id: int,
    request: UpdateSMILESRequest,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """更新SMILES分子信息"""
    try:
        updates = request.dict(exclude_unset=True, exclude_none=True)

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        success = smiles_manager.update_smiles(smiles_id, updates)

        if success:
            # 获取更新后的SMILES分子信息
            updated_smiles = smiles_manager.get_smiles_by_id(smiles_id)
            return SMILESResponse(
                success=True,
                message=f"SMILES分子 {smiles_id} 更新成功",
                smiles=updated_smiles or {"smiles_id": smiles_id}
            )
        else:
            raise HTTPException(status_code=400, detail="SMILES分子更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新SMILES分子失败: {str(e)}")


@router.delete("/{smiles_id}")
async def delete_smiles(
    smiles_id: int,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """删除SMILES分子"""
    try:
        success = smiles_manager.delete_smiles(smiles_id)

        if success:
            return {
                "success": True,
                "message": f"SMILES分子 {smiles_id} 删除成功"
            }
        else:
            raise HTTPException(status_code=400, detail="SMILES分子删除失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除SMILES分子失败: {str(e)}")


# ===== 高级功能 =====

@router.post("/search/advanced", response_model=SMILESListResponse)
async def advanced_search_smiles(
    query: SMILESSearchQuery,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """高级搜索SMILES分子"""
    try:
        smiles_list = smiles_manager.search_smiles(
            search_term=query.search_term,
            compound_name=query.compound_name,
            cas_number=query.cas_number,
            has_smiles_string=query.has_smiles_string,
            has_molecular_formula=query.has_molecular_formula,
            min_molecular_weight=query.min_molecular_weight,
            max_molecular_weight=query.max_molecular_weight
        )

        return SMILESListResponse(
            success=True,
            message="高级搜索SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"高级搜索SMILES分子失败: {str(e)}")


@router.post("/batch", response_model=SMILESBatchResponse)
async def batch_operation_smiles(
    batch: SMILESBatch,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """批量操作SMILES分子"""
    try:
        if batch.operation == "delete":
            result = smiles_manager.batch_delete_smiles(batch.smiles_ids)
            return SMILESBatchResponse(
                success=True,
                message=f"批量删除操作完成",
                processed_count=result['processed_count'],
                failed_count=result['failed_count'],
                failed_items=result['failed_items']
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的批量操作: {batch.operation}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")


@router.get("/compound/{compound_name}", response_model=SMILESListResponse)
async def get_smiles_by_compound_name(
    compound_name: str,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """根据化合物名称获取SMILES分子"""
    try:
        smiles_list = smiles_manager.get_smiles_by_compound_name(compound_name)
        return SMILESListResponse(
            success=True,
            message=f"根据化合物名称查找SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找SMILES分子失败: {str(e)}")


@router.post("/validate/smiles-string")
async def validate_smiles_string(
    smiles_string: str = Query(..., description="要验证的SMILES字符串"),
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """验证SMILES字符串"""
    try:
        result = smiles_manager.validate_smiles_string(smiles_string)
        return {
            "success": True,
            "message": "SMILES字符串验证完成",
            "validation_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证SMILES字符串失败: {str(e)}")


@router.get("/by-cas/{cas_number}", response_model=SMILESListResponse)
async def get_smiles_by_cas_number(
    cas_number: str,
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """根据CAS号获取SMILES分子"""
    try:
        smiles_list = smiles_manager.search_smiles(cas_number=cas_number)
        return SMILESListResponse(
            success=True,
            message=f"根据CAS号查找SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找SMILES分子失败: {str(e)}")


@router.get("/molecular-weight-range")
async def get_smiles_by_molecular_weight_range(
    min_weight: float = Query(..., ge=0, description="最小分子量"),
    max_weight: float = Query(..., ge=0, description="最大分子量"),
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """根据分子量范围获取SMILES分子"""
    try:
        if min_weight > max_weight:
            raise HTTPException(status_code=400, detail="最小分子量不能大于最大分子量")

        smiles_list = smiles_manager.search_smiles(
            min_molecular_weight=min_weight,
            max_molecular_weight=max_weight
        )

        return SMILESListResponse(
            success=True,
            message=f"根据分子量范围({min_weight}-{max_weight})查找SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找SMILES分子失败: {str(e)}")


@router.get("/incomplete/missing-data")
async def get_incomplete_smiles(
    missing_field: str = Query(..., description="缺失字段: smiles_string, molecular_formula, molecular_weight, cas_number"),
    smiles_manager: SMILESManager = Depends(get_smiles_manager)
):
    """获取数据不完整的SMILES分子"""
    try:
        field_mapping = {
            'smiles_string': False,
            'molecular_formula': False,
            'molecular_weight': False,
        }

        if missing_field not in ['smiles_string', 'molecular_formula', 'molecular_weight', 'cas_number']:
            raise HTTPException(status_code=400, detail="无效的缺失字段参数")

        search_params = {}
        if missing_field in field_mapping:
            search_params[f'has_{missing_field}'] = False

        smiles_list = smiles_manager.search_smiles(**search_params)

        # 对于CAS号，需要特殊处理
        if missing_field == 'cas_number':
            all_smiles = smiles_manager.get_all_smiles()
            smiles_list = [s for s in all_smiles if not s.get('cas_number')]

        return SMILESListResponse(
            success=True,
            message=f"获取缺失{missing_field}的SMILES分子成功",
            smiles_list=smiles_list,
            total_count=len(smiles_list)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取不完整SMILES分子失败: {str(e)}")