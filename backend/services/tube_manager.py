"""
试管管理器
Tube Manager
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.tube_models import (
    TubeInfo,
    TubeSequence,
    TubeOperation,
    TubePosition,
    TubeRack,
    TubeBatch,
    TubeStatus,
    TubeType
)
from core.database import DatabaseManager
from core.mqtt_manager import MQTTManager

logger = logging.getLogger(__name__)


class TubeManager:
    """试管管理器"""

    def __init__(self, db_manager: DatabaseManager, mqtt_manager: MQTTManager):
        self.db_manager = db_manager
        self.mqtt_manager = mqtt_manager
        self.tubes_cache: Dict[str, TubeInfo] = {}
        self.racks_cache: Dict[str, TubeRack] = {}
        self.operations_queue: List[TubeOperation] = []
        self.current_operation: Optional[TubeOperation] = None

    async def register_tube(self, tube_info: TubeInfo) -> bool:
        """注册试管"""
        logger.info(f"注册试管: {tube_info.tube_id}")

        # 检查位置是否已被占用
        position_occupied = await self._check_position_occupied(tube_info.position)
        if position_occupied:
            raise ValueError(f"位置已被占用: {tube_info.position}")

        # 保存试管信息
        self.tubes_cache[tube_info.tube_id] = tube_info

        # 更新试管架占用状态
        await self._update_rack_occupancy(tube_info.position.rack_id, 1)

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "tubes/registered",
            {
                "tube_id": tube_info.tube_id,
                "position": tube_info.position.dict(),
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"试管注册成功: {tube_info.tube_id}")
        return True

    async def update_tube_status(self, tube_id: str, new_status: TubeStatus, operator: str) -> bool:
        """更新试管状态"""
        tube = self.tubes_cache.get(tube_id)
        if not tube:
            raise ValueError(f"试管不存在: {tube_id}")

        old_status = tube.tube_status
        tube.tube_status = new_status

        # 记录状态变更
        await self._log_tube_event(
            tube_id,
            "status_updated",
            {
                "old_status": old_status,
                "new_status": new_status,
                "operator": operator
            }
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "tubes/status_updated",
            {
                "tube_id": tube_id,
                "old_status": old_status,
                "new_status": new_status,
                "operator": operator,
                "timestamp": datetime.now().isoformat()
            }
        )

        return True

    async def move_tube(self, tube_id: str, target_position: TubePosition, operator: str) -> TubeOperation:
        """移动试管"""
        logger.info(f"移动试管: {tube_id} -> {target_position}")

        tube = self.tubes_cache.get(tube_id)
        if not tube:
            raise ValueError(f"试管不存在: {tube_id}")

        # 检查目标位置是否可用
        position_occupied = await self._check_position_occupied(target_position)
        if position_occupied:
            raise ValueError(f"目标位置已被占用: {target_position}")

        # 创建移动操作
        import uuid
        operation = TubeOperation(
            operation_id=f"op_{uuid.uuid4().hex[:8]}",
            tube_id=tube_id,
            operation_type="move",
            source_position=tube.position,
            target_position=target_position,
            operator=operator,
            status="pending"
        )

        # 添加到操作队列
        await self.queue_operation(operation)

        return operation

    async def pickup_tube(self, tube_id: str, operator: str) -> TubeOperation:
        """拾取试管"""
        logger.info(f"拾取试管: {tube_id}")

        tube = self.tubes_cache.get(tube_id)
        if not tube:
            raise ValueError(f"试管不存在: {tube_id}")

        if tube.tube_status == TubeStatus.IN_USE:
            raise ValueError(f"试管正在使用中: {tube_id}")

        # 创建拾取操作
        import uuid
        operation = TubeOperation(
            operation_id=f"op_{uuid.uuid4().hex[:8]}",
            tube_id=tube_id,
            operation_type="pickup",
            source_position=tube.position,
            operator=operator,
            status="pending"
        )

        # 添加到操作队列
        await self.queue_operation(operation)

        return operation

    async def inject_sample(self, tube_id: str, volume_ul: float, operator: str) -> TubeOperation:
        """进样操作"""
        logger.info(f"进样操作: {tube_id}, 体积: {volume_ul}μL")

        tube = self.tubes_cache.get(tube_id)
        if not tube:
            raise ValueError(f"试管不存在: {tube_id}")

        # 检查剩余体积
        remaining = tube.remaining_volume_ul or tube.volume_ul
        if remaining < volume_ul:
            raise ValueError(f"试管剩余体积不足: {remaining}μL < {volume_ul}μL")

        # 创建进样操作
        import uuid
        operation = TubeOperation(
            operation_id=f"op_{uuid.uuid4().hex[:8]}",
            tube_id=tube_id,
            operation_type="inject",
            volume_ul=volume_ul,
            parameters={"injection_volume": volume_ul},
            operator=operator,
            status="pending"
        )

        # 添加到操作队列
        await self.queue_operation(operation)

        return operation

    async def wash_needle(self, wash_volume_ul: float, operator: str) -> TubeOperation:
        """清洗针头"""
        logger.info(f"清洗针头: {wash_volume_ul}μL")

        # 创建清洗操作
        import uuid
        operation = TubeOperation(
            operation_id=f"op_{uuid.uuid4().hex[:8]}",
            tube_id="system",
            operation_type="wash",
            volume_ul=wash_volume_ul,
            parameters={"wash_volume": wash_volume_ul},
            operator=operator,
            status="pending"
        )

        # 添加到操作队列
        await self.queue_operation(operation)

        return operation

    async def queue_operation(self, operation: TubeOperation):
        """将操作加入队列"""
        self.operations_queue.append(operation)

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "tubes/operation_queued",
            {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "tube_id": operation.tube_id,
                "queue_position": len(self.operations_queue),
                "timestamp": datetime.now().isoformat()
            }
        )

        # 如果没有正在执行的操作，立即开始执行
        if not self.current_operation:
            await self._execute_next_operation()

    async def _execute_next_operation(self):
        """执行下一个操作"""
        if not self.operations_queue:
            return

        operation = self.operations_queue.pop(0)
        self.current_operation = operation

        try:
            # 更新操作状态
            operation.status = "running"
            operation.start_time = datetime.now()

            # 发布开始执行消息
            await self.mqtt_manager.publish_data(
                "tubes/operation_started",
                {
                    "operation_id": operation.operation_id,
                    "operation_type": operation.operation_type,
                    "tube_id": operation.tube_id,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 执行具体操作
            success = await self._perform_operation(operation)

            # 更新操作状态
            operation.status = "completed" if success else "failed"
            operation.end_time = datetime.now()

            if success:
                logger.info(f"操作执行成功: {operation.operation_id}")
            else:
                logger.error(f"操作执行失败: {operation.operation_id}")

            # 发布完成消息
            await self.mqtt_manager.publish_data(
                "tubes/operation_completed",
                {
                    "operation_id": operation.operation_id,
                    "operation_type": operation.operation_type,
                    "tube_id": operation.tube_id,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"操作执行异常: {e}")
            operation.status = "failed"
            operation.error_message = str(e)
            operation.end_time = datetime.now()

        finally:
            # 清除当前操作
            self.current_operation = None

            # 记录操作日志
            await self._log_tube_event(
                operation.tube_id,
                "operation_completed",
                operation.dict()
            )

            # 继续执行下一个操作
            if self.operations_queue:
                await self._execute_next_operation()

    async def _perform_operation(self, operation: TubeOperation) -> bool:
        """执行具体操作"""
        try:
            if operation.operation_type == "move":
                return await self._perform_move(operation)
            elif operation.operation_type == "pickup":
                return await self._perform_pickup(operation)
            elif operation.operation_type == "inject":
                return await self._perform_inject(operation)
            elif operation.operation_type == "wash":
                return await self._perform_wash(operation)
            else:
                logger.error(f"不支持的操作类型: {operation.operation_type}")
                return False
        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            return False

    async def _perform_move(self, operation: TubeOperation) -> bool:
        """执行移动操作"""
        # 模拟移动操作
        import asyncio
        await asyncio.sleep(2)  # 模拟移动时间

        # 更新试管位置
        tube = self.tubes_cache.get(operation.tube_id)
        if tube and operation.target_position:
            old_rack = tube.position.rack_id
            new_rack = operation.target_position.rack_id

            tube.position = operation.target_position

            # 更新试管架占用状态
            if old_rack != new_rack:
                await self._update_rack_occupancy(old_rack, -1)
                await self._update_rack_occupancy(new_rack, 1)

        return True

    async def _perform_pickup(self, operation: TubeOperation) -> bool:
        """执行拾取操作"""
        import asyncio
        await asyncio.sleep(1)  # 模拟拾取时间

        # 更新试管状态
        tube = self.tubes_cache.get(operation.tube_id)
        if tube:
            tube.tube_status = TubeStatus.IN_USE

        return True

    async def _perform_inject(self, operation: TubeOperation) -> bool:
        """执行进样操作"""
        import asyncio
        await asyncio.sleep(3)  # 模拟进样时间

        # 更新试管剩余体积
        tube = self.tubes_cache.get(operation.tube_id)
        if tube and operation.volume_ul:
            remaining = tube.remaining_volume_ul or tube.volume_ul
            tube.remaining_volume_ul = remaining - operation.volume_ul

            # 如果体积用完，更新状态
            if tube.remaining_volume_ul <= 0:
                tube.tube_status = TubeStatus.PROCESSED

        return True

    async def _perform_wash(self, operation: TubeOperation) -> bool:
        """执行清洗操作"""
        import asyncio
        await asyncio.sleep(1)  # 模拟清洗时间
        return True

    async def get_tube_info(self, tube_id: str) -> Optional[TubeInfo]:
        """获取试管信息"""
        return self.tubes_cache.get(tube_id)

    async def list_tubes_by_rack(self, rack_id: str) -> List[TubeInfo]:
        """按试管架列出试管"""
        return [tube for tube in self.tubes_cache.values()
                if tube.position.rack_id == rack_id]

    async def get_operation_queue_status(self) -> Dict[str, Any]:
        """获取操作队列状态"""
        return {
            "queue_length": len(self.operations_queue),
            "current_operation": self.current_operation.dict() if self.current_operation else None,
            "queued_operations": [op.dict() for op in self.operations_queue[:5]]  # 显示前5个
        }

    async def _check_position_occupied(self, position: TubePosition) -> bool:
        """检查位置是否被占用"""
        for tube in self.tubes_cache.values():
            if (tube.position.rack_id == position.rack_id and
                tube.position.position_number == position.position_number):
                return True
        return False

    async def _update_rack_occupancy(self, rack_id: str, delta: int):
        """更新试管架占用状态"""
        rack = self.racks_cache.get(rack_id)
        if rack:
            rack.occupied_positions = max(0, rack.occupied_positions + delta)

    async def _log_tube_event(self, tube_id: str, event_type: str, details: Dict[str, Any]):
        """记录试管事件"""
        try:
            await self.db_manager.log_system_event(
                event_type,
                "info",
                "tube_manager",
                f"试管事件: {event_type}",
                {"tube_id": tube_id, **details}
            )
        except Exception as e:
            logger.error(f"记录试管事件失败: {e}")