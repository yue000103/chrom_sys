"""
SMILES分子管理模型
SMILES Molecule Management Models
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base_models import BaseResponse
import re


class SMILESInfo(BaseModel):
    """SMILES分子信息模型"""
    smiles_id: Optional[int] = None
    smiles_description: str = Field(..., min_length=1, max_length=500, description="SMILES描述")
    smiles_string: Optional[str] = Field(None, description="SMILES字符串")
    molecular_formula: Optional[str] = Field(None, description="分子式")
    molecular_weight: Optional[float] = Field(None, gt=0, description="分子量")
    compound_name: Optional[str] = Field(None, max_length=200, description="化合物名称")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS号")

    # 审计信息
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('smiles_description')
    def validate_description(cls, v):
        """验证SMILES描述"""
        if not v or not v.strip():
            raise ValueError('SMILES描述不能为空')
        return v.strip()

    @validator('smiles_string')
    def validate_smiles_string(cls, v):
        """验证SMILES字符串格式"""
        if v is not None:
            v = v.strip()
            if v and not re.match(r'^[A-Za-z0-9\[\]()=#+\-\\/@.]*$', v):
                raise ValueError('SMILES字符串包含无效字符')
        return v

    @validator('molecular_weight')
    def validate_molecular_weight(cls, v):
        """验证分子量范围"""
        if v is not None and (v < 10 or v > 10000):
            raise ValueError('分子量应在10-10000范围内')
        return v

    @validator('cas_number')
    def validate_cas_number(cls, v):
        """验证CAS号格式"""
        if v is not None:
            v = v.strip()
            if v and not re.match(r'^\d{1,7}-\d{2}-\d$', v):
                raise ValueError('CAS号格式无效，应为XXXXXX-XX-X格式')
        return v


class CreateSMILESRequest(BaseModel):
    """创建SMILES分子请求模型"""
    smiles_description: str = Field(..., min_length=1, max_length=500, description="SMILES描述")
    smiles_string: Optional[str] = Field(None, description="SMILES字符串")
    molecular_formula: Optional[str] = Field(None, description="分子式")
    molecular_weight: Optional[float] = Field(None, gt=0, description="分子量")
    compound_name: Optional[str] = Field(None, max_length=200, description="化合物名称")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS号")


class UpdateSMILESRequest(BaseModel):
    """更新SMILES分子请求模型"""
    smiles_description: Optional[str] = Field(None, min_length=1, max_length=500)
    smiles_string: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = Field(None, gt=0)
    compound_name: Optional[str] = Field(None, max_length=200)
    cas_number: Optional[str] = Field(None, max_length=50)


class SMILESResponse(BaseResponse):
    """SMILES分子响应模型"""
    smiles: Dict[str, Any]


class SMILESListResponse(BaseResponse):
    """SMILES分子列表响应模型"""
    smiles_list: List[Dict[str, Any]]
    total_count: int


class SMILESStatistics(BaseModel):
    """SMILES分子统计信息模型"""
    total_smiles: int
    has_smiles_string: int
    has_molecular_formula: int
    has_molecular_weight: int
    has_cas_number: int
    average_molecular_weight: Optional[float]
    molecular_weight_distribution: Dict[str, int]  # 分子量范围分布
    recent_additions: int  # 最近30天新增
    timestamp: str


class SMILESStatisticsResponse(BaseResponse):
    """SMILES分子统计响应模型"""
    statistics: SMILESStatistics


class SMILESSearchQuery(BaseModel):
    """SMILES分子搜索查询模型"""
    search_term: Optional[str] = Field(None, description="搜索关键词(描述、化合物名称)")
    compound_name: Optional[str] = Field(None, description="化合物名称")
    cas_number: Optional[str] = Field(None, description="CAS号")
    has_smiles_string: Optional[bool] = Field(None, description="是否有SMILES字符串")
    has_molecular_formula: Optional[bool] = Field(None, description="是否有分子式")
    min_molecular_weight: Optional[float] = Field(None, gt=0, description="最小分子量")
    max_molecular_weight: Optional[float] = Field(None, gt=0, description="最大分子量")

    @validator('max_molecular_weight')
    def validate_weight_range(cls, v, values):
        """验证分子量范围"""
        if v is not None and 'min_molecular_weight' in values and values['min_molecular_weight'] is not None:
            if v < values['min_molecular_weight']:
                raise ValueError('最大分子量不能小于最小分子量')
        return v


class SMILESBatch(BaseModel):
    """SMILES分子批量操作模型"""
    smiles_ids: List[int] = Field(..., min_items=1, description="SMILES ID列表")
    operation: str = Field(..., description="操作类型: delete, export")
    options: Dict[str, Any] = Field(default_factory=dict, description="操作选项")


class SMILESBatchResponse(BaseResponse):
    """SMILES分子批量操作响应模型"""
    processed_count: int
    failed_count: int
    failed_items: List[Dict[str, Any]] = []
    results: Dict[str, Any] = {}


class SMILESImport(BaseModel):
    """SMILES分子导入模型"""
    file_type: str = Field(..., description="文件类型: csv, sdf, json")
    file_content: str = Field(..., description="文件内容(base64编码或直接内容)")
    import_options: Dict[str, Any] = Field(default_factory=dict, description="导入选项")
    overwrite_existing: bool = Field(False, description="是否覆盖现有记录")


class SMILESImportResponse(BaseResponse):
    """SMILES分子导入响应模型"""
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, str]] = []
    preview: List[Dict[str, Any]] = []  # 导入预览


class SMILESExport(BaseModel):
    """SMILES分子导出模型"""
    export_format: str = Field(..., description="导出格式: csv, sdf, json, xlsx")
    smiles_ids: Optional[List[int]] = Field(None, description="指定导出的SMILES ID列表")
    include_fields: List[str] = Field(default_factory=list, description="包含的字段")
    export_options: Dict[str, Any] = Field(default_factory=dict, description="导出选项")


class SMILESExportResponse(BaseResponse):
    """SMILES分子导出响应模型"""
    file_content: str  # base64编码的文件内容
    file_name: str
    file_size: int
    export_count: int


class SMILESValidation(BaseModel):
    """SMILES分子验证模型"""
    validation_id: Optional[str] = None
    smiles_id: int
    validation_type: str = Field(..., description="验证类型: structure, properties, database")
    validation_status: str = Field(..., description="验证状态: valid, invalid, warning")
    validation_date: str
    validation_results: Dict[str, Any] = {}
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    validated_by: str

    # 结构验证结果
    is_valid_smiles: Optional[bool] = None
    canonical_smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchi_key: Optional[str] = None

    # 性质验证结果
    calculated_molecular_weight: Optional[float] = None
    calculated_formula: Optional[str] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None