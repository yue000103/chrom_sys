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


class TubeCollectionManager:
    """试管收集管理器 - 专门处理实验过程中的试管收集逻辑"""

    def __init__(self, flow_rate_ml_min: float, collection_volume_ml: float, experiment_manager=None):
        """
        初始化试管收集管理器

        Args:
            flow_rate_ml_min: 流速 (ml/min)
            collection_volume_ml: 每根试管收集体积 (ml)
            experiment_manager: 实验功能管理器引用，用于获取rack信息
        """
        self.flow_rate = flow_rate_ml_min
        self.collection_volume = collection_volume_ml
        self.experiment_manager = experiment_manager
        self.collection_time_per_tube = self._calculate_collection_time()

        # 初始化阀门路径管理器
        try:
            from services.valve_path_manager import ValvePathManager, ValvePathExecutor
            self.valve_path_manager = ValvePathManager()
            self.valve_path_executor = ValvePathExecutor(self.valve_path_manager)
            logger.info("阀门路径管理器初始化成功")
        except Exception as e:
            logger.error(f"阀门路径管理器初始化失败: {e}")
            self.valve_path_manager = None
            self.valve_path_executor = None

        # 验证参数
        if not self.validate_tube_parameters(flow_rate_ml_min, collection_volume_ml):
            raise ValueError(f"试管参数无效: flow_rate={flow_rate_ml_min}, collection_volume={collection_volume_ml}")

        logger.info(f"试管收集管理器初始化: 流速={self.flow_rate}ml/min, "
                   f"收集体积={self.collection_volume}ml, "
                   f"每管时间={self.collection_time_per_tube:.2f}秒")

    def _get_current_tube_count(self) -> int:
        """
        从实验管理器获取当前rack的tube_count

        Returns:
            int: 试管数量，默认40
        """
        if self.experiment_manager and hasattr(self.experiment_manager, 'current_rack_id'):
            try:
                current_experiment_id = self.experiment_manager.get_current_experiment_id()
                if current_experiment_id:
                    rack_info = self.experiment_manager._get_cached_data(current_experiment_id, 'rack_info')
                    if rack_info and 'tube_count' in rack_info:
                        return rack_info['tube_count']
            except Exception as e:
                logger.warning(f"获取rack tube_count失败，使用默认值40: {e}")

        # 默认返回40
        return 40

    def _tube_id_to_module_tube(self, tube_id: int) -> tuple[int, int]:
        """
        将试管ID转换为模块号和试管号

        Args:
            tube_id: 试管ID (1-N)

        Returns:
            tuple: (module_number, tube_number)
        """
        # 正确映射：试管号保持原值，只计算模块号
        # tube_id 1-20 -> module 1, tube 1-20
        # tube_id 21-40 -> module 2, tube 21-40
        # tube_id 41-60 -> module 3, tube 41-60

        tubes_per_module = self._get_tubes_per_module()

        if tube_id <= 0:
            return 1, 1

        module_number = ((tube_id - 1) // tubes_per_module) + 1
        tube_number = tube_id  # 试管号保持原值

        logger.debug(f"试管ID {tube_id} 转换为 模块{module_number}, 试管{tube_number} (每模块{tubes_per_module}管)")
        return module_number, tube_number

    def _get_tubes_per_module(self) -> int:
        """
        获取每个模块的试管数量

        Returns:
            int: 每个模块的试管数量，默认20
        """
        # 可以从rack配置或数据库中获取这个信息
        # 目前使用固定值，未来可以从实验管理器或数据库配置中获取
        try:
            if self.experiment_manager:
                current_experiment_id = self.experiment_manager.get_current_experiment_id()
                if current_experiment_id:
                    rack_info = self.experiment_manager._get_cached_data(current_experiment_id, 'rack_info')
                    if rack_info and 'tubes_per_module' in rack_info:
                        return rack_info['tubes_per_module']
        except Exception as e:
            logger.debug(f"获取tubes_per_module失败，使用默认值: {e}")

        # 默认每个模块20个试管
        return 20

    def _calculate_collection_time(self) -> float:
        """
        计算每根试管收集时间(秒)

        Returns:
            float: 收集时间(秒)
        """
        if self.flow_rate <= 0:
            raise ValueError("流速必须大于0")
        return (self.collection_volume / self.flow_rate) * 60

    def is_collection_complete(self, tube_start_time: float, current_time: float) -> bool:
        """
        积分函数 - 检查试管收集是否完成

        Args:
            tube_start_time: 试管开始收集时间(相对于实验开始的秒数)
            current_time: 当前时间(相对于实验开始的秒数)

        Returns:
            bool: True表示收集完成，需要切换试管
        """
        elapsed = current_time - tube_start_time
        is_complete = elapsed >= self.collection_time_per_tube

        if is_complete:
            logger.debug(f"试管收集完成: 已用时{elapsed:.2f}秒, 预期{self.collection_time_per_tube:.2f}秒")

        return is_complete

    def create_tube_data(self, start_time: float, end_time: float, tube_id: int) -> List[float]:
        """
        创建试管数据 - 格式: [start_time, end_time, tube_id]

        Args:
            start_time: 开始时间(秒)
            end_time: 结束时间(秒)
            tube_id: 试管ID

        Returns:
            List[float]: [开始时间, 结束时间, 试管ID]
        """
        tube_data = [start_time, end_time, tube_id]
        logger.debug(f"创建试管数据: {tube_data}")
        return tube_data

    async def switch_to_tube(self, tube_id: int) -> bool:
        """
        切换到指定试管 - 执行具体的硬件切换操作

        Args:
            tube_id: 目标试管ID (1-N)

        Returns:
            bool: 切换是否成功
        """
        try:
            # 验证试管ID
            if not self._validate_tube_id(tube_id):
                logger.error(f"试管ID无效: {tube_id}")
                return False

            logger.info(f"开始切换到试管 {tube_id}")

            # 步骤1: 停止当前收集
            # await self._stop_current_collection()

            # 步骤2: 移动到目标试管位置
            await self._move_to_tube_position(tube_id)

            # 步骤3: 开始新试管的收集（这里会执行阀门路径切换）
            await self._start_tube_collection(tube_id)

            logger.info(f"成功切换到试管 {tube_id}")
            return True

        except Exception as e:
            logger.error(f"切换试管失败: tube_id={tube_id}, error={e}")
            return False

    async def _stop_current_collection(self):
        """停止当前试管的收集"""
        # 模拟停止收集操作
        import asyncio
        await asyncio.sleep(0.05)  # 50ms
        logger.debug("停止当前试管收集")

    async def _move_to_tube_position(self, tube_id: int):
        """移动到目标试管位置"""

        import asyncio
        await asyncio.sleep(0.1)  # 100ms移动时间
        logger.debug(f"移动到试管 {tube_id} 位置")

    async def _start_tube_collection(self, tube_id: int):
        """开始新试管的收集"""
        try:
            if self.valve_path_executor is None:
                logger.warning("阀门路径执行器未初始化，使用模拟模式")
                import asyncio
                await asyncio.sleep(0.05)  # 50ms
                logger.debug(f"开始试管 {tube_id} 收集（模拟模式）")
                return

            # 将试管ID转换为模块号和试管号
            module_number, tube_number = self._tube_id_to_module_tube(tube_id)

            logger.info(f"开始试管 {tube_id} 收集: 模块{module_number}, 试管{tube_number}")

            # 使用阀门路径执行器执行路径
            result = await self.valve_path_executor.execute_tube_path(module_number, tube_number)

            if result['success']:
                logger.info(f"试管 {tube_id} 路径执行成功: {result['message']}")
                logger.debug(f"路径执行详情: 总步骤={result['total_steps']}, "
                           f"成功步骤={result['success_steps']}, "
                           f"耗时={result['execution_time']:.3f}s")
            else:
                logger.error(f"试管 {tube_id} 路径执行失败: {result['message']}")
                # 仍然继续，只记录错误但不中断实验

        except Exception as e:
            logger.error(f"试管 {tube_id} 收集启动异常: {e}")
            # 发生异常时使用备用模拟模式
            import asyncio
            await asyncio.sleep(0.05)  # 50ms
            logger.debug(f"试管 {tube_id} 收集启动（备用模拟模式）")

    def _validate_tube_id(self, tube_id: int) -> bool:
        """
        验证试管ID是否有效

        Args:
            tube_id: 试管ID

        Returns:
            bool: ID是否有效
        """
        max_tube_count = self._get_current_tube_count()
        is_valid = 1 <= tube_id <= max_tube_count
        if not is_valid:
            logger.warning(f"试管ID {tube_id} 超出有效范围 1-{max_tube_count}")
        return is_valid

    def get_collection_time_per_tube(self) -> float:
        """
        获取每根试管的收集时间

        Returns:
            float: 收集时间(秒)
        """
        return self.collection_time_per_tube

    def get_total_collection_time(self, tube_count: int = None) -> float:
        """
        获取总收集时间

        Args:
            tube_count: 试管数量，如果不指定则使用当前rack的tube_count

        Returns:
            float: 总时间(秒)
        """
        if tube_count is None:
            tube_count = self._get_current_tube_count()
        return self.collection_time_per_tube * tube_count

    def get_collection_progress(self, elapsed_time: float, tube_start_time: float) -> float:
        """
        获取当前试管的收集进度

        Args:
            elapsed_time: 实验总耗时
            tube_start_time: 当前试管开始时间

        Returns:
            float: 进度百分比 (0-100)
        """
        tube_elapsed = elapsed_time - tube_start_time
        progress = min((tube_elapsed / self.collection_time_per_tube) * 100, 100.0)
        return progress

    def estimate_remaining_time(self, current_tube_id: int, tube_start_time: float, current_time: float) -> float:
        """
        估算剩余时间

        Args:
            current_tube_id: 当前试管ID
            tube_start_time: 当前试管开始时间
            current_time: 当前时间

        Returns:
            float: 剩余时间(秒)
        """
        # 当前试管剩余时间
        current_tube_elapsed = current_time - tube_start_time
        current_tube_remaining = max(0, self.collection_time_per_tube - current_tube_elapsed)

        # 剩余试管时间
        max_tube_count = self._get_current_tube_count()
        remaining_tubes = max(0, max_tube_count - current_tube_id)
        remaining_tubes_time = remaining_tubes * self.collection_time_per_tube

        return current_tube_remaining + remaining_tubes_time

    @staticmethod
    def validate_tube_parameters(flow_rate: float, collection_volume: float) -> bool:
        """
        验证试管参数

        Args:
            flow_rate: 流速
            collection_volume: 收集体积

        Returns:
            bool: 参数是否有效
        """
        return flow_rate > 0 and collection_volume > 0

    def get_status_info(self) -> Dict[str, Any]:
        """
        获取试管管理器状态信息

        Returns:
            Dict: 状态信息
        """
        max_tube_count = self._get_current_tube_count()
        return {
            "flow_rate_ml_min": self.flow_rate,
            "collection_volume_ml": self.collection_volume,
            "collection_time_per_tube_sec": self.collection_time_per_tube,
            "total_collection_time_sec": self.get_total_collection_time(),
            "max_tube_count": max_tube_count
        }

    def __repr__(self):
        return (f"TubeCollectionManager(flow_rate={self.flow_rate}, "
                f"collection_volume={self.collection_volume}, "
                f"collection_time={self.collection_time_per_tube:.2f}s)")


class TubeManagerError(Exception):
    """试管管理器异常"""
    pass


class TubeCollectionError(TubeManagerError):
    """试管收集异常"""
    pass


class TubeSwitchError(TubeManagerError):
    """试管切换异常"""
    pass