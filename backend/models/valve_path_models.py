"""
试管阀门路径配置数据模型
Tube Valve Path Configuration Data Models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class DeviceType(str, Enum):
    """设备类型枚举"""
    SOLENOID = "solenoid"           # 电磁阀
    MULTI_WAY = "multi_way"         # 多向阀
    BIDIRECTIONAL = "bidirectional" # 双向阀
    PUMP = "pump"                   # 泵


class ActionType(str, Enum):
    """动作类型枚举"""
    OPEN = "open"                   # 开启
    CLOSE = "close"                 # 关闭
    TURN_TO = "turn_to"             # 转到指定位置
    START = "start"                 # 启动
    STOP = "stop"                   # 停止


class ControllerType(str, Enum):
    """控制器类型枚举"""
    VALVE_CONTROLLER = "valve_controller"
    MULTI_VALVE_CONTROLLER = "multi_valve_controller"


# ===== 基础数据模型 =====

class TubeValvePath(BaseModel):
    """试管阀门路径模型"""
    path_id: Optional[int] = None
    module_number: int = Field(..., ge=1, description="模块号")
    tube_number: int = Field(..., ge=1, description="试管号")
    sequence_order: int = Field(..., ge=1, description="执行顺序")
    device_code: str = Field(..., min_length=1, max_length=50, description="设备编码")
    device_type: DeviceType = Field(..., description="设备类型")
    action_type: ActionType = Field(..., description="动作类型")
    target_position: Optional[int] = Field(None, ge=1, le=6, description="目标位置")
    description: Optional[str] = Field(None, max_length=200, description="操作描述")
    is_required: Optional[bool] = Field(True, description="是否必需")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('target_position')
    def validate_target_position(cls, v, values):
        """验证目标位置"""
        action_type = values.get('action_type')
        device_type = values.get('device_type')

        if action_type == ActionType.TURN_TO:
            if device_type == DeviceType.MULTI_WAY and v is None:
                raise ValueError("多向阀转动操作必须指定目标位置")
            if v is not None and (v < 1 or v > 6):
                raise ValueError("多向阀位置必须在1-6之间")

        return v


class DeviceMapping(BaseModel):
    """设备映射模型"""
    mapping_id: Optional[int] = None
    device_code: str = Field(..., min_length=1, max_length=50, description="设备编码")
    controller_type: ControllerType = Field(..., description="控制器类型")
    physical_id: str = Field(..., min_length=1, max_length=50, description="物理设备ID")
    controller_instance: Optional[str] = Field(None, max_length=50, description="控制器实例")
    device_description: Optional[str] = Field(None, max_length=200, description="设备描述")
    is_active: Optional[bool] = Field(True, description="是否激活")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ===== 请求模型 =====

class CreateTubePathRequest(BaseModel):
    """创建试管路径请求"""
    module_number: int = Field(..., ge=1, description="模块号")
    tube_number: int = Field(..., ge=1, description="试管号")
    path_steps: List[Dict[str, Any]] = Field(..., min_items=1, description="路径步骤")

    class Config:
        schema_extra = {
            "example": {
                "module_number": 1,
                "tube_number": 1,
                "path_steps": [
                    {
                        "sequence_order": 1,
                        "device_code": "双向阀1",
                        "device_type": "bidirectional",
                        "action_type": "open",
                        "description": "开启双向阀1"
                    },
                    {
                        "sequence_order": 2,
                        "device_code": "多向阀9",
                        "device_type": "multi_way",
                        "action_type": "turn_to",
                        "target_position": 1,
                        "description": "多向阀9转到位置1"
                    }
                ]
            }
        }


class UpdateTubePathRequest(BaseModel):
    """更新试管路径请求"""
    path_steps: Optional[List[Dict[str, Any]]] = Field(None, description="路径步骤")


class CreateDeviceMappingRequest(BaseModel):
    """创建设备映射请求"""
    device_code: str = Field(..., min_length=1, max_length=50)
    controller_type: ControllerType
    physical_id: str = Field(..., min_length=1, max_length=50)
    controller_instance: Optional[str] = Field(None, max_length=50)
    device_description: Optional[str] = Field(None, max_length=200)


class UpdateDeviceMappingRequest(BaseModel):
    """更新设备映射请求"""
    controller_type: Optional[ControllerType] = None
    physical_id: Optional[str] = Field(None, min_length=1, max_length=50)
    controller_instance: Optional[str] = Field(None, max_length=50)
    device_description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class TubePathQueryRequest(BaseModel):
    """试管路径查询请求"""
    module_number: Optional[int] = Field(None, ge=1)
    tube_number: Optional[int] = Field(None, ge=1)
    device_code: Optional[str] = Field(None, min_length=1)
    device_type: Optional[DeviceType] = None


# ===== 响应模型 =====

class TubePathResponse(BaseModel):
    """试管路径响应"""
    success: bool = True
    message: str = "操作成功"
    path: Optional[TubeValvePath] = None


class TubePathListResponse(BaseModel):
    """试管路径列表响应"""
    success: bool = True
    message: str = "获取试管路径列表成功"
    paths: List[TubeValvePath] = []
    total_count: int = 0


class TubePathDetailResponse(BaseModel):
    """试管路径详情响应"""
    success: bool = True
    message: str = "获取试管路径详情成功"
    module_number: int
    tube_number: int
    path_steps: List[TubeValvePath] = []
    total_steps: int = 0


class DeviceMappingResponse(BaseModel):
    """设备映射响应"""
    success: bool = True
    message: str = "操作成功"
    mapping: Optional[DeviceMapping] = None


class DeviceMappingListResponse(BaseModel):
    """设备映射列表响应"""
    success: bool = True
    message: str = "获取设备映射列表成功"
    mappings: List[DeviceMapping] = []
    total_count: int = 0


class PathExecutionStep(BaseModel):
    """路径执行步骤结果"""
    sequence_order: int
    device_code: str
    device_type: str
    action_type: str
    target_position: Optional[int] = None
    success: bool
    physical_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class PathExecutionResponse(BaseModel):
    """路径执行响应"""
    success: bool = True
    message: str = "路径执行完成"
    module_number: int
    tube_number: int
    total_steps: int = 0
    success_steps: int = 0
    execution_time: Optional[float] = None
    step_results: List[PathExecutionStep] = []


class TubePathSummaryResponse(BaseModel):
    """试管路径汇总响应"""
    success: bool = True
    message: str = "获取试管路径汇总成功"
    total_modules: int = 0
    total_tubes: int = 0
    total_paths: int = 0
    module_summary: List[Dict[str, Any]] = []


class DeviceStatusResponse(BaseModel):
    """设备状态响应"""
    success: bool = True
    message: str = "获取设备状态成功"
    device_code: str
    physical_id: str
    controller_type: str
    current_status: Dict[str, Any] = {}
    is_available: bool = True


# ===== 批量操作模型 =====

class BatchPathExecutionRequest(BaseModel):
    """批量路径执行请求"""
    tube_paths: List[Dict[str, int]] = Field(..., min_items=1, description="试管路径列表")

    class Config:
        schema_extra = {
            "example": {
                "tube_paths": [
                    {"module_number": 1, "tube_number": 1},
                    {"module_number": 1, "tube_number": 2},
                    {"module_number": 2, "tube_number": 1}
                ]
            }
        }


class BatchPathExecutionResponse(BaseModel):
    """批量路径执行响应"""
    success: bool = True
    message: str = "批量路径执行完成"
    total_paths: int = 0
    success_paths: int = 0
    failed_paths: int = 0
    execution_results: List[PathExecutionResponse] = []


# ===== 统计模型 =====

class PathStatistics(BaseModel):
    """路径统计信息"""
    total_modules: int = 0
    total_tubes: int = 0
    total_paths: int = 0
    total_steps: int = 0
    device_type_stats: Dict[str, int] = {}
    action_type_stats: Dict[str, int] = {}
    module_tube_distribution: Dict[str, int] = {}


class PathStatisticsResponse(BaseModel):
    """路径统计响应"""
    success: bool = True
    message: str = "获取路径统计信息成功"
    statistics: PathStatistics