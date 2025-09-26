"""
实验功能管理器
Experiment Function Manager
"""

import asyncio
import logging
import time
import json
import uuid
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
from data.database_utils import ChromatographyDB
from services.tube_manager import TubeCollectionManager
from services.system_preprocessing_manager import SystemPreprocessingManager
from hardware.host_devices.pump_controller import PumpController

logger = logging.getLogger(__name__)


class ExperimentFunctionManager:
    """实验功能管理器"""

    def __init__(self, mqtt_manager: MQTTManager):
        self.mqtt_manager = mqtt_manager
        self.db = ChromatographyDB()
        self.running_experiments: Dict[str, ExperimentProgress] = {}
        # 移除实验队列，系统只支持单个实验执行
        # self.experiment_queue: List[ExperimentConfig] = []
        self.system_busy = False
        # 实验数据缓存 - 避免重复查询数据库
        self.experiment_data_cache: Dict[str, Dict[str, Any]] = {}
        # 当前正在运行的实验ID
        self.current_experiment_id: Optional[str] = None
        # 当前使用的架子ID
        self.current_rack_id: Optional[str] = None
        # 试管收集管理器 - 每个实验对应一个管理器
        self.tube_managers: Dict[str, TubeCollectionManager] = {}
        # 检测器信号订阅主题
        self.detector_signal_topic = "chromatography/detector/detector_1/signal"

        # 收集控制相关主题
        self.collection_control_topic_template = "experiments/{}/collection/control"
        self.collection_status_topic_template = "experiments/{}/collection/status"

        # 收集监控任务管理
        self.collection_monitor_tasks: Dict[str, asyncio.Task] = {}  # 每个实验的收集监控任务

        # 初始化系统预处理管理器和泵控制器
        self.preprocessing_manager = SystemPreprocessingManager(mqtt_manager)
        self.pump_controller = PumpController(mock=True)

        # 梯度执行控制
        self.gradient_task: Optional[asyncio.Task] = None
        self.gradient_running = False

        # 信号数据备份控制
        self.backup_tasks: Dict[str, asyncio.Task] = {}  # 每个实验的备份任务
        self.experiment_history_ids: Dict[str, str] = {}  # 每个实验对应的history_id

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

        # 预加载实验相关的所有数据
        await self._preload_experiment_data(config)

        # 获取方法信息并初始化试管收集管理器
        method_info = self._get_cached_data(config.experiment_id, 'method_info')

        # 获取当前使用的架子信息
        rack_info = self._get_cached_data(config.experiment_id, 'rack_info')
        self.current_rack_id = rack_info['rack_id']

        tube_manager = TubeCollectionManager(
            method_info['flow_rate_ml_min'],
            config.collection_volume_ml,  # 从实验中获取
            experiment_manager=self  # 传递自身引用
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
        progress.current_step = "实验暂停中..."

        # 发布暂停控制消息，触发MQTT处理
        await self._publish_collection_control(experiment_id, "pause_collection", {
            "user_id": user_id,
            "reason": reason
        })

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
        progress.current_step = "实验恢复中..."

        # 发布恢复控制消息，触发MQTT处理
        await self._publish_collection_control(experiment_id, "resume_collection", {
            "user_id": user_id
        })

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
        progress.current_step = "初始化设备参数"
        progress.progress_percentage = 0.0

        logger.info(f"开始系统预处理: 实验 {experiment_id}")

        # 获取实验数据
        experiment_data = self._get_cached_data(experiment_id, 'experiment_info')
        method_info = self._get_cached_data(experiment_id, 'method_info')

        # 步骤1: 设备初始化 - 设置检测器波长和泵流速参数
        detector_wavelength = method_info.get('detector_wavelength', [254, 280])
        flow_rate = method_info.get('flow_rate_ml_min', 1.0)

        # 构建方法参数
        method_params = {
            'wavelength': detector_wavelength if not isinstance(detector_wavelength, list) else detector_wavelength[0],
            'flow_rates': {'A': flow_rate, 'B': 0.0, 'C': 0.0, 'D': 0.0}
        }

        initialization_data = {
            'experiment_id': experiment_id,
            'method_params': method_params
        }

        # 使用预处理管理器的initialize_devices方法
        devices_initialized = await self.preprocessing_manager.initialize_devices(
            experiment_data=initialization_data,
            wavelength=detector_wavelength if not isinstance(detector_wavelength, list) else detector_wavelength[0],
            flow_rates={'A': flow_rate, 'B': 0.0, 'C': 0.0, 'D': 0.0}
        )

        if not devices_initialized:
            raise Exception("设备初始化失败")

        logger.info(f"设备初始化成功: 波长={detector_wavelength}, 流速={flow_rate} ml/min")

        progress.current_step = "开始系统预处理"
        progress.progress_percentage = 10.0

        # 构建预处理数据
        preprocessing_data = {
            'experiment_id': experiment_id,
            'preprocessing': {
                'purge_system': experiment_data.get('purge_system', False),
                'purge_column': experiment_data.get('purge_column', False),
                'purge_column_time_min': experiment_data.get('purge_column_time_min', 0),
                'column_balance': experiment_data.get('column_balance', False),
                'column_balance_time_min': experiment_data.get('column_balance_time_min', 0),
                'column_conditioning_solution': experiment_data.get('column_conditioning_solution')
            },
            'method_params': method_params
        }

        # 执行系统预处理：吹扫柱子 -> 吹扫系统 -> 柱平衡
        preprocessing_success = await self.preprocessing_manager.execute_preprocessing(preprocessing_data)

        if not preprocessing_success:
            raise Exception("系统预处理失败")

        progress.current_step = "系统预处理完成，订阅检测器信号"
        progress.progress_percentage = 30.0
        logger.info(f"系统预处理完成: 实验 {experiment_id}")

        # 系统预处理完成后订阅检测器信号
        # 从column_balance步骤开始需要检测器信号数据
        await self._subscribe_detector_signal(experiment_id)
        logger.info(f"检测器信号订阅完成: 实验 {experiment_id}")

    async def _execute_formal_experiment_phase(self, experiment_id: str, progress: ExperimentProgress, config: ExperimentConfig):
        """执行正式实验阶段"""
        tube_manager = self.tube_managers.get(experiment_id)
        if not tube_manager:
            raise ValueError(f"试管管理器未初始化: {experiment_id}")

        progress.current_phase = ExperimentPhase.DURING_EXPERIMENT
        progress.current_step = "切换到1号试管"
        progress.progress_percentage = 35.0

        logger.info(f"开始正式实验: 实验 {experiment_id}")

        # 获取方法信息
        method_info = self._get_cached_data(experiment_id, 'method_info')

        # 步骤1: 切换到1号试管
        progress.current_tube_id = 1
        switch_success = await tube_manager.switch_to_tube(progress.current_tube_id)
        if not switch_success:
            raise Exception(f"切换到1号试管失败: tube_id={progress.current_tube_id}")

        # 步骤2: 激活检测器信号收集（订阅已在预处理完成后进行）
        progress.current_step = "激活信号收集"
        progress.progress_percentage = 40.0
        await self._start_signal_collection(experiment_id)

        # 步骤3: 开始梯度执行和积分
        gradient_time_table = method_info.get('gradient_time_table', [])

        progress.current_step = "开始梯度执行和积分"
        progress.progress_percentage = 45.0

        # 启动梯度控制任务
        await self._start_gradient_execution(experiment_id, gradient_time_table)

        # 启动积分监控 - 记录第一个试管开始时的实验时间
        progress.tube_start_time = self._get_experiment_elapsed_time(experiment_id)

        # 获取当前架子的试管数量
        rack_info = await self._get_current_rack_info()
        max_tube_count = rack_info['tube_count']
        logger.info(f"开始基于MQTT的收集监控，最大试管数: {max_tube_count}")

        # 启动独立的收集监控任务
        collection_monitor_task = asyncio.create_task(
            self._start_collection_monitor(experiment_id)
        )
        self.collection_monitor_tasks[experiment_id] = collection_monitor_task

        # 发布开始收集消息
        await self._publish_collection_control(experiment_id, "start_collection")

        # 等待收集完成或实验结束
        try:
            await collection_monitor_task
        except asyncio.CancelledError:
            logger.info(f"收集监控任务被取消: {experiment_id}")

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

        # 获取当前架子的试管数量
        rack_info = await self._get_current_rack_info()
        max_tube_count = rack_info['tube_count']

        # 更新进度
        progress_percent = (progress.current_tube_id / max_tube_count) * 40 + 40  # 40-80%范围
        progress.progress_percentage = min(progress_percent, 80.0)
        progress.current_step = f"已收集试管 {progress.current_tube_id}/{max_tube_count}"

        logger.info(f"试管 {progress.current_tube_id} 收集完成: {tube_data}")

        # 检查是否结束
        if progress.current_tube_id >= max_tube_count:
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
        progress.current_step = f"切换到试管 {next_tube_id}/{max_tube_count}"

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

            # 更新实验数据中的试管收集信息
            self.db.update_data(
                "experiments",
                {"tube_collection": tube_collection_json, "updated_at": datetime.now().isoformat()},
                "experiment_id = ?",
                (experiment_id,)
            )

            logger.info(f"试管收集数据已保存: 实验 {experiment_id}, "
                       f"收集了 {len(progress.tube_collection_cache)} 个试管")

            # 获取当前架子的试管数量
            rack_info = await self._get_current_rack_info()
            max_tube_count = rack_info['tube_count']

            # 设置实验完成状态
            progress.current_step = f"实验完成 - 已收集{max_tube_count}个试管"

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
        # 获取当前架子的试管数量
        max_tube_count = tube_manager._get_current_tube_count()

        # 更新试管收集进度
        tube_progress = tube_manager.get_collection_progress(current_time, progress.tube_start_time)

        # 计算总体进度 (40-80%范围)
        base_progress = (progress.current_tube_id - 1) / max_tube_count * 40 + 40
        current_tube_progress = tube_progress / 100 * (40 / max_tube_count)  # 每个试管占总进度的一定比例
        progress.progress_percentage = min(base_progress + current_tube_progress, 80.0)

        # 估算剩余时间
        remaining_time = tube_manager.estimate_remaining_time(
            progress.current_tube_id,
            progress.tube_start_time,
            current_time
        )

        progress.estimated_completion = datetime.now() + timedelta(seconds=remaining_time)

    async def _start_gradient_execution(self, experiment_id: str, gradient_time_table: List[Dict[str, Any]]):
        """启动梯度执行任务"""
        if self.gradient_running:
            logger.warning("梯度执行任务已在运行")
            return

        self.gradient_running = True
        logger.info(f"启动梯度执行任务: 实验 {experiment_id}")

        # 启动泵系统
        try:
            pump_started = await self.pump_controller.start_pump()
            if pump_started:
                logger.info(f"泵系统启动成功: 实验 {experiment_id}")
            else:
                logger.error(f"泵系统启动失败: 实验 {experiment_id}")
                self.gradient_running = False
                return
        except Exception as e:
            logger.error(f"启动泵系统时发生异常: {e}, 实验 {experiment_id}")
            self.gradient_running = False
            return

        # 创建梯度执行任务
        self.gradient_task = asyncio.create_task(
            self._execute_gradient_control(experiment_id, gradient_time_table)
        )

    async def _execute_gradient_control(self, experiment_id: str, gradient_time_table: List[Dict[str, Any]]):
        """执行梯度控制 - 基于实验逻辑时间而非现实时间"""
        try:
            logger.info(f"开始梯度控制: 实验 {experiment_id}")

            while self.gradient_running and experiment_id in self.running_experiments:
                progress = self.running_experiments[experiment_id]

                # 检查实验状态，暂停时不执行梯度计算
                if progress.current_status != ExperimentStatus.RUNNING:
                    await asyncio.sleep(0.5)  # 暂停状态下等待
                    continue

                # 使用实验逻辑时间而非现实时间
                experiment_elapsed_time = self._get_experiment_elapsed_time(experiment_id)
                elapsed_time = int(experiment_elapsed_time)  # 基于实验开始的逻辑时间

                # 根据时间表获取当前时间点的梯度配置
                gradient_values = self._get_gradient_for_time(elapsed_time, gradient_time_table)

                if gradient_values and len(gradient_values) == 4:
                    # 将数组转换为字典格式，以适配泵控制器
                    gradient_config = {
                        'A': gradient_values[0],  # originalA
                        'B': gradient_values[1],  # originalB
                        'C': gradient_values[2],  # originalC
                        'D': gradient_values[3]   # originalD
                    }

                    # 设置泵控制器梯度
                    await self.pump_controller.set_gradient(gradient_config)
                    logger.debug(f"设置梯度 实验时间t={experiment_elapsed_time:.1f}s: A={gradient_values[0]:.1f}, B={gradient_values[1]:.1f}, C={gradient_values[2]:.1f}, D={gradient_values[3]:.1f}")

                await asyncio.sleep(1)  # 每秒检查一次

        except asyncio.CancelledError:
            logger.info(f"梯度控制任务被取消: 实验 {experiment_id}")
        except Exception as e:
            logger.error(f"梯度控制执行失败: {e}")
        finally:
            self.gradient_running = False

    def _get_gradient_for_time(self, elapsed_time: int, gradient_time_table: List[Dict[str, Any]]) -> Optional[List[float]]:
        """
        根据已运行时间获取对应的梯度配置（时间折线插值）

        :param elapsed_time: 已运行时间（秒）
        :param gradient_time_table: 梯度时间表，格式如：
            [{"time": 0, "originalB": 90.0, "originalA": 10.0, "originalC": 0, "originalD": 0, "flowRate": 12.0},
             {"time": 15, "originalB": 60.0, "originalA": 40.0, "originalC": 0, "originalD": 0, "flowRate": 12.0},
             {"time": 25, "originalB": 90.0, "originalA": 10.0, "originalC": 0, "originalD": 0, "flowRate": 12.0}]
        :return: [originalA, originalB, originalC, originalD] 形式的数组
        """
        if not gradient_time_table or not isinstance(gradient_time_table, list):
            logger.warning(f"梯度时间表为空或格式错误: {gradient_time_table}")
            return None

        # 将elapsed_time从秒转换为分钟
        elapsed_time_min = elapsed_time / 60.0

        try:
            # 按时间排序确保数据正确
            time_points = sorted(gradient_time_table, key=lambda x: x.get('time', 0))

            if not time_points:
                logger.warning("梯度时间表为空")
                return None

            # 如果时间小于等于第一个时间点，返回第一个点的值
            if elapsed_time_min <= time_points[0]['time']:
                point = time_points[0]
                return [
                    point.get('originalA', 0),
                    point.get('originalB', 0),
                    point.get('originalC', 0),
                    point.get('originalD', 0)
                ]

            # 如果时间大于等于最后一个时间点，返回最后一个点的值
            if elapsed_time_min >= time_points[-1]['time']:
                point = time_points[-1]
                return [
                    point.get('originalA', 0),
                    point.get('originalB', 0),
                    point.get('originalC', 0),
                    point.get('originalD', 0)
                ]

            # 找到当前时间所在的时间段进行线性插值
            for i in range(len(time_points) - 1):
                t1 = time_points[i]['time']
                t2 = time_points[i + 1]['time']

                if t1 <= elapsed_time_min <= t2:
                    # 线性插值计算
                    ratio = (elapsed_time_min - t1) / (t2 - t1) if t2 != t1 else 0

                    # 获取两个时间点的值
                    p1 = time_points[i]
                    p2 = time_points[i + 1]

                    # 对每个通道进行线性插值
                    original_a = p1.get('originalA', 0) + ratio * (p2.get('originalA', 0) - p1.get('originalA', 0))
                    original_b = p1.get('originalB', 0) + ratio * (p2.get('originalB', 0) - p1.get('originalB', 0))
                    original_c = p1.get('originalC', 0) + ratio * (p2.get('originalC', 0) - p1.get('originalC', 0))
                    original_d = p1.get('originalD', 0) + ratio * (p2.get('originalD', 0) - p1.get('originalD', 0))

                    result = [original_a, original_b, original_c, original_d]

                    logger.debug(f"梯度插值计算: t={elapsed_time_min:.2f}min, 区间[{t1}, {t2}], 比例={ratio:.3f}, 结果={result}")

                    return result

            # 如果没有找到合适的区间（理论上不应该到达这里）
            logger.warning(f"未找到合适的梯度时间区间: elapsed_time_min={elapsed_time_min}")
            return None

        except Exception as e:
            logger.error(f"梯度插值计算失败: {e}, elapsed_time={elapsed_time}, gradient_time_table={gradient_time_table}")
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
        method_info = await self._get_method_info_from_db(config.method_id, experiment_id)
        gradient_time_table = method_info.get('gradient_time_table', [])

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
        if not config.sample_id:
            errors.append("样品ID不能为空")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _estimate_completion_time(self, config: ExperimentConfig) -> datetime:
        """估算完成时间"""
        try:
            # 从缓存中获取方法信息和实验信息
            method_info = self._get_cached_data(config.experiment_id, 'method_info')
            experiment_info = self._get_cached_data(config.experiment_id, 'experiment_info')

            # 获取时间参数
            run_time_min = method_info.get('run_time_min', 0)
            purge_column_time_min = experiment_info.get('purge_column_time_min', 0)
            column_balance_time_min = experiment_info.get('column_balance_time_min', 0)

            # 计算总时间：运行时间 + 吹扫柱时间 + 柱平衡时间
            total_minutes = run_time_min + purge_column_time_min + column_balance_time_min

            # 如果计算结果为0或异常，使用默认值30分钟
            if total_minutes <= 0:
                total_minutes = 30

            estimated_duration = timedelta(minutes=total_minutes)
            logger.info(f"估算完成时间: {total_minutes}分钟 (运行:{run_time_min} + 吹扫柱:{purge_column_time_min} + 柱平衡:{column_balance_time_min})")
            return datetime.now() + estimated_duration

        except Exception as e:
            logger.error(f"估算完成时间失败: {e}")
            # 出错时使用默认值
            estimated_duration = timedelta(minutes=30)
            return datetime.now() + estimated_duration

    def _calculate_total_steps(self, config: ExperimentConfig) -> int:
        """计算总步骤数"""
        try:
            # 从缓存中获取实验信息
            experiment_info = self._get_cached_data(config.experiment_id, 'experiment_info')

            total_steps = 0

            # 根据experiments表中的开关字段计算预处理步骤
            if experiment_info.get('purge_system') == 1:
                total_steps += 1  # 吹扫系统步骤

            if experiment_info.get('purge_column') == 1:
                total_steps += 1  # 吹扫柱子步骤

            if experiment_info.get('column_balance') == 1:
                total_steps += 1  # 柱平衡步骤

            # 固定步骤：收集 + 后处理
            total_steps += 1  # 收集步骤
            total_steps += 1  # 后处理步骤

            logger.info(f"计算总步骤数: {total_steps} "
                       f"(吹扫系统:{experiment_info.get('purge_system', 0)} + "
                       f"吹扫柱子:{experiment_info.get('purge_column', 0)} + "
                       f"柱平衡:{experiment_info.get('column_balance', 0)} + "
                       f"收集:1 + 后处理:1)")

            return max(total_steps, 2)  # 至少2个步骤（收集 + 后处理）

        except Exception as e:
            logger.error(f"计算总步骤数失败: {e}")
            return 2  # 默认2个步骤（最少步骤数）


    async def _get_method_info_from_db(self, method_id: str, experiment_id: str = None) -> Dict[str, Any]:
        """从数据库获取方法信息（优先从缓存获取）"""
        # 如果提供了experiment_id，优先从缓存获取
        if experiment_id and experiment_id in self.experiment_data_cache:
            method_info = self._get_cached_data(experiment_id, 'method_info')
            if method_info:
                logger.debug(f"从缓存获取方法信息: {method_id} -> {method_info}")
                return method_info

        # 缓存中没有，从数据库查询
        try:
            # 通过method_id查询方法信息
            methods = self.db.get_methods(method_id=int(method_id))

            if not methods:
                logger.warning(f"未找到方法ID: {method_id}，使用默认值")
                return {
                    'flow_rate_ml_min': 1.0,  # 默认流速 1 ml/min
                    'method_name': f'Method_{method_id}',
                    'collection_volume_ml': 2.0  # 默认收集体积
                }

            method_info = methods[0]
            logger.info(f"从数据库获取方法信息: {method_id} -> {method_info}")
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
            # 使用标准日志记录而不是数据库
            logger.info(f"实验事件 [{experiment_id}]: {event_type}, 详情: {details}")
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

            # 生成唯一的history_id并保存
            history_id = f"hist_{uuid.uuid4().hex[:12]}_{int(time.time())}"
            self.experiment_history_ids[experiment_id] = history_id
            logger.info(f"生成实验历史ID: {experiment_id} -> {history_id}")

            logger.info(f"开始信号数据收集: {experiment_id}")

            # 启动定时备份任务（每30秒）
            backup_task = asyncio.create_task(self._backup_signal_data_loop(experiment_id))
            self.backup_tasks[experiment_id] = backup_task
            logger.info(f"启动信号数据备份任务: {experiment_id} (每30秒备份)")

            # 发布信号收集开始状态
            await self.mqtt_manager.publish_data(
                "experiments/signal_status",
                {
                    "experiment_id": experiment_id,
                    "action": "start_collection",
                    "history_id": history_id,
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

            # 停止并清理备份任务
            if experiment_id in self.backup_tasks:
                backup_task = self.backup_tasks[experiment_id]
                if not backup_task.done():
                    backup_task.cancel()
                    try:
                        await backup_task
                    except asyncio.CancelledError:
                        pass
                del self.backup_tasks[experiment_id]
                logger.info(f"已停止信号数据备份任务: {experiment_id}")

            # 执行最后一次备份
            if len(progress.detector_signal_cache) > 0:
                await self._backup_elution_curve_to_db(experiment_id)
                logger.info(f"执行最终备份: {experiment_id}")

            logger.info(f"停止信号数据收集: {experiment_id}, 共收集 {len(progress.detector_signal_cache)} 个数据点")

            # 发布信号收集停止状态和最终数据
            history_id = self.experiment_history_ids.get(experiment_id, "")
            await self.mqtt_manager.publish_data(
                "experiments/signal_final",
                {
                    "experiment_id": experiment_id,
                    "action": "stop_collection",
                    "history_id": history_id,
                    "total_signal_points": len(progress.detector_signal_cache),
                    "signal_data_sample": progress.detector_signal_cache[-10:] if progress.detector_signal_cache else [],  # 最后10个数据点
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 取消订阅信号主题
            await self.mqtt_manager.unsubscribe_topic(self.detector_signal_topic)

            # 清理history_id
            if experiment_id in self.experiment_history_ids:
                del self.experiment_history_ids[experiment_id]

        except Exception as e:
            logger.error(f"停止信号收集时出错: {e}")

    async def _backup_signal_data_loop(self, experiment_id: str):
        """定时备份信号数据循环任务（每30秒）"""
        try:
            logger.info(f"启动信号数据备份循环: {experiment_id}")
            last_backup_count = 0  # 上次备份时的数据点数量

            while (experiment_id in self.running_experiments and
                   experiment_id in self.backup_tasks):

                try:
                    progress = self.running_experiments[experiment_id]
                    current_count = len(progress.detector_signal_cache)

                    # 如果有新数据且信号收集处于活跃状态，进行备份
                    if (current_count > last_backup_count and
                        progress.signal_collection_active and
                        progress.current_status == ExperimentStatus.RUNNING):

                        await self._backup_elution_curve_to_db(experiment_id)
                        last_backup_count = current_count
                        logger.debug(f"备份信号数据: {experiment_id}, 数据点数量: {current_count}")

                    # 等待30秒
                    await asyncio.sleep(30)

                except Exception as e:
                    logger.error(f"备份信号数据时出错 [{experiment_id}]: {e}")
                    await asyncio.sleep(30)  # 出错也等待30秒再试

        except asyncio.CancelledError:
            logger.info(f"信号数据备份任务被取消: {experiment_id}")
        except Exception as e:
            logger.error(f"备份循环任务异常 [{experiment_id}]: {e}")

    async def _backup_elution_curve_to_db(self, experiment_id: str):
        """备份洗脱曲线数据到数据库的experiment_history表"""
        try:
            if experiment_id not in self.running_experiments:
                logger.warning(f"实验未找到，跳过备份: {experiment_id}")
                return

            progress = self.running_experiments[experiment_id]
            history_id = self.experiment_history_ids.get(experiment_id)

            if not history_id:
                logger.error(f"未找到history_id，跳过备份: {experiment_id}")
                return

            # 获取信号数据（保持原格式：[[signal_a, signal_b], ...]）
            signal_data = progress.detector_signal_cache.copy()

            if not signal_data:
                logger.debug(f"没有信号数据，跳过备份: {experiment_id}")
                return

            # 构建洗脱曲线JSON数据
            elution_curve_data = {
                "experiment_id": experiment_id,
                "history_id": history_id,
                "data_points": len(signal_data),
                "sampling_rate_hz": 1.0,  # 每秒1个数据点
                "channels": ["A", "B"],  # 双通道
                "signal_data": signal_data,  # [[signal_a, signal_b], ...] 格式，下标=秒数
                "last_updated": datetime.now().isoformat(),
                "backup_info": {
                    "backup_time": datetime.now().isoformat(),
                    "data_format": "array_index_as_seconds",
                    "note": "数组下标代表从实验开始的秒数"
                }
            }

            # 转换为JSON字符串
            elution_curve_json = json.dumps(elution_curve_data, ensure_ascii=False)

            # 检查是否已存在该history_id的记录
            existing_records = self.db.query_data(
                "experiment_history",
                where_condition="history_id = ?",
                where_params=(history_id,)
            )

            current_time = datetime.now().isoformat()

            if existing_records:
                # 更新现有记录
                self.db.update_data(
                    "experiment_history",
                    {
                        "elution_curve": elution_curve_json,
                        "end_time": current_time,
                        "updated_at": current_time
                    },
                    "history_id = ?",
                    (history_id,)
                )
                logger.debug(f"更新洗脱曲线数据: {history_id}, 数据点: {len(signal_data)}")
            else:
                # 创建新记录
                self.db.insert_data("experiment_history", {
                    "history_id": history_id,
                    "experiment_id": int(experiment_id),
                    "start_time": progress.start_time.isoformat() if progress.start_time else current_time,
                    "end_time": current_time,
                    "elution_curve": elution_curve_json,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                logger.info(f"创建洗脱曲线记录: {history_id}, 数据点: {len(signal_data)}")

        except Exception as e:
            logger.error(f"备份洗脱曲线数据失败 [{experiment_id}]: {e}")

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

        # 停止信号数据收集（包含备份任务清理）
        await self._stop_signal_collection(experiment_id)

        # 额外确保备份任务被清理（防止遗漏）
        if experiment_id in self.backup_tasks:
            backup_task = self.backup_tasks[experiment_id]
            if not backup_task.done():
                backup_task.cancel()
            self.backup_tasks.pop(experiment_id, None)

        # 清理history_id（防止遗漏）
        self.experiment_history_ids.pop(experiment_id, None)

        # 清理收集监控任务
        if experiment_id in self.collection_monitor_tasks:
            monitor_task = self.collection_monitor_tasks[experiment_id]
            if not monitor_task.done():
                monitor_task.cancel()
            self.collection_monitor_tasks.pop(experiment_id, None)

        # 移除运行实验和试管管理器
        self.running_experiments.pop(experiment_id, None)
        self.tube_managers.pop(experiment_id, None)
        self.system_busy = False

        # 清理实验数据缓存
        self._clear_experiment_cache(experiment_id)

        # 清理当前实验ID和架子ID
        if self.current_experiment_id == experiment_id:
            self.current_experiment_id = None
            self.current_rack_id = None

        logger.info(f"清理实验资源完成: {experiment_id}, 原因: {reason}")

    # ==================== MQTT收集控制相关方法 ====================

    async def _publish_collection_control(self, experiment_id: str, action: str, data: Dict[str, Any] = None):
        """发布收集控制消息"""
        try:
            control_topic = self.collection_control_topic_template.format(experiment_id)
            control_data = {
                "action": action,
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat()
            }
            if data:
                control_data.update(data)

            await self.mqtt_manager.publish_data(control_topic, control_data)
            logger.debug(f"发布收集控制消息: {control_topic} -> {action}")

        except Exception as e:
            logger.error(f"发布收集控制消息失败: {e}")

    async def _publish_collection_status(self, experiment_id: str, status: str, data: Dict[str, Any] = None):
        """发布收集状态消息"""
        try:
            status_topic = self.collection_status_topic_template.format(experiment_id)
            status_data = {
                "status": status,
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat()
            }
            if data:
                status_data.update(data)

            await self.mqtt_manager.publish_data(status_topic, status_data)
            logger.debug(f"发布收集状态消息: {status_topic} -> {status}")

        except Exception as e:
            logger.error(f"发布收集状态消息失败: {e}")

    async def _subscribe_collection_control(self, experiment_id: str):
        """订阅收集控制消息"""
        try:
            control_topic = self.collection_control_topic_template.format(experiment_id)

            def control_handler(topic: str, data: Any):
                asyncio.create_task(self._handle_collection_control(experiment_id, data))

            success = await self.mqtt_manager.subscribe_topic(control_topic, control_handler)
            if success:
                logger.info(f"订阅收集控制消息成功: {control_topic}")
            else:
                logger.error(f"订阅收集控制消息失败: {control_topic}")

        except Exception as e:
            logger.error(f"订阅收集控制消息时出错: {e}")

    async def _unsubscribe_collection_control(self, experiment_id: str):
        """取消订阅收集控制消息"""
        try:
            control_topic = self.collection_control_topic_template.format(experiment_id)
            await self.mqtt_manager.unsubscribe_topic(control_topic)
            logger.info(f"取消订阅收集控制消息: {control_topic}")

        except Exception as e:
            logger.error(f"取消订阅收集控制消息时出错: {e}")

    async def _handle_collection_control(self, experiment_id: str, control_data: Dict[str, Any]):
        """处理收集控制消息"""
        try:
            if experiment_id not in self.running_experiments:
                logger.warning(f"收到未知实验的控制消息: {experiment_id}")
                return

            action = control_data.get("action")
            logger.info(f"处理收集控制消息: {experiment_id} -> {action}")

            if action == "pause_collection":
                await self._handle_mqtt_pause(experiment_id, control_data)
            elif action == "resume_collection":
                await self._handle_mqtt_resume(experiment_id, control_data)
            elif action == "stop_collection":
                await self._handle_mqtt_stop(experiment_id, control_data)
            elif action == "start_collection":
                logger.info(f"MQTT开始收集: {experiment_id}")
                # 开始收集消息主要用于日志记录
            else:
                logger.warning(f"未知的收集控制动作: {action}")

        except Exception as e:
            logger.error(f"处理收集控制消息时出错: {e}")

    async def _handle_mqtt_pause(self, experiment_id: str, control_data: Dict[str, Any]):
        """处理MQTT暂停消息"""
        try:
            progress = self.running_experiments[experiment_id]

            # 记录暂停时的实验时间点和现实时间
            progress.pause_experiment_time = self._get_experiment_elapsed_time(experiment_id)
            progress.pause_real_time = time.time()

            logger.info(f"MQTT暂停收集: {experiment_id}, 暂停在实验第{progress.pause_experiment_time:.1f}秒")

            # 暂停各个组件
            await self._pause_signal_collection(experiment_id)
            await self._pause_gradient_and_integration(experiment_id)

        except Exception as e:
            logger.error(f"处理MQTT暂停消息时出错: {e}")

    async def _handle_mqtt_resume(self, experiment_id: str, control_data: Dict[str, Any]):
        """处理MQTT恢复消息"""
        try:
            progress = self.running_experiments[experiment_id]

            # 调整时间基准（补偿暂停时间）
            if progress.pause_real_time is not None and progress.pause_experiment_time is not None:
                pause_duration = time.time() - progress.pause_real_time
                progress.experiment_start_timestamp += pause_duration

                logger.info(f"MQTT恢复收集: {experiment_id}, 暂停了{pause_duration:.1f}秒, 从实验第{progress.pause_experiment_time:.1f}秒继续")

                # 清理暂停相关属性
                progress.pause_real_time = None
                progress.pause_experiment_time = None

            # 恢复各个组件
            await self._resume_signal_collection(experiment_id)
            try:
                config_data = self._get_cached_data(experiment_id, 'config')
                if config_data:
                    from models.experiment_function_models import ExperimentConfig
                    config = ExperimentConfig(**config_data)
                    await self._resume_gradient_and_integration(experiment_id, config)
                    logger.info(f"梯度执行已恢复: {experiment_id}")
            except Exception as e:
                logger.error(f"恢复梯度执行失败: {e}")

        except Exception as e:
            logger.error(f"处理MQTT恢复消息时出错: {e}")

    async def _handle_mqtt_stop(self, experiment_id: str, control_data: Dict[str, Any]):
        """处理MQTT停止消息"""
        try:
            logger.info(f"MQTT停止收集: {experiment_id}")

            # 停止各个组件
            await self._stop_signal_collection(experiment_id)
            await self._stop_gradient_execution(experiment_id)

            # 停止收集监控任务
            if experiment_id in self.collection_monitor_tasks:
                monitor_task = self.collection_monitor_tasks[experiment_id]
                if not monitor_task.done():
                    monitor_task.cancel()
                del self.collection_monitor_tasks[experiment_id]

        except Exception as e:
            logger.error(f"处理MQTT停止消息时出错: {e}")

    async def _start_collection_monitor(self, experiment_id: str):
        """启动独立的收集监控任务"""
        try:
            logger.info(f"启动收集监控任务: {experiment_id}")

            # 订阅收集控制消息
            await self._subscribe_collection_control(experiment_id)

            # 启动试管收集检查任务
            collection_check_task = asyncio.create_task(
                self._collection_check_loop(experiment_id)
            )

            try:
                # 等待实验完成或被取消
                while (experiment_id in self.running_experiments and
                       self.running_experiments[experiment_id].current_status in
                       [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]):
                    await asyncio.sleep(1)

                logger.info(f"收集监控任务正常结束: {experiment_id}")

            finally:
                # 清理任务
                collection_check_task.cancel()
                try:
                    await collection_check_task
                except asyncio.CancelledError:
                    pass
                await self._unsubscribe_collection_control(experiment_id)

        except asyncio.CancelledError:
            logger.info(f"收集监控任务被取消: {experiment_id}")
        except Exception as e:
            logger.error(f"收集监控任务异常: {e}")

    async def _collection_check_loop(self, experiment_id: str):
        """收集完成检查循环 - 使用实验逻辑时间"""
        try:
            logger.info(f"启动收集检查循环: {experiment_id}")

            while experiment_id in self.running_experiments:
                progress = self.running_experiments[experiment_id]

                # 只在运行状态下检查收集完成
                if progress.current_status == ExperimentStatus.RUNNING:
                    tube_manager = self.tube_managers.get(experiment_id)
                    if tube_manager:
                        experiment_elapsed_time = self._get_experiment_elapsed_time(experiment_id)

                        if tube_manager.is_collection_complete(progress.tube_start_time, experiment_elapsed_time):
                            # 直接处理试管收集完成
                            await self._handle_tube_collection_complete(experiment_id, progress, experiment_elapsed_time)

                await asyncio.sleep(1)  # 每秒检查一次

        except asyncio.CancelledError:
            logger.info(f"收集检查循环被取消: {experiment_id}")
        except Exception as e:
            logger.error(f"收集检查循环异常: {e}")

    async def _get_current_rack_info(self) -> Dict[str, Any]:
        """从数据库获取当前使用的架子信息"""
        try:
            # 首先查询所有架子，然后筛选状态为"使用"的
            all_racks = self.db.get_rack_info()
            active_racks = [rack for rack in all_racks if rack.get('status') == '使用']

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
            # TODO: 实现从数据库获取关键报警信息的功能

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

    def _get_experiment_elapsed_time(self, experiment_id: str) -> float:
        """获取实验已运行时间（排除暂停时间）"""
        if experiment_id not in self.running_experiments:
            return 0.0

        progress = self.running_experiments[experiment_id]

        if progress.current_status == ExperimentStatus.PAUSED:
            # 暂停状态返回暂停时的时间点
            return progress.pause_experiment_time or 0.0
        else:
            # 运行状态返回当前实验时间
            return time.time() - progress.experiment_start_timestamp

    async def _preload_experiment_data(self, config: ExperimentConfig) -> Dict[str, Any]:
        """预加载实验相关的所有数据，避免后续重复查询数据库"""
        try:
            experiment_id = config.experiment_id

            # 获取方法信息
            method_info = {}
            try:
                methods = self.db.get_methods(method_id=int(config.method_id))
                if methods and len(methods) > 0:
                    method_info = methods[0]
                    logger.info(f"预加载方法信息: {config.method_id} -> {method_info}")
                else:
                    logger.warning(f"未找到方法ID: {config.method_id}，使用默认值")
                    method_info = {
                        'flow_rate_ml_min': 1.0,
                        'method_name': f'Method_{config.method_id}',
                        'collection_volume_ml': 2.0,
                        'run_time_min': 30,
                        'gradient_time_table': []
                    }
            except Exception as e:
                logger.error(f"获取方法信息失败: {e}")
                method_info = {
                    'flow_rate_ml_min': 1.0,
                    'method_name': 'Default_Method',
                    'collection_volume_ml': 2.0,
                    'run_time_min': 30,
                    'gradient_time_table': {}
                }

            # 获取实验信息
            experiment_info = {}
            try:
                experiments = self.db.query_data(
                    "experiments",
                    where_condition="id = ?",
                    where_params=(int(config.experiment_id),)
                )
                if experiments and len(experiments) > 0:
                    experiment_info = experiments[0]
                    logger.info(f"预加载实验信息: {config.experiment_id} -> {experiment_info}")
                else:
                    logger.warning(f"未找到实验ID: {config.experiment_id}，使用默认值")
                    experiment_info = {
                        'purge_column_time_min': 5,
                        'column_balance_time_min': 10,
                        'collection_volume_ml': 2.0
                    }
            except Exception as e:
                logger.error(f"获取实验信息失败: {e}")
                experiment_info = {
                    'purge_column_time_min': 5,
                    'column_balance_time_min': 10,
                    'collection_volume_ml': 2.0
                }

            # 获取架子信息
            rack_info = await self._get_current_rack_info()

            # 组装缓存数据
            cached_data = {
                'method_info': method_info,
                'experiment_info': experiment_info,
                'rack_info': rack_info,
                'config': config.dict()
            }

            # 存储到缓存
            self.experiment_data_cache[experiment_id] = cached_data

            logger.info(f"实验数据预加载完成: {experiment_id}")
            return cached_data

        except Exception as e:
            logger.error(f"预加载实验数据失败: {e}")
            # 即使预加载失败，也要确保有基本的缓存结构
            self.experiment_data_cache[config.experiment_id] = {
                'method_info': {'flow_rate_ml_min': 1.0, 'run_time_min': 30},
                'experiment_info': {'purge_column_time_min': 5, 'column_balance_time_min': 10},
                'rack_info': {'rack_id': 'rack_001', 'tube_count': 40},
                'config': config.dict()
            }
            return self.experiment_data_cache[config.experiment_id]

    def _get_cached_data(self, experiment_id: str, data_type: str) -> Dict[str, Any]:
        """从缓存中获取特定类型的数据"""
        if experiment_id not in self.experiment_data_cache:
            logger.warning(f"实验数据缓存未找到: {experiment_id}")
            return {}

        cached_data = self.experiment_data_cache[experiment_id]
        return cached_data.get(data_type, {})

    def _clear_experiment_cache(self, experiment_id: str):
        """清理指定实验的缓存数据"""
        if experiment_id in self.experiment_data_cache:
            del self.experiment_data_cache[experiment_id]
            logger.info(f"清理实验缓存数据: {experiment_id}")
        else:
            logger.warning(f"要清理的实验缓存不存在: {experiment_id}")