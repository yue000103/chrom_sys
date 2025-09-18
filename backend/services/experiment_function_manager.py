"""
实验功能管理器
Experiment Function Manager
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models.experiment_function_models import (
    ExperimentConfig,
    ExperimentProgress,
    ExperimentControl,
    ExperimentResult,
    ExperimentQueue,
    ExperimentStatus,
    ExperimentPhase
)
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class ExperimentFunctionManager:
    """实验功能管理器"""

    def __init__(self, mqtt_manager: MQTTManager, db_manager: DatabaseManager):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.running_experiments: Dict[str, ExperimentProgress] = {}
        self.experiment_queue: List[ExperimentConfig] = []
        self.system_busy = False

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

        # 添加到运行实验列表
        self.running_experiments[config.experiment_id] = progress
        self.system_busy = True

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
            self.system_busy = False
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
        """停止实验"""
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

        # 移除运行实验
        self.running_experiments.pop(experiment_id, None)
        self.system_busy = False

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

    async def add_to_queue(self, config: ExperimentConfig) -> int:
        """添加实验到队列"""
        logger.info(f"添加实验到队列: {config.experiment_name}")

        # 验证实验配置
        validation_result = await self._validate_experiment_config(config)
        if not validation_result["valid"]:
            raise ValueError(f"实验配置无效: {validation_result['errors']}")

        self.experiment_queue.append(config)
        position = len(self.experiment_queue)

        # 记录队列事件
        await self._log_experiment_event(
            config.experiment_id,
            "experiment_queued",
            {"position": position, "config": config.dict()}
        )

        return position

    async def remove_from_queue(self, experiment_id: str) -> bool:
        """从队列中移除实验"""
        for i, config in enumerate(self.experiment_queue):
            if config.experiment_id == experiment_id:
                removed_config = self.experiment_queue.pop(i)
                logger.info(f"从队列移除实验: {removed_config.experiment_name}")

                await self._log_experiment_event(
                    experiment_id,
                    "experiment_removed_from_queue",
                    {"position": i + 1}
                )
                return True
        return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_length": len(self.experiment_queue),
            "experiments": [
                {
                    "experiment_id": config.experiment_id,
                    "experiment_name": config.experiment_name,
                    "position": i + 1,
                    "estimated_start_time": self._estimate_queue_start_time(i)
                }
                for i, config in enumerate(self.experiment_queue)
            ],
            "system_busy": self.system_busy
        }

    async def _execute_experiment(self, config: ExperimentConfig):
        """执行实验的主要逻辑"""
        experiment_id = config.experiment_id
        progress = self.running_experiments[experiment_id]

        try:
            # 阶段1: 实验前准备
            await self._execute_pre_experiment_phase(experiment_id, progress)

            # 阶段2: 实验进行中
            await self._execute_during_experiment_phase(experiment_id, progress)

            # 阶段3: 实验后处理
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
            self.running_experiments.pop(experiment_id, None)
            self.system_busy = False

            # 如果有队列中的实验，自动开始下一个
            if self.experiment_queue and not self.system_busy:
                next_experiment = self.experiment_queue.pop(0)
                asyncio.create_task(self.start_experiment(next_experiment))

    async def _execute_pre_experiment_phase(self, experiment_id: str, progress: ExperimentProgress):
        """执行实验前准备阶段"""
        progress.current_phase = ExperimentPhase.PRE_EXPERIMENT
        progress.current_step = "系统检查"
        progress.progress_percentage = 10.0

        # 模拟系统检查
        await asyncio.sleep(2)

        progress.current_step = "准备试剂"
        progress.progress_percentage = 20.0
        await asyncio.sleep(1)

        progress.current_step = "设备校准"
        progress.progress_percentage = 30.0
        await asyncio.sleep(1)

    async def _execute_during_experiment_phase(self, experiment_id: str, progress: ExperimentProgress):
        """执行实验进行中阶段"""
        progress.current_phase = ExperimentPhase.DURING_EXPERIMENT
        progress.current_step = "样品进样"
        progress.progress_percentage = 40.0

        # 模拟实验过程
        await asyncio.sleep(3)

        progress.current_step = "色谱分离"
        progress.progress_percentage = 60.0
        await asyncio.sleep(5)

        progress.current_step = "信号检测"
        progress.progress_percentage = 80.0
        await asyncio.sleep(2)

    async def _execute_post_experiment_phase(self, experiment_id: str, progress: ExperimentProgress):
        """执行实验后处理阶段"""
        progress.current_phase = ExperimentPhase.POST_EXPERIMENT
        progress.current_step = "数据处理"
        progress.progress_percentage = 85.0

        # 模拟后处理
        await asyncio.sleep(2)

        progress.current_step = "结果分析"
        progress.progress_percentage = 95.0
        await asyncio.sleep(1)

        progress.current_step = "清洗系统"
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
        # 简单估算，实际应根据方法参数计算
        estimated_duration = timedelta(minutes=30)  # 默认30分钟
        return datetime.now() + estimated_duration

    def _calculate_total_steps(self, config: ExperimentConfig) -> int:
        """计算总步骤数"""
        # 简单计算，实际应根据方法复杂度
        return 10  # 默认10个步骤

    def _estimate_queue_start_time(self, position: int) -> Optional[datetime]:
        """估算队列中实验的开始时间"""
        if self.system_busy:
            # 如果系统忙碌，基于当前实验估算
            estimated_remaining = timedelta(minutes=20)  # 简化估算
            start_time = datetime.now() + estimated_remaining
        else:
            start_time = datetime.now()

        # 加上前面实验的估算时间
        for i in range(position):
            start_time += timedelta(minutes=30)  # 每个实验估算30分钟

        return start_time

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