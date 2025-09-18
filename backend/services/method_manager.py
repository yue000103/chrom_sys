"""
方法管理器
Method Manager
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.method_models import (
    AnalysisMethod,
    MethodValidation,
    MethodTemplate,
    MethodHistory,
    MethodType,
    MethodStatus
)
from core.database import DatabaseManager
from core.mqtt_manager import MQTTManager

logger = logging.getLogger(__name__)


class MethodManager:
    """分析方法管理器"""

    def __init__(self, db_manager: DatabaseManager, mqtt_manager: MQTTManager):
        self.db_manager = db_manager
        self.mqtt_manager = mqtt_manager
        self.methods_cache: Dict[str, AnalysisMethod] = {}

    async def create_method(self, method_data: Dict[str, Any], created_by: str) -> AnalysisMethod:
        """创建新的分析方法"""
        logger.info(f"创建新方法: {method_data.get('method_name')}")

        # 创建方法对象
        method = AnalysisMethod(
            created_by=created_by,
            **method_data
        )

        # 验证方法
        validation_result = await self.validate_method(method)
        if not validation_result["valid"]:
            raise ValueError(f"方法验证失败: {validation_result['errors']}")

        # 保存到数据库 (这里需要实现数据库保存逻辑)
        # 目前先保存到缓存
        self.methods_cache[method.method_id] = method

        # 记录历史
        await self._log_method_history(
            method.method_id,
            "created",
            "创建新方法",
            created_by
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "methods/created",
            {
                "method_id": method.method_id,
                "method_name": method.method_name,
                "created_by": created_by,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"方法创建成功: {method.method_id}")
        return method

    async def update_method(self, method_id: str, updates: Dict[str, Any], modified_by: str) -> AnalysisMethod:
        """更新分析方法"""
        logger.info(f"更新方法: {method_id}")

        # 获取现有方法
        method = await self.get_method(method_id)
        if not method:
            raise ValueError(f"方法不存在: {method_id}")

        # 检查权限 (简化版本)
        if method.method_status == MethodStatus.ARCHIVED:
            raise ValueError("已归档的方法不能修改")

        # 保存修改前状态
        old_version = method.version
        changes_made = updates.copy()

        # 应用更新
        for key, value in updates.items():
            if hasattr(method, key):
                setattr(method, key, value)

        # 更新元数据
        method.modified_by = modified_by
        method.modified_at = datetime.now()
        method.version = self._increment_version(method.version)

        # 重新验证
        validation_result = await self.validate_method(method)
        if not validation_result["valid"]:
            raise ValueError(f"更新后方法验证失败: {validation_result['errors']}")

        # 保存更新
        self.methods_cache[method_id] = method

        # 记录历史
        await self._log_method_history(
            method_id,
            "modified",
            "方法已更新",
            modified_by,
            changes_made,
            old_version,
            method.version
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "methods/updated",
            {
                "method_id": method_id,
                "modified_by": modified_by,
                "version": method.version,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"方法更新成功: {method_id}")
        return method

    async def get_method(self, method_id: str) -> Optional[AnalysisMethod]:
        """获取单个方法"""
        # 先从缓存获取
        if method_id in self.methods_cache:
            return self.methods_cache[method_id]

        # 从数据库获取 (这里需要实现数据库查询逻辑)
        # 目前返回None
        return None

    async def list_methods(
        self,
        method_type: Optional[MethodType] = None,
        status: Optional[MethodStatus] = None,
        created_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalysisMethod]:
        """列出方法"""
        logger.info(f"查询方法列表: type={method_type}, status={status}")

        # 从缓存获取 (实际应从数据库查询)
        methods = list(self.methods_cache.values())

        # 应用过滤器
        if method_type:
            methods = [m for m in methods if m.method_type == method_type]
        if status:
            methods = [m for m in methods if m.method_status == status]
        if created_by:
            methods = [m for m in methods if m.created_by == created_by]

        # 应用分页
        return methods[offset:offset + limit]

    async def delete_method(self, method_id: str, deleted_by: str) -> bool:
        """删除方法"""
        logger.info(f"删除方法: {method_id}")

        method = await self.get_method(method_id)
        if not method:
            raise ValueError(f"方法不存在: {method_id}")

        # 检查是否可以删除
        if method.usage_count > 0:
            raise ValueError("已使用的方法不能删除，只能归档")

        # 从缓存移除
        self.methods_cache.pop(method_id, None)

        # 记录历史
        await self._log_method_history(
            method_id,
            "deleted",
            "方法已删除",
            deleted_by
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "methods/deleted",
            {
                "method_id": method_id,
                "deleted_by": deleted_by,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"方法删除成功: {method_id}")
        return True

    async def archive_method(self, method_id: str, archived_by: str) -> bool:
        """归档方法"""
        logger.info(f"归档方法: {method_id}")

        method = await self.get_method(method_id)
        if not method:
            raise ValueError(f"方法不存在: {method_id}")

        # 更新状态
        method.method_status = MethodStatus.ARCHIVED
        method.modified_by = archived_by
        method.modified_at = datetime.now()

        # 保存更新
        self.methods_cache[method_id] = method

        # 记录历史
        await self._log_method_history(
            method_id,
            "archived",
            "方法已归档",
            archived_by
        )

        return True

    async def validate_method(self, method: AnalysisMethod) -> Dict[str, Any]:
        """验证方法"""
        errors = []
        warnings = []

        # 基本验证
        if not method.method_name:
            errors.append("方法名称不能为空")

        if not method.gradient_program:
            errors.append("梯度程序不能为空")

        if not method.tube_sequence:
            errors.append("试管序列不能为空")

        # 运行时间验证
        if method.run_time_minutes <= 0:
            errors.append("运行时间必须大于0")

        # 温度范围验证
        if method.column_temperature_celsius < 4 or method.column_temperature_celsius > 80:
            errors.append("柱温必须在4-80°C范围内")

        # 注射体积验证
        if method.injection_volume_ul <= 0:
            errors.append("注射体积必须大于0")

        # 警告检查
        if method.run_time_minutes > 120:
            warnings.append("运行时间超过2小时，可能影响效率")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def copy_method(self, source_method_id: str, new_name: str, copied_by: str) -> AnalysisMethod:
        """复制方法"""
        logger.info(f"复制方法: {source_method_id} -> {new_name}")

        source_method = await self.get_method(source_method_id)
        if not source_method:
            raise ValueError(f"源方法不存在: {source_method_id}")

        # 创建新方法ID
        import uuid
        new_method_id = f"method_{uuid.uuid4().hex[:8]}"

        # 复制方法数据
        method_data = source_method.dict()
        method_data.update({
            "method_id": new_method_id,
            "method_name": new_name,
            "version": "1.0",
            "usage_count": 0,
            "last_used": None
        })

        # 创建新方法
        new_method = await self.create_method(method_data, copied_by)

        logger.info(f"方法复制成功: {new_method_id}")
        return new_method

    async def get_method_usage_stats(self, method_id: str) -> Dict[str, Any]:
        """获取方法使用统计"""
        method = await self.get_method(method_id)
        if not method:
            raise ValueError(f"方法不存在: {method_id}")

        # 这里应该从数据库查询实际使用统计
        return {
            "method_id": method_id,
            "usage_count": method.usage_count,
            "last_used": method.last_used,
            "success_rate": 0.95,  # 模拟数据
            "avg_duration_minutes": 45,  # 模拟数据
            "total_experiments": method.usage_count
        }

    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                return "1.1"
        except:
            return "1.1"

    async def _log_method_history(
        self,
        method_id: str,
        action_type: str,
        description: str,
        performed_by: str,
        changes_made: Optional[Dict[str, Any]] = None,
        previous_version: Optional[str] = None,
        new_version: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """记录方法历史"""
        try:
            # 这里应该保存到数据库的方法历史表
            history = MethodHistory(
                history_id=f"hist_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                method_id=method_id,
                action_type=action_type,
                action_description=description,
                changes_made=changes_made or {},
                previous_version=previous_version,
                new_version=new_version,
                performed_by=performed_by,
                performed_at=datetime.now(),
                reason=reason
            )

            # 记录到系统日志
            await self.db_manager.log_system_event(
                "method_history",
                "info",
                "method_manager",
                description,
                history.dict()
            )

        except Exception as e:
            logger.error(f"记录方法历史失败: {e}")

    async def search_methods(self, query: str, limit: int = 20) -> List[AnalysisMethod]:
        """搜索方法"""
        logger.info(f"搜索方法: {query}")

        # 简单的搜索实现
        methods = list(self.methods_cache.values())
        results = []

        query_lower = query.lower()
        for method in methods:
            if (query_lower in method.method_name.lower() or
                query_lower in method.description.lower() or
                query_lower in method.application.lower()):
                results.append(method)

        return results[:limit]