"""
梯度曲线管理器
Gradient Curve Manager
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from models.gradient_models import (
    GradientProgram,
    GradientStep,
    GradientCurve,
    GradientExecution,
    GradientProfile,
    FlowControlType
)

logger = logging.getLogger(__name__)


class GradientCurveManager:
    """梯度曲线管理器"""

    def __init__(self, mqtt_manager: MQTTManager, db_manager: DatabaseManager):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.current_execution: Optional[GradientExecution] = None
        self.gradient_cache: Dict[str, GradientProgram] = {}
        self.execution_history: List[GradientExecution] = []

    async def create_gradient_curve(self, program: GradientProgram) -> GradientCurve:
        """根据梯度程序创建梯度曲线"""
        logger.info(f"创建梯度曲线: {program.program_name}")

        # 验证梯度程序
        validation_result = await self.validate_gradient_program(program)
        if not validation_result["valid"]:
            raise ValueError(f"梯度程序无效: {validation_result['errors']}")

        # 生成时间点和流动相比例
        time_points, mobile_phase_ratios = await self._generate_curve_points(program)

        # 计算流速曲线
        flow_rate_curve = await self._calculate_flow_rate_curve(program, time_points)

        # 创建梯度曲线
        curve = GradientCurve(
            curve_id=f"curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            program_id=program.program_id,
            program_name=program.program_name,
            total_duration_minutes=program.total_duration_minutes,
            time_points=time_points,
            mobile_phase_a_ratios=mobile_phase_ratios["A"],
            mobile_phase_b_ratios=mobile_phase_ratios["B"],
            mobile_phase_c_ratios=mobile_phase_ratios.get("C", []),
            mobile_phase_d_ratios=mobile_phase_ratios.get("D", []),
            flow_rate_curve=flow_rate_curve,
            curve_resolution_seconds=program.curve_resolution_seconds,
            generated_at=datetime.now()
        )

        # 缓存梯度曲线
        self.gradient_cache[curve.curve_id] = program

        # 记录创建事件
        await self._log_gradient_event(
            "curve_created",
            f"创建梯度曲线: {curve.program_name}",
            {"curve_id": curve.curve_id, "program_id": program.program_id}
        )

        logger.info(f"梯度曲线创建成功: {curve.curve_id}")
        return curve

    async def execute_gradient(self, curve: GradientCurve, experiment_id: str) -> GradientExecution:
        """执行梯度曲线"""
        logger.info(f"开始执行梯度: {curve.curve_id} for experiment {experiment_id}")

        if self.current_execution:
            raise ValueError("已有梯度在执行中，无法启动新的梯度")

        # 创建执行记录
        execution = GradientExecution(
            execution_id=f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            curve_id=curve.curve_id,
            experiment_id=experiment_id,
            start_time=datetime.now(),
            current_step_index=0,
            current_time_minutes=0.0,
            current_mobile_phase_ratios={"A": curve.mobile_phase_a_ratios[0], "B": curve.mobile_phase_b_ratios[0]},
            current_flow_rate=curve.flow_rate_curve[0] if curve.flow_rate_curve else 1.0,
            status="running"
        )

        self.current_execution = execution

        try:
            # 发布执行开始消息
            await self.mqtt_manager.publish_data(
                "gradient/execution_started",
                {
                    "execution_id": execution.execution_id,
                    "curve_id": curve.curve_id,
                    "experiment_id": experiment_id,
                    "total_duration": curve.total_duration_minutes,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 启动执行任务
            asyncio.create_task(self._execute_gradient_curve(curve, execution))

            return execution

        except Exception as e:
            self.current_execution = None
            logger.error(f"启动梯度执行失败: {e}")
            raise

    async def pause_gradient(self, execution_id: str) -> bool:
        """暂停梯度执行"""
        if not self.current_execution or self.current_execution.execution_id != execution_id:
            raise ValueError(f"执行 {execution_id} 未找到或未运行")

        logger.info(f"暂停梯度执行: {execution_id}")
        self.current_execution.status = "paused"

        await self.mqtt_manager.publish_data(
            "gradient/execution_paused",
            {
                "execution_id": execution_id,
                "current_time": self.current_execution.current_time_minutes,
                "timestamp": datetime.now().isoformat()
            }
        )

        return True

    async def resume_gradient(self, execution_id: str) -> bool:
        """恢复梯度执行"""
        if not self.current_execution or self.current_execution.execution_id != execution_id:
            raise ValueError(f"执行 {execution_id} 未找到")

        if self.current_execution.status != "paused":
            raise ValueError(f"执行状态不允许恢复: {self.current_execution.status}")

        logger.info(f"恢复梯度执行: {execution_id}")
        self.current_execution.status = "running"

        await self.mqtt_manager.publish_data(
            "gradient/execution_resumed",
            {
                "execution_id": execution_id,
                "current_time": self.current_execution.current_time_minutes,
                "timestamp": datetime.now().isoformat()
            }
        )

        return True

    async def stop_gradient(self, execution_id: str, reason: str = None) -> bool:
        """停止梯度执行"""
        if not self.current_execution or self.current_execution.execution_id != execution_id:
            raise ValueError(f"执行 {execution_id} 未找到或未运行")

        logger.info(f"停止梯度执行: {execution_id}, 原因: {reason}")

        self.current_execution.status = "stopped"
        self.current_execution.end_time = datetime.now()
        self.current_execution.stop_reason = reason

        # 添加到历史记录
        self.execution_history.append(self.current_execution)

        await self.mqtt_manager.publish_data(
            "gradient/execution_stopped",
            {
                "execution_id": execution_id,
                "reason": reason,
                "final_time": self.current_execution.current_time_minutes,
                "timestamp": datetime.now().isoformat()
            }
        )

        self.current_execution = None
        return True

    async def get_gradient_status(self) -> Optional[Dict[str, Any]]:
        """获取当前梯度状态"""
        if not self.current_execution:
            return None

        return {
            "execution_id": self.current_execution.execution_id,
            "curve_id": self.current_execution.curve_id,
            "experiment_id": self.current_execution.experiment_id,
            "status": self.current_execution.status,
            "current_time_minutes": self.current_execution.current_time_minutes,
            "progress_percentage": self._calculate_progress_percentage(),
            "current_mobile_phase_ratios": self.current_execution.current_mobile_phase_ratios,
            "current_flow_rate": self.current_execution.current_flow_rate,
            "estimated_completion": self._estimate_completion_time()
        }

    async def validate_gradient_program(self, program: GradientProgram) -> Dict[str, Any]:
        """验证梯度程序"""
        errors = []
        warnings = []

        # 基本验证
        if not program.program_name:
            errors.append("程序名称不能为空")

        if not program.steps:
            errors.append("梯度步骤不能为空")

        if program.total_duration_minutes <= 0:
            errors.append("总时长必须大于0")

        # 步骤验证
        total_step_time = 0
        for i, step in enumerate(program.steps):
            if step.duration_minutes <= 0:
                errors.append(f"步骤 {i+1} 时长必须大于0")

            if step.mobile_phase_a_percent < 0 or step.mobile_phase_a_percent > 100:
                errors.append(f"步骤 {i+1} 流动相A比例必须在0-100%之间")

            if step.mobile_phase_b_percent < 0 or step.mobile_phase_b_percent > 100:
                errors.append(f"步骤 {i+1} 流动相B比例必须在0-100%之间")

            # 检查总比例
            total_percent = step.mobile_phase_a_percent + step.mobile_phase_b_percent
            if hasattr(step, 'mobile_phase_c_percent') and step.mobile_phase_c_percent:
                total_percent += step.mobile_phase_c_percent
            if hasattr(step, 'mobile_phase_d_percent') and step.mobile_phase_d_percent:
                total_percent += step.mobile_phase_d_percent

            if abs(total_percent - 100) > 0.1:
                errors.append(f"步骤 {i+1} 流动相总比例必须为100%")

            total_step_time += step.duration_minutes

        # 时间一致性检查
        if abs(total_step_time - program.total_duration_minutes) > 0.1:
            errors.append(f"步骤总时长({total_step_time})与程序总时长({program.total_duration_minutes})不匹配")

        # 流速验证
        if program.flow_rate_ml_min <= 0:
            errors.append("流速必须大于0")
        elif program.flow_rate_ml_min > 10:
            warnings.append("流速超过10 mL/min，请确认是否正确")

        # 梯度合理性检查
        if len(program.steps) > 1:
            for i in range(len(program.steps) - 1):
                current_step = program.steps[i]
                next_step = program.steps[i + 1]

                # 检查梯度变化幅度
                a_change = abs(next_step.mobile_phase_a_percent - current_step.mobile_phase_a_percent)
                if a_change > 50:
                    warnings.append(f"步骤 {i+1} 到 {i+2} 流动相A变化幅度较大({a_change}%)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def create_gradient_profile(self, name: str, steps: List[GradientStep]) -> GradientProfile:
        """创建梯度模板"""
        profile = GradientProfile(
            profile_id=f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            profile_name=name,
            description=f"梯度模板: {name}",
            steps=steps,
            created_at=datetime.now()
        )

        # 记录创建事件
        await self._log_gradient_event(
            "profile_created",
            f"创建梯度模板: {name}",
            {"profile_id": profile.profile_id}
        )

        return profile

    async def _generate_curve_points(self, program: GradientProgram) -> Tuple[List[float], Dict[str, List[float]]]:
        """生成梯度曲线数据点"""
        resolution = program.curve_resolution_seconds
        total_seconds = program.total_duration_minutes * 60
        num_points = int(total_seconds / resolution) + 1

        time_points = [i * resolution / 60 for i in range(num_points)]  # 转换为分钟
        mobile_phase_ratios = {"A": [], "B": [], "C": [], "D": []}

        current_time = 0
        step_index = 0

        for time_point in time_points:
            # 找到当前时间点对应的步骤
            while step_index < len(program.steps) - 1:
                step_end_time = sum(step.duration_minutes for step in program.steps[:step_index + 1])
                if time_point <= step_end_time:
                    break
                step_index += 1

            current_step = program.steps[step_index]

            # 如果是梯度步骤，需要插值计算
            if step_index > 0 and current_step.gradient_type == "linear":
                prev_step = program.steps[step_index - 1]
                step_start_time = sum(step.duration_minutes for step in program.steps[:step_index])
                step_progress = (time_point - step_start_time) / current_step.duration_minutes
                step_progress = max(0, min(1, step_progress))

                # 线性插值
                a_ratio = prev_step.mobile_phase_a_percent + (current_step.mobile_phase_a_percent - prev_step.mobile_phase_a_percent) * step_progress
                b_ratio = prev_step.mobile_phase_b_percent + (current_step.mobile_phase_b_percent - prev_step.mobile_phase_b_percent) * step_progress
            else:
                # 等度步骤
                a_ratio = current_step.mobile_phase_a_percent
                b_ratio = current_step.mobile_phase_b_percent

            mobile_phase_ratios["A"].append(a_ratio)
            mobile_phase_ratios["B"].append(b_ratio)
            mobile_phase_ratios["C"].append(getattr(current_step, 'mobile_phase_c_percent', 0))
            mobile_phase_ratios["D"].append(getattr(current_step, 'mobile_phase_d_percent', 0))

        return time_points, mobile_phase_ratios

    async def _calculate_flow_rate_curve(self, program: GradientProgram, time_points: List[float]) -> List[float]:
        """计算流速曲线"""
        flow_rates = []

        for time_point in time_points:
            # 简化处理，使用恒定流速
            # 实际实现中可以根据压力反馈动态调整
            flow_rates.append(program.flow_rate_ml_min)

        return flow_rates

    async def _execute_gradient_curve(self, curve: GradientCurve, execution: GradientExecution):
        """执行梯度曲线的主要逻辑"""
        try:
            start_time = datetime.now()
            total_duration_seconds = curve.total_duration_minutes * 60
            resolution_seconds = curve.curve_resolution_seconds

            for i, time_point in enumerate(curve.time_points):
                if execution.status != "running":
                    # 暂停或停止
                    if execution.status == "paused":
                        while execution.status == "paused":
                            await asyncio.sleep(0.1)
                    elif execution.status == "stopped":
                        break

                # 更新执行状态
                execution.current_step_index = i
                execution.current_time_minutes = time_point
                execution.current_mobile_phase_ratios = {
                    "A": curve.mobile_phase_a_ratios[i],
                    "B": curve.mobile_phase_b_ratios[i]
                }
                execution.current_flow_rate = curve.flow_rate_curve[i] if curve.flow_rate_curve else 1.0

                # 发送控制指令到硬件设备
                await self._send_gradient_control_commands(execution)

                # 发布实时状态
                await self.mqtt_manager.publish_data(
                    "gradient/real_time_status",
                    {
                        "execution_id": execution.execution_id,
                        "time_minutes": execution.current_time_minutes,
                        "mobile_phase_ratios": execution.current_mobile_phase_ratios,
                        "flow_rate": execution.current_flow_rate,
                        "progress_percent": self._calculate_progress_percentage(),
                        "timestamp": datetime.now().isoformat()
                    }
                )

                # 等待下一个时间点
                await asyncio.sleep(resolution_seconds)

            # 梯度执行完成
            if execution.status == "running":
                execution.status = "completed"
                execution.end_time = datetime.now()

                await self.mqtt_manager.publish_data(
                    "gradient/execution_completed",
                    {
                        "execution_id": execution.execution_id,
                        "total_duration": curve.total_duration_minutes,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                logger.info(f"梯度执行完成: {execution.execution_id}")

        except Exception as e:
            logger.error(f"梯度执行异常: {e}")
            execution.status = "error"
            execution.error_message = str(e)
            execution.end_time = datetime.now()

        finally:
            # 添加到历史记录
            self.execution_history.append(execution)
            if self.current_execution == execution:
                self.current_execution = None

    async def _send_gradient_control_commands(self, execution: GradientExecution):
        """发送梯度控制指令到硬件设备"""
        try:
            # 发送流动相比例控制指令
            await self.mqtt_manager.publish_data(
                "hardware/gradient_control",
                {
                    "mobile_phase_a": execution.current_mobile_phase_ratios["A"],
                    "mobile_phase_b": execution.current_mobile_phase_ratios["B"],
                    "flow_rate": execution.current_flow_rate,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"发送梯度控制指令失败: {e}")

    def _calculate_progress_percentage(self) -> float:
        """计算进度百分比"""
        if not self.current_execution:
            return 0.0

        curve = self.gradient_cache.get(self.current_execution.curve_id)
        if not curve:
            return 0.0

        return (self.current_execution.current_time_minutes / curve.total_duration_minutes) * 100

    def _estimate_completion_time(self) -> Optional[datetime]:
        """估算完成时间"""
        if not self.current_execution:
            return None

        curve = self.gradient_cache.get(self.current_execution.curve_id)
        if not curve:
            return None

        remaining_minutes = curve.total_duration_minutes - self.current_execution.current_time_minutes
        return datetime.now() + timedelta(minutes=remaining_minutes)

    async def _log_gradient_event(self, event_type: str, description: str, details: Dict[str, Any]):
        """记录梯度事件"""
        try:
            await self.db_manager.log_system_event(
                event_type,
                "info",
                "gradient_manager",
                description,
                details
            )
        except Exception as e:
            logger.error(f"记录梯度事件失败: {e}")

    async def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return [
            {
                "execution_id": exec.execution_id,
                "curve_id": exec.curve_id,
                "experiment_id": exec.experiment_id,
                "start_time": exec.start_time,
                "end_time": exec.end_time,
                "status": exec.status,
                "duration_minutes": (exec.end_time - exec.start_time).total_seconds() / 60 if exec.end_time else None
            }
            for exec in self.execution_history[-limit:]
        ]