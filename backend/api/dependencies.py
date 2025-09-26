"""
API依赖注入工厂
API Dependency Injection Factories
"""

from typing import Optional
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from services.experiment_function_manager import ExperimentFunctionManager
from services.initialization_manager import InitializationManager
from services.experiment_data_manager import ExperimentDataManager
from services.method_manager import MethodManager
from services.tube_manager import TubeManager

# 全局实例（单例模式）
_mqtt_manager: Optional[MQTTManager] = None
_db_manager: Optional[DatabaseManager] = None
_experiment_manager: Optional[ExperimentFunctionManager] = None
_init_manager: Optional[InitializationManager] = None
_data_manager: Optional[ExperimentDataManager] = None
_method_manager: Optional[MethodManager] = None
_tube_manager: Optional[TubeManager] = None


def get_mqtt_manager() -> MQTTManager:
    """获取MQTT管理器实例"""
    global _mqtt_manager
    if _mqtt_manager is None:
        _mqtt_manager = MQTTManager()
    return _mqtt_manager


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_experiment_manager() -> ExperimentFunctionManager:
    """获取实验功能管理器实例"""
    global _experiment_manager
    if _experiment_manager is None:
        mqtt = get_mqtt_manager()
        db = get_db_manager()
        _experiment_manager = ExperimentFunctionManager(mqtt, db)
    return _experiment_manager


def get_init_manager() -> InitializationManager:
    """获取初始化管理器实例"""
    global _init_manager
    if _init_manager is None:
        mqtt = get_mqtt_manager()
        db = get_db_manager()
        _init_manager = InitializationManager(mqtt, db)
    return _init_manager


def get_data_manager() -> ExperimentDataManager:
    """获取实验数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        mqtt = get_mqtt_manager()
        _data_manager = ExperimentDataManager(mqtt)
    return _data_manager


def get_method_manager() -> MethodManager:
    """获取方法管理器实例"""
    global _method_manager
    if _method_manager is None:
        mqtt = get_mqtt_manager()
        db = get_db_manager()
        _method_manager = MethodManager(mqtt, db)
    return _method_manager


def get_tube_manager() -> TubeManager:
    """获取试管管理器实例"""
    global _tube_manager
    if _tube_manager is None:
        mqtt = get_mqtt_manager()
        db = get_db_manager()
        _tube_manager = TubeManager(mqtt, db)
    return _tube_manager


# 用于在应用启动时初始化服务
async def init_services():
    """初始化所有服务"""
    mqtt = get_mqtt_manager()
    await mqtt.connect()

    # 初始化其他服务...
    return True


# 用于在应用关闭时清理资源
async def cleanup_services():
    """清理所有服务"""
    if _mqtt_manager:
        await _mqtt_manager.disconnect()

    # 清理其他服务...
    return True