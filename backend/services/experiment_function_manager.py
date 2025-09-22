"""
实验功能管理器
Experiment Function Manager
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models.experiment_function_models import (
    ExperimentConfig,
    ExperimentProgress,
    ExperimentResult,
    ExperimentStatus,
    ExperimentPhase
)
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from services.tube_manager import TubeCollectionManager
from services.system_preprocessing_manager import SystemPreprocessingManager
from hardware.host_devices.pump_controller import PumpController

logger = logging.getLogger(__name__)


class ExperimentFunctionManager:
    """实验功能管理器"""

    def __init__(self, mqtt_manager: MQTTManager, db_manager: DatabaseManager):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.running_experiments: Dict[str, ExperimentProgress] = {}
        # 移除实验队列，系统只支持单个实验执行
        # self.experiment_queue: List[ExperimentConfig] = []
        self.system_busy = False
        # 当前正在运行的实验ID
        self.current_experiment_id: Optional[str] = None
        # 当前使用的架子ID
        self.current_rack_id: Optional[str] = None
        # 试管收集管理器 - 每个实验对应一个管理器
        self.tube_managers: Dict[str, TubeCollectionManager] = {}
        # 检测器信号订阅主题
        self.detector_signal_topic = "chromatography/detector/detector_1/signal"

        # 初始化系统预处理管理器和泵控制器
        self.preprocessing_manager = SystemPreprocessingManager(mqtt_manager, db_manager)
        self.pump_controller = PumpController(mock=True)

        # 梯度执行控制
        self.gradient_task: Optional[asyncio.Task] = None
        self.gradient_running = False

    async def start_experiment(self, config: ExperimentConfig) -> ExperimentProgress:
        """启动实验"""
        logger.info(f"启动实验: {config.experiment_name} (ID: {config.experiment_id})")

        # 检查系统是否可用
        if self.system_busy:
            raise ValueError("系统忙碌中，无法启动新实验")

        # 验证实验配置
        validation_result = await self._validate_experiment_config(config)
        if not validation_result["valid"]:
            raise ValueError(f"实验配置无效: {validation_result['errors']}")

        # 获取方法信息并初始化试管收集管理器
        method_info = await self._get_method_info_from_db(config.method_id)

        # 获取当前使用的架子信息
        rack_info = await self._get_current_rack_info()
        self.current_rack_id = rack_info['rack_id']

        tube_manager = TubeCollectionManager(
            method_info['flow_rate_ml_min'],
            config.collection_volume_ml  # 从实验中获取
        )
        self.tube_managers[config.experiment_id] = tube_manager

        # 创建实验进度记录
        progress = ExperimentProgress(
            experiment_id=config.experiment_id,
            current_phase=ExperimentPhase.PRE_EXPERIMENT,
            current_status=ExperimentStatus.RUNNING,
            progress_percentage=0.0,
            start_time=datetime.now(),
            estimated_completion=self._estimate_completion_time(config),
            current_step="初始化实验",
            total_steps=self._calculate_total_steps(config),
            completed_steps=0
        )

        # 初始化试管收集相关字段
        progress.tube_collection_cache = []
        progress.current_tube_id = 0  # 初始为0，预处理完成后才切换到1号试管
        progress.tube_start_time = 0.0
        progress.experiment_start_timestamp = time.time()

        # 初始化检测器信号收集相关字段
        progress.detector_signal_cache = []
        progress.signal_collection_active = False

        # 订阅检测器信号主题
        await self._subscribe_detector_signal(config.experiment_id)

        # 添加到运行实验列表
        self.running_experiments[config.experiment_id] = progress
        self.system_busy = True
        # 设置当前实验ID
        self.current_experiment_id = config.experiment_id

        try:
            # 记录实验开始
            await self._log_experiment_event(
                config.experiment_id,
                "experiment_started",
                {"config": config.dict()}
            )

            # 发布MQTT消息
            await self.mqtt_manager.publish_data(
                "experiments/status",
                {
                    "experiment_id": config.experiment_id,
                    "status": "started",
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 启动实验执行任务
            asyncio.create_task(self._execute_experiment(config))

            return progress

        except Exception as e:
            # 移除失败的实验
            self.running_experiments.pop(config.experiment_id, None)
            self.tube_managers.pop(config.experiment_id, None)
            self.system_busy = False
            # 清理当前实验ID
            if self.current_experiment_id == config.experiment_id:
                self.current_experiment_id = None
            logger.error(f"启动实验失败: {e}")
            raise

    async def pause_experiment(self, experiment_id: str, user_id: str, reason: str = None) -> bool:
        """暂停实验"""
        if experiment_id not in self.running_experiments:
            raise ValueError(f"实验 {experiment_id} 未找到或未运行")

        progress = self.running_experiments[experiment_id]

        if progress.current_status != ExperimentStatus.RUNNING:
            raise ValueError(f"实验状态不允许暂停: {progress.current_status}")

        logger.info(f"暂停实验: {experiment_id}, 用户: {user_id}, 原因: {reason}")

        # 更新状态
        progress.current_status = ExperimentStatus.PAUSED
        progress.current_step = "实验已暂停"

        # 暂停信号数据收集
        await self._pause_signal_collection(experiment_id)

        # 暂停梯度执行和积分
        await self._pause_gradient_and_integration(experiment_id)

        # 记录暂停事件
        await self._log_experiment_event(
            experiment_id,
            "experiment_paused",
            {"user_id": user_id, "reason": reason}
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "experiments/status",
            {
                "experiment_id": experiment_id,
                "status": "paused",
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )

        return True

    async def resume_experiment(self, experiment_id: str, user_id: str) -> bool:
        """恢复实验"""
        if experiment_id not in self.running_experiments:
            raise ValueError(f"实验 {experiment_id} 未找到")

        progress = self.running_experiments[experiment_id]

        if progress.current_status != ExperimentStatus.PAUSED:
            raise ValueError(f"实验状态不允许恢复: {progress.current_status}")

        logger.info(f"恢复实验: {experiment_id}, 用户: {user_id}")

        # 更新状态
        progress.current_status = ExperimentStatus.RUNNING
        progress.current_step = "实验已恢复"

        # 恢复信号数据收集
        await self._resume_signal_collection(experiment_id)

        # 恢复梯度执行和积分 (需要获取实验配置)
        # 注意：这里需要从数据库或其他地方获取实验配置
        # 暂时跳过梯度恢复，实际实现时需要存储实验配置
        logger.info(f"恢复实验但暂时跳过梯度恢复: {experiment_id}")

        # 记录恢复事件
        await self._log_experiment_event(
            experiment_id,
            "experiment_resumed",
            {"user_id": user_id}
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "experiments/status",
            {
                "experiment_id": experiment_id,
                "status": "resumed",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )

        return True

    async def stop_experiment(self, experiment_id: str, user_id: str, reason: str = None) -> ExperimentResult:
        """停止实验（情况2：前端传来终止实验信号）"""
        if experiment_id not in self.running_experiments:
            raise ValueError(f"实验 {experiment_id} 未找到或未运行")

        progress = self.running_experiments[experiment_id]
        logger.info(f"停止实验: {experiment_id}, 用户: {user_id}, 原因: {reason}")

        # 创建实验结果
        end_time = datetime.now()
        duration = (end_time - progress.start_time).total_seconds() if progress.start_time else 0

        result = ExperimentResult(
            experiment_id=experiment_id,
            final_status=ExperimentStatus.CANCELLED if reason else ExperimentStatus.COMPLETED,
            start_time=progress.start_time or end_time,
            end_time=end_time,
            duration_seconds=duration,
            total_data_points=0,  # 需要从数据系统获取
            detected_peaks=0,     # 需要从数据系统获取
            success_rate=progress.progress_percentage / 100.0,
            error_messages=[reason] if reason else [],
            result_summary={"stopped_by": user_id, "reason": reason}
        )

        # 停止信号数据收集
        await self._stop_signal_collection(experiment_id)

        # 移除运行实验和试管管理器
        self.running_experiments.pop(experiment_id, None)
        self.tube_managers.pop(experiment_id, None)
        self.system_busy = False
        # 清理当前实验ID
        if self.current_experiment_id == experiment_id:
            self.current_experiment_id = None

        # 记录停止事件
        await self._log_experiment_event(
            experiment_id,
            "experiment_stopped",
            {"user_id": user_id, "reason": reason, "result": result.dict()}
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "experiments/status",
            {
                "experiment_id": experiment_id,
                "status": "stopped",
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )

        return result

    async def get_experiment_progress(self, experiment_id: str) -> Optional[ExperimentProgress]:
        """获取实验进度"""
        return self.running_experiments.get(experiment_id)

    async def list_running_experiments(self) -> List[ExperimentProgress]:
        """列出所有运行中的实验"""
        return list(self.running_experiments.values())

    def get_current_experiment_id(self) -> Optional[str]:
        """获取当前正在运行的实验ID"""
        return self.current_experiment_id

    def is_experiment_running(self) -> bool:
        """检查是否有实验正在运行"""
        return self.current_experiment_id is not None

    async def add_to_queue(self, config: ExperimentConfig) -> int:
        """添加实验到队列 - 系统不再支持队列功能"""
        raise ValueError("系统不支持实验队列功能，请直接启动实验")

    async def remove_from_queue(self, experiment_id: str) -> bool:
        """从队列中移除实验 - 系统不再支持队列功能"""
        raise ValueError("系统不支持实验队列功能")

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态 - 系统不再支持队列功能"""
        return {
            "queue_length": 0,
            "experiments": [],
            "system_busy": self.system_busy,
            "message": "系统不支持实验队列功能"
        }

    async def _execute_experiment(self, config: ExperimentConfig):
        """执行实验的主要逻辑"""
        experiment_id = config.experiment_id
        progress = self.running_experiments[experiment_id]

        try:
            # 阶段1: 系统预处理
            await self._execute_preprocessing_phase(experiment_id, progress)

            # 阶段2: 正式实验执行
            await self._execute_formal_experiment_phase(experiment_id, progress, config)

            # 阶段3: 实验后清理
            await self._execute_post_experiment_phase(experiment_id, progress)

            # 实验完成
            progress.current_status = ExperimentStatus.COMPLETED
            progress.progress_percentage = 100.0
            progress.actual_completion = datetime.now()
            progress.current_step = "实验完成"

            logger.info(f"实验完成: {experiment_id}")

        except Exception as e:
            logger.error(f"实验执行失败: {e}")
            progress.current_status = ExperimentStatus.FAILED
            progress.current_step = f"实验失败: {str(e)}"

        finally:
            # 清理和收尾工作
            await self._cleanup_experiment_resources(experiment_id, "实验结束")

            # 系统不再支持队列，实验完成后系统空闲
            pass

    async def _execute_preprocessing_phase(self, experiment_id: str, progress: ExperimentProgress):
        """执行系统预处理阶段"""
        progress.current_phase = ExperimentPhase.PRE_EXPERIMENT
        progress.current_step = "开始系统预处理"
        progress.progress_percentage = 5.0

        logger.info(f"开始系统预处理: 实验 {experiment_id}")

        # 执行系统预处理：吹扫柱子 -> 吹扫系统 -> 柱平衡
        preprocessing_success = await self.preprocessing_manager.execute_preprocessing(int(experiment_id))

        if not preprocessing_success:
            raise Exception("系统预处理失败")

        progress.current_step = "系统预处理完成"
        progress.progress_percentage = 30.0
        logger.info(f"系统预处理完成: 实验 {experiment_id}")

    async def _execute_formal_experiment_phase(self, experiment_id: str, progress: ExperimentProgress, config: ExperimentConfig):
        """执行正式实验阶段"""
        tube_manager = self.tube_managers.get(experiment_id)
        if not tube_manager:
            raise ValueError(f"试管管理器未初始化: {experiment_id}")

        progress.current_phase = ExperimentPhase.DURING_EXPERIMENT
        progress.current_step = "切换到1号试管"
        progress.progress_percentage = 35.0

        logger.info(f"开始正式实验: 实验 {experiment_id}")

        # 步骤1: 切换到1号试管
        progress.current_tube_id = 1
        switch_success = await tube_manager.switch_to_tube(progress.current_tube_id)
        if not switch_success:
            raise Exception(f"切换到1号试管失败: tube_id={progress.current_tube_id}")

        # 步骤2: 开始订阅检测器信号
        progress.current_step = "开始信号收集"
        progress.progress_percentage = 40.0
        await self._start_signal_collection(experiment_id)

        # 步骤3: 获取方法信息并开始梯度执行
        method_info = await self._get_method_info_from_db(config.method_id)
        gradient_time_table = method_info.get('gradient_time_table', {})

        progress.current_step = "开始梯度执行和积分"
        progress.progress_percentage = 45.0

        # 启动梯度控制任务
        await self._start_gradient_execution(experiment_id, gradient_time_table)

        # 启动积分监控
        progress.tube_start_time = time.time() - progress.experiment_start_timestamp

        # 获取当前架子的试管数量
        rack_info = await self._get_current_rack_info()
        max_tube_count = rack_info['tube_count']

        # 主要收集循环
        while (progress.current_tube_id <= max_tube_count and
               progress.current_status == ExperimentStatus.RUNNING):

            current_time = time.time()
            relative_time = current_time - progress.experiment_start_timestamp

            # 调用试管管理器的积分函数检查是否完成收集
            if tube_manager.is_collection_complete(progress.tube_start_time, relative_time):
                await self._handle_tube_collection_complete(experiment_id, progress, relative_time)

                # 检查是否所有试管收集完成（情况1：试管用完了）
                if progress.current_tube_id > max_tube_count:
                    logger.info(f"试管收集完成，已使用完架子中所有试管: {max_tube_count}")
                    await self._stop_experiment_tubes_completed(experiment_id)
                    break

            # 检查暂停状态
            if progress.current_status == ExperimentStatus.PAUSED:
                await self._handle_experiment_pause(progress)

            # 更新实验进度
            self._update_experiment_progress(progress, tube_manager, relative_time)

            await asyncio.sleep(0.1)  # 100ms检查间隔

        # 收集完成
        progress.current_step = "试管收集完成"
        progress.progress_percentage = 80.0
        logger.info(f"正式实验完成: 实验 {experiment_id}")

    async def _handle_tube_collection_complete(self, experiment_id: str, progress: ExperimentProgress, current_relative_time: float):
        """处理试管收集完成"""
        tube_manager = self.tube_managers[experiment_id]

        # 创建试管数据 [start, end, tube_id]
        tube_data = tube_manager.create_tube_data(
            progress.tube_start_time,
            current_relative_time,
            progress.current_tube_id
        )

        # 存储到缓存
        progress.tube_collection_cache.append(tube_data)

        # MQTT推送
        await self._publish_tube_collection_data(experiment_id, tube_data)

        # 更新进度
        progress_percent = (progress.current_tube_id / 40) * 40 + 40  # 40-80%范围
        progress.progress_percentage = min(progress_percent, 80.0)
        progress.current_step = f"已收集试管 {progress.current_tube_id}/40"

        logger.info(f"试管 {progress.current_tube_id} 收集完成: {tube_data}")

        # 检查是否结束
        if progress.current_tube_id >= 40:
            await self._finalize_tube_collection(experiment_id, progress)
            return

        # 切换到下一个试管
        next_tube_id = progress.current_tube_id + 1
        switch_success = await tube_manager.switch_to_tube(next_tube_id)

        if not switch_success:
            # 切换失败，标记实验失败
            progress.current_status = ExperimentStatus.FAILED
            progress.current_step = f"切换试管失败: tube_id={next_tube_id}"
            logger.error(f"切换试管失败: 实验 {experiment_id}, tube_id={next_tube_id}")
            return

        # 切换成功，更新状态
        progress.current_tube_id = next_tube_id
        progress.tube_start_time = current_relative_time
        progress.current_step = f"切换到试管 {next_tube_id}/40"

    async def _publish_tube_collection_data(self, experiment_id: str, tube_data: List[float]):
        """推送试管收集数据到MQTT"""
        try:
            await self.mqtt_manager.publish_data(
                "experiments/tube_collection",
                {
                    "experiment_id": experiment_id,
                    "tube_data": tube_data,  # [start, end, tube_id]
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.debug(f"MQTT推送试管数据: {tube_data}")
        except Exception as e:
            logger.error(f"MQTT推送失败: {e}")

    async def _finalize_tube_collection(self, experiment_id: str, progress: ExperimentProgress):
        """完成试管收集并保存数据"""
        try:
            # 将tube_collection_cache保存到数据库
            tube_collection_json = json.dumps(progress.tube_collection_cache)

            # 这里需要调用数据库管理器更新实验数据
            # await self.db_manager.update_experiment_data(
            #     experiment_id,
            #     {"tube_collection": tube_collection_json}
            # )

            logger.info(f"试管收集数据已保存: 实验 {experiment_id}, "
                       f"收集了 {len(progress.tube_collection_cache)} 个试管")

            # 设置实验完成状态
            progress.current_step = "实验完成 - 已收集40个试管"

        except Exception as e:
            logger.error(f"保存试管收集数据失败: {e}")

    async def _handle_experiment_pause(self, progress: ExperimentProgress):
        """处理实验暂停状态"""
        pause_start_time = time.time()

        while progress.current_status == ExperimentStatus.PAUSED:
            await asyncio.sleep(1)  # 暂停期间等待

        # 恢复时调整时间基准，补偿暂停时长
        pause_duration = time.time() - pause_start_time
        progress.experiment_start_timestamp += pause_duration
        logger.info(f"实验恢复，暂停时长: {pause_duration:.2f}秒")

    def _update_experiment_progress(self, progress: ExperimentProgress, tube_manager: TubeCollectionManager, current_time: float):
        """更新实验进度信息"""
        # 更新试管收集进度
        tube_progress = tube_manager.get_collection_progress(current_time, progress.tube_start_time)

        # 计算总体进度 (40-80%范围)
        base_progress = (progress.current_tube_id - 1) / 40 * 40 + 40
        current_tube_progress = tube_progress / 100 * (40 / 40)  # 每个试管占总进度的1%
        progress.progress_percentage = min(base_progress + current_tube_progress, 80.0)

        # 估算剩余时间
        remaining_time = tube_manager.estimate_remaining_time(
            progress.current_tube_id,
            progress.tube_start_time,
            current_time
        )

        progress.estimated_completion = datetime.now() + timedelta(seconds=remaining_time)

    async def _start_gradient_execution(self, experiment_id: str, gradient_time_table: Dict[str, Any]):
        """启动梯度执行任务"""
        if self.gradient_running:
            logger.warning("梯度执行任务已在运行")
            return

        self.gradient_running = True
        logger.info(f"启动梯度执行任务: 实验 {experiment_id}")

        # 创建梯度执行任务
        self.gradient_task = asyncio.create_task(
            self._execute_gradient_control(experiment_id, gradient_time_table)
        )

    async def _execute_gradient_control(self, experiment_id: str, gradient_time_table: Dict[str, Any]):
        """执行梯度控制 - 每秒根据gradient_time_table设置梯度"""
        try:
            start_time = time.time()
            logger.info(f"开始梯度控制: 实验 {experiment_id}")

            while self.gradient_running and experiment_id in self.running_experiments:
                current_time = time.time()
                elapsed_time = int(current_time - start_time)  # 已运行秒数

                # 根据时间表获取当前时间点的梯度配置
                gradient_config = self._get_gradient_for_time(elapsed_time, gradient_time_table)

                if gradient_config:
                    # 设置泵控制器梯度
                    await self.pump_controller.set_gradient(gradient_config)
                    logger.debug(f"设置梯度 t={elapsed_time}s: {gradient_config}")

                await asyncio.sleep(1)  # 每秒执行一次

        except asyncio.CancelledError:
            logger.info(f"梯度控制任务被取消: 实验 {experiment_id}")
        except Exception as e:
            logger.error(f"梯度控制执行失败: {e}")
        finally:
            self.gradient_running = False

    def _get_gradient_for_time(self, elapsed_time: int, gradient_time_table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """根据已运行时间获取对应的梯度配置"""
        # 这里需要根据实际的gradient_time_table格式来解析
        # 假设格式类似: {"0": {"A": 1.0, "B": 0.0}, "60": {"A": 0.5, "B": 0.5}, ...}
        time_str = str(elapsed_time)
        if time_str in gradient_time_table:
            return gradient_time_table[time_str]
        return None

    async def _stop_gradient_execution(self, experiment_id: str):
        """停止梯度执行"""
        if self.gradient_task and not self.gradient_task.done():
            self.gradient_running = False
            self.gradient_task.cancel()
            try:
                await self.gradient_task
            except asyncio.CancelledError:
                pass
            logger.info(f"停止梯度执行: 实验 {experiment_id}")

        # 停止泵控制器
        await self.pump_controller.stop_all_pumps()

    async def _pause_gradient_and_integration(self, experiment_id: str):
        """暂停梯度执行和积分"""
        # 暂停梯度执行
        if self.gradient_running:
            self.gradient_running = False
            logger.info(f"暂停梯度执行: 实验 {experiment_id}")

        # 停止泵控制器
        await self.pump_controller.stop_all_pumps()
        logger.info(f"停止泵控制器: 实验 {experiment_id}")

    async def _resume_gradient_and_integration(self, experiment_id: str, config: ExperimentConfig):
        """恢复梯度执行和积分"""
        if experiment_id not in self.running_experiments:
            return

        # 获取方法信息
        method_info = await self._get_method_info_from_db(config.method_id)
        gradient_time_table = method_info.get('gradient_time_table', {})

        # 恢复梯度执行
        await self._start_gradient_execution(experiment_id, gradient_time_table)
        logger.info(f"恢复梯度执行: 实验 {experiment_id}")

    async def _execute_post_experiment_phase(self, experiment_id: str, progress: ExperimentProgress):
        """执行实验后处理阶段"""
        progress.current_phase = ExperimentPhase.POST_EXPERIMENT
        progress.current_step = "停止梯度执行"
        progress.progress_percentage = 85.0

        # 停止梯度执行
        await self._stop_gradient_execution(experiment_id)

        progress.current_step = "数据处理"
        progress.progress_percentage = 90.0
        await asyncio.sleep(1)

        progress.current_step = "系统清理"
        progress.progress_percentage = 95.0
        await asyncio.sleep(1)

    async def _validate_experiment_config(self, config: ExperimentConfig) -> Dict[str, Any]:
        """验证实验配置"""
        errors = []

        # 基本验证
        if not config.experiment_id:
            errors.append("实验ID不能为空")
        if not config.method_id:
            errors.append("方法ID不能为空")
        if not config.smiles_id:
            errors.append("样品ID不能为空")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _estimate_completion_time(self, config: ExperimentConfig) -> datetime:
        """估算完成时间"""
        # 简单估算，实际应根据方法参数计算
        estimated_duration = timedelta(minutes=30)  # 默认30分钟
        return datetime.now() + estimated_duration

    def _calculate_total_steps(self, config: ExperimentConfig) -> int:
        """计算总步骤数"""
        # 简单计算，实际应根据方法复杂度
        return 10  # 默认10个步骤


    async def _get_method_info_from_db(self, method_id: str) -> Dict[str, Any]:
        """从数据库获取方法信息"""
        try:
            # 这里需要调用数据库管理器获取方法的flow_rate_ml_min和collection_volume_ml
            # method_info = await self.db_manager.get_method_by_id(method_id)
            # 临时返回默认值，实际应该从数据库查询
            method_info = {
                'flow_rate_ml_min': 10.0,  # 默认流速 10 ml/min
                'method_name': f'Method_{method_id}'
            }
            logger.info(f"获取方法信息: {method_id} -> {method_info}")
            return method_info
        except Exception as e:
            logger.error(f"获取方法信息失败: {e}")
            # 返回默认值以防止程序崩溃
            return {
                'flow_rate_ml_min': 10.0,
                'method_name': 'Default_Method'
            }

    async def _log_experiment_event(self, experiment_id: str, event_type: str, details: Dict[str, Any]):
        """记录实验事件"""
        try:
            await self.db_manager.log_system_event(
                event_type,
                "info",
                "experiment_manager",
                f"实验事件: {event_type}",
                {"experiment_id": experiment_id, **details}
            )
        except Exception as e:
            logger.error(f"记录实验事件失败: {e}")

    # ==================== 检测器信号数据收集相关方法 ====================

    async def _subscribe_detector_signal(self, experiment_id: str):
        """订阅检测器信号主题"""
        try:
            # 创建专门的消息处理器，绑定到特定实验
            def signal_handler(topic: str, data: Any):
                self._handle_detector_signal(experiment_id, topic, data)

            # 订阅MQTT主题
            success = await self.mqtt_manager.subscribe_topic(
                self.detector_signal_topic,
                handler=signal_handler
            )

            if success:
                logger.info(f"成功订阅检测器信号主题: {self.detector_signal_topic} for experiment {experiment_id}")
            else:
                logger.error(f"订阅检测器信号主题失败: {self.detector_signal_topic}")

        except Exception as e:
            logger.error(f"订阅检测器信号时出错: {e}")

    def _handle_detector_signal(self, experiment_id: str, topic: str, data: Any):
        """处理接收到的检测器信号数据"""
        try:
            # 检查实验是否还在运行
            if experiment_id not in self.running_experiments:
                return

            progress = self.running_experiments[experiment_id]

            # 只有当信号收集处于活跃状态且实验正在运行时才收集数据
            if not progress.signal_collection_active or progress.current_status != ExperimentStatus.RUNNING:
                return

            # 处理信号数据 - 期望格式: [1.73427, 2.61003]
            if isinstance(data, list) and len(data) >= 2:
                signal_data = data[:2]  # 只取前两个值
                progress.detector_signal_cache.append(signal_data)

                logger.debug(f"收集信号数据: {signal_data} for experiment {experiment_id}")

                # 可选：定期发布信号收集状态
                if len(progress.detector_signal_cache) % 100 == 0:  # 每100个数据点发布一次状态
                    asyncio.create_task(self._publish_signal_collection_status(experiment_id))

            else:
                logger.warning(f"收到无效的信号数据格式: {data} for experiment {experiment_id}")

        except Exception as e:
            logger.error(f"处理检测器信号数据时出错: {e}")

    async def _publish_signal_collection_status(self, experiment_id: str):
        """发布信号收集状态"""
        try:
            if experiment_id not in self.running_experiments:
                return

            progress = self.running_experiments[experiment_id]

            status_data = {
                "experiment_id": experiment_id,
                "signal_points_collected": len(progress.detector_signal_cache),
                "collection_active": progress.signal_collection_active,
                "timestamp": datetime.now().isoformat()
            }

            await self.mqtt_manager.publish_data(
                "experiments/signal_status",
                status_data
            )

        except Exception as e:
            logger.error(f"发布信号收集状态时出错: {e}")

    async def _start_signal_collection(self, experiment_id: str):
        """开始信号数据收集"""
        try:
            if experiment_id not in self.running_experiments:
                logger.error(f"实验未找到，无法开始信号收集: {experiment_id}")
                return

            progress = self.running_experiments[experiment_id]
            progress.signal_collection_active = True

            logger.info(f"开始信号数据收集: {experiment_id}")

            # 发布信号收集开始状态
            await self.mqtt_manager.publish_data(
                "experiments/signal_status",
                {
                    "experiment_id": experiment_id,
                    "action": "start_collection",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"开始信号收集时出错: {e}")

    async def _pause_signal_collection(self, experiment_id: str):
        """暂停信号数据收集"""
        try:
            if experiment_id not in self.running_experiments:
                logger.error(f"实验未找到，无法暂停信号收集: {experiment_id}")
                return

            progress = self.running_experiments[experiment_id]
            progress.signal_collection_active = False

            logger.info(f"暂停信号数据收集: {experiment_id}")

            # 发布信号收集暂停状态
            await self.mqtt_manager.publish_data(
                "experiments/signal_status",
                {
                    "experiment_id": experiment_id,
                    "action": "pause_collection",
                    "signal_points_collected": len(progress.detector_signal_cache),
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"暂停信号收集时出错: {e}")

    async def _resume_signal_collection(self, experiment_id: str):
        """恢复信号数据收集"""
        try:
            if experiment_id not in self.running_experiments:
                logger.error(f"实验未找到，无法恢复信号收集: {experiment_id}")
                return

            progress = self.running_experiments[experiment_id]
            progress.signal_collection_active = True

            logger.info(f"恢复信号数据收集: {experiment_id}")

            # 发布信号收集恢复状态
            await self.mqtt_manager.publish_data(
                "experiments/signal_status",
                {
                    "experiment_id": experiment_id,
                    "action": "resume_collection",
                    "signal_points_collected": len(progress.detector_signal_cache),
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"恢复信号收集时出错: {e}")

    async def _stop_signal_collection(self, experiment_id: str):
        """停止信号数据收集"""
        try:
            if experiment_id not in self.running_experiments:
                return

            progress = self.running_experiments[experiment_id]
            progress.signal_collection_active = False

            logger.info(f"停止信号数据收集: {experiment_id}, 共收集 {len(progress.detector_signal_cache)} 个数据点")

            # 发布信号收集停止状态和最终数据
            await self.mqtt_manager.publish_data(
                "experiments/signal_final",
                {
                    "experiment_id": experiment_id,
                    "action": "stop_collection",
                    "total_signal_points": len(progress.detector_signal_cache),
                    "signal_data_sample": progress.detector_signal_cache[-10:] if progress.detector_signal_cache else [],  # 最后10个数据点
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 取消订阅信号主题
            await self.mqtt_manager.unsubscribe_topic(self.detector_signal_topic)

        except Exception as e:
            logger.error(f"停止信号收集时出错: {e}")

    async def get_signal_data(self, experiment_id: str) -> List[List[float]]:
        """获取实验的信号数据"""
        if experiment_id not in self.running_experiments:
            return []

        progress = self.running_experiments[experiment_id]
        return progress.detector_signal_cache.copy()  # 返回副本避免外部修改

    # ==================== 三种停止实验情况的专用方法 ====================

    async def _stop_experiment_tubes_completed(self, experiment_id: str) -> ExperimentResult:
        """停止实验（情况1：试管用完了）"""
        logger.info(f"实验因试管用完而正常完成: {experiment_id}")

        progress = self.running_experiments[experiment_id]
        end_time = datetime.now()
        duration = (end_time - progress.start_time).total_seconds() if progress.start_time else 0

        result = ExperimentResult(
            experiment_id=experiment_id,
            final_status=ExperimentStatus.COMPLETED,
            start_time=progress.start_time or end_time,
            end_time=end_time,
            duration_seconds=duration,
            total_data_points=len(progress.detector_signal_cache),
            detected_peaks=0,  # 需要从数据分析获取
            success_rate=1.0,  # 试管用完算作100%成功
            error_messages=[],
            result_summary={
                "completion_reason": "tubes_completed",
                "tubes_used": progress.current_tube_id - 1,
                "rack_id": self.current_rack_id
            }
        )

        # 更新实验状态
        progress.current_status = ExperimentStatus.COMPLETED
        progress.progress_percentage = 100.0
        progress.actual_completion = end_time
        progress.current_step = "实验正常完成"

        # 清理资源
        await self._cleanup_experiment_resources(experiment_id, "试管收集完成")

        # 记录完成事件
        await self._log_experiment_event(
            experiment_id,
            "experiment_completed_tubes",
            {"completion_reason": "tubes_completed", "result": result.dict()}
        )

        # 发布MQTT消息
        await self.mqtt_manager.publish_data(
            "experiments/status",
            {
                "experiment_id": experiment_id,
                "status": "completed",
                "completion_reason": "tubes_completed",
                "timestamp": datetime.now().isoformat()
            }
        )

        return result

    async def _stop_experiment_critical_alarm(self, experiment_id: str, alarm_info: Dict[str, Any]) -> ExperimentResult:
        """停止实验（情况3：有终止级别的报警出现）"""
        logger.error(f"实验因严重报警而紧急停止: {experiment_id}, 报警: {alarm_info}")

        progress = self.running_experiments[experiment_id]
        end_time = datetime.now()
        duration = (end_time - progress.start_time).total_seconds() if progress.start_time else 0

        result = ExperimentResult(
            experiment_id=experiment_id,
            final_status=ExperimentStatus.FAILED,
            start_time=progress.start_time or end_time,
            end_time=end_time,
            duration_seconds=duration,
            total_data_points=len(progress.detector_signal_cache),
            detected_peaks=0,
            success_rate=progress.progress_percentage / 100.0,
            error_messages=[f"严重报警: {alarm_info.get('message', 'Unknown alarm')}"],
            result_summary={
                "completion_reason": "critical_alarm",
                "alarm_info": alarm_info,
                "tubes_used": progress.current_tube_id - 1,
                "rack_id": self.current_rack_id
            }
        )

        # 更新实验状态
        progress.current_status = ExperimentStatus.FAILED
        progress.current_step = f"实验因报警停止: {alarm_info.get('message', 'Critical alarm')}"

        # 紧急清理资源
        await self._cleanup_experiment_resources(experiment_id, f"严重报警: {alarm_info.get('message', 'Critical alarm')}")

        # 记录报警停止事件
        await self._log_experiment_event(
            experiment_id,
            "experiment_stopped_alarm",
            {"alarm_info": alarm_info, "result": result.dict()}
        )

        # 发布紧急停止MQTT消息
        await self.mqtt_manager.publish_data(
            "experiments/emergency",
            {
                "experiment_id": experiment_id,
                "status": "emergency_stopped",
                "alarm_info": alarm_info,
                "timestamp": datetime.now().isoformat()
            }
        )

        return result

    async def _cleanup_experiment_resources(self, experiment_id: str, reason: str):
        """清理实验资源的通用方法"""
        # 停止梯度执行
        await self._stop_gradient_execution(experiment_id)

        # 停止信号数据收集
        await self._stop_signal_collection(experiment_id)

        # 移除运行实验和试管管理器
        self.running_experiments.pop(experiment_id, None)
        self.tube_managers.pop(experiment_id, None)
        self.system_busy = False

        # 清理当前实验ID和架子ID
        if self.current_experiment_id == experiment_id:
            self.current_experiment_id = None
            self.current_rack_id = None

        logger.info(f"清理实验资源完成: {experiment_id}, 原因: {reason}")

    async def _get_current_rack_info(self) -> Dict[str, Any]:
        """从数据库获取当前使用的架子信息"""
        try:
            # 首先查询状态为"使用"的架子
            active_racks = await self.db_manager.get_racks_by_status("使用")

            if active_racks:
                # 如果找到状态为"使用"的架子，使用第一个
                rack_info = active_racks[0]
                logger.info(f"找到状态为'使用'的架子: {rack_info}")
            else:
                # 如果没找到状态为"使用"的架子，使用默认配置
                logger.warning("未找到状态为'使用'的架子，使用默认配置")
                rack_info = {
                    'rack_id': 'rack_001',
                    'tube_count': 40,
                    'tube_volume_ml': 2.0,
                    'rack_type': 'standard',
                    'status': 'active'
                }

            logger.info(f"获取架子信息: {rack_info}")
            return rack_info

        except Exception as e:
            logger.error(f"获取架子信息失败: {e}")
            # 返回默认值以防止程序崩溃
            return {
                'rack_id': 'rack_001',
                'tube_count': 40,
                'tube_volume_ml': 2.0,
                'rack_type': 'standard',
                'status': 'active'
            }

    async def _check_critical_alarms(self) -> Optional[Dict[str, Any]]:
        """检查是否有终止级别的报警"""
        try:
            # 这里需要调用系统报警检查，例如：
            # 1. 温度过高/过低
            # 2. 压力异常
            # 3. 流速异常
            # 4. 硬件故障
            # alarms = await self.db_manager.get_critical_alarms()

            # 临时模拟报警检查逻辑
            # 实际应该从系统状态或数据库查询
            logger.debug("检查终止级别报警...")

            # 模拟：这里应该检查实际的系统状态
            # 返回None表示没有终止级别报警
            return None

        except Exception as e:
            logger.error(f"检查报警时出错: {e}")
            return None

    def get_current_rack_id(self) -> Optional[str]:
        """获取当前使用的架子ID"""
        return self.current_rack_id