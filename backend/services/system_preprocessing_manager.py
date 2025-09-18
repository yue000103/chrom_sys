"""
系统预处理管理器
System Preprocessing Manager
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from models.system_preprocessing_models import (
    SystemCheckConfig,
    SystemCheckResult,
    PreprocessingSequence,
    PreprocessingStep,
    CalibrationResult,
    SystemReadinessResult
)
from models.base_models import DeviceStatus

logger = logging.getLogger(__name__)


class SystemPreprocessingManager:
    """系统预处理管理器"""

    def __init__(self, mqtt_manager: MQTTManager, db_manager: DatabaseManager):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.current_sequence: Optional[PreprocessingSequence] = None
        self.system_ready = False
        self.last_check_time: Optional[datetime] = None

    async def perform_system_check(self, config: SystemCheckConfig) -> SystemCheckResult:
        """执行系统检查"""
        logger.info("开始执行系统检查...")
        start_time = datetime.now()

        check_results = []
        failed_checks = []

        try:
            # 1. 设备连接检查
            if config.check_device_connections:
                device_result = await self._check_device_connections()
                check_results.append(device_result)
                if not device_result["success"]:
                    failed_checks.append("device_connections")

            # 2. 压力系统检查
            if config.check_pressure_system:
                pressure_result = await self._check_pressure_system()
                check_results.append(pressure_result)
                if not pressure_result["success"]:
                    failed_checks.append("pressure_system")

            # 3. 检测器检查
            if config.check_detector:
                detector_result = await self._check_detector_system()
                check_results.append(detector_result)
                if not detector_result["success"]:
                    failed_checks.append("detector_system")

            # 4. 泵系统检查
            if config.check_pump_system:
                pump_result = await self._check_pump_system()
                check_results.append(pump_result)
                if not pump_result["success"]:
                    failed_checks.append("pump_system")

            # 5. 试管架检查
            if config.check_tube_racks:
                rack_result = await self._check_tube_racks()
                check_results.append(rack_result)
                if not rack_result["success"]:
                    failed_checks.append("tube_racks")

            # 6. 温度系统检查
            if config.check_temperature:
                temp_result = await self._check_temperature_system()
                check_results.append(temp_result)
                if not temp_result["success"]:
                    failed_checks.append("temperature_system")

            end_time = datetime.now()
            check_duration = (end_time - start_time).total_seconds()

            # 创建检查结果
            result = SystemCheckResult(
                check_id=f"check_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                start_time=start_time,
                end_time=end_time,
                check_duration_seconds=check_duration,
                total_checks=len(check_results),
                passed_checks=len([r for r in check_results if r["success"]]),
                failed_checks=failed_checks,
                check_details=check_results,
                overall_success=len(failed_checks) == 0,
                system_ready_for_experiment=len(failed_checks) == 0
            )

            self.system_ready = result.system_ready_for_experiment
            self.last_check_time = end_time

            # 记录检查结果
            await self._log_system_check_event(result)

            # 发布MQTT消息
            await self.mqtt_manager.publish_data(
                "system/check_completed",
                {
                    "check_id": result.check_id,
                    "success": result.overall_success,
                    "failed_checks": failed_checks,
                    "duration": check_duration,
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"系统检查完成: {result.overall_success}, 耗时: {check_duration:.2f}秒")
            return result

        except Exception as e:
            logger.error(f"系统检查过程中发生异常: {e}")
            end_time = datetime.now()
            return SystemCheckResult(
                check_id=f"check_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                start_time=start_time,
                end_time=end_time,
                check_duration_seconds=(end_time - start_time).total_seconds(),
                total_checks=0,
                passed_checks=0,
                failed_checks=["system_error"],
                check_details=[{"name": "system_error", "success": False, "error": str(e)}],
                overall_success=False,
                system_ready_for_experiment=False
            )

    async def calibrate_system(self, calibration_config: Dict[str, Any]) -> CalibrationResult:
        """系统校准"""
        logger.info("开始系统校准...")
        start_time = datetime.now()

        calibration_steps = []
        failed_calibrations = []

        try:
            # 1. 检测器校准
            if calibration_config.get("calibrate_detector", True):
                detector_cal = await self._calibrate_detector()
                calibration_steps.append(detector_cal)
                if not detector_cal["success"]:
                    failed_calibrations.append("detector")

            # 2. 泵流量校准
            if calibration_config.get("calibrate_pump", True):
                pump_cal = await self._calibrate_pump_flow()
                calibration_steps.append(pump_cal)
                if not pump_cal["success"]:
                    failed_calibrations.append("pump_flow")

            # 3. 压力传感器校准
            if calibration_config.get("calibrate_pressure", True):
                pressure_cal = await self._calibrate_pressure_sensors()
                calibration_steps.append(pressure_cal)
                if not pressure_cal["success"]:
                    failed_calibrations.append("pressure_sensors")

            # 4. 温度校准
            if calibration_config.get("calibrate_temperature", True):
                temp_cal = await self._calibrate_temperature()
                calibration_steps.append(temp_cal)
                if not temp_cal["success"]:
                    failed_calibrations.append("temperature")

            end_time = datetime.now()
            calibration_duration = (end_time - start_time).total_seconds()

            result = CalibrationResult(
                calibration_id=f"cal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                start_time=start_time,
                end_time=end_time,
                calibration_duration_seconds=calibration_duration,
                calibrated_components=len([s for s in calibration_steps if s["success"]]),
                failed_components=failed_calibrations,
                calibration_details=calibration_steps,
                overall_success=len(failed_calibrations) == 0,
                drift_compensation_applied=True,
                next_calibration_due=datetime.now()
            )

            # 记录校准结果
            await self._log_calibration_event(result)

            logger.info(f"系统校准完成: {result.overall_success}")
            return result

        except Exception as e:
            logger.error(f"系统校准过程中发生异常: {e}")
            end_time = datetime.now()
            return CalibrationResult(
                calibration_id=f"cal_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                start_time=start_time,
                end_time=end_time,
                calibration_duration_seconds=(end_time - start_time).total_seconds(),
                calibrated_components=0,
                failed_components=["system_error"],
                calibration_details=[{"component": "system", "success": False, "error": str(e)}],
                overall_success=False,
                drift_compensation_applied=False,
                next_calibration_due=datetime.now()
            )

    async def execute_preprocessing_sequence(self, sequence: PreprocessingSequence) -> Dict[str, Any]:
        """执行预处理序列"""
        logger.info(f"执行预处理序列: {sequence.sequence_name}")
        self.current_sequence = sequence

        start_time = datetime.now()
        completed_steps = 0
        failed_steps = []

        try:
            for i, step in enumerate(sequence.steps):
                logger.info(f"执行步骤 {i+1}/{len(sequence.steps)}: {step.step_name}")

                step_result = await self._execute_preprocessing_step(step)

                if step_result["success"]:
                    completed_steps += 1
                    logger.info(f"步骤完成: {step.step_name}")
                else:
                    failed_steps.append(step.step_name)
                    logger.error(f"步骤失败: {step.step_name} - {step_result.get('error', '')}")

                    if sequence.stop_on_error:
                        break

                # 发布进度
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_progress",
                    {
                        "sequence_id": sequence.sequence_id,
                        "current_step": i + 1,
                        "total_steps": len(sequence.steps),
                        "step_name": step.step_name,
                        "progress_percent": ((i + 1) / len(sequence.steps)) * 100,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            result = {
                "sequence_id": sequence.sequence_id,
                "success": len(failed_steps) == 0,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "total_duration_seconds": total_duration,
                "start_time": start_time,
                "end_time": end_time
            }

            # 发布完成消息
            await self.mqtt_manager.publish_data(
                "system/preprocessing_completed",
                {
                    **result,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"预处理序列完成: {result['success']}")
            return result

        except Exception as e:
            logger.error(f"预处理序列执行异常: {e}")
            return {
                "sequence_id": sequence.sequence_id,
                "success": False,
                "error": str(e),
                "completed_steps": completed_steps,
                "failed_steps": failed_steps
            }
        finally:
            self.current_sequence = None

    async def get_system_readiness(self) -> SystemReadinessResult:
        """获取系统就绪状态"""
        device_statuses = await self._get_all_device_statuses()

        critical_devices_ready = all(
            status["status"] == DeviceStatus.READY
            for device_id, status in device_statuses.items()
            if status.get("critical", False)
        )

        return SystemReadinessResult(
            system_ready=self.system_ready and critical_devices_ready,
            last_check_time=self.last_check_time,
            critical_devices_ready=critical_devices_ready,
            total_devices=len(device_statuses),
            ready_devices=len([s for s in device_statuses.values() if s["status"] == DeviceStatus.READY]),
            error_devices=len([s for s in device_statuses.values() if s["status"] == DeviceStatus.ERROR]),
            calibration_required=False,  # 简化处理
            maintenance_required=False   # 简化处理
        )

    # 私有方法 - 设备检查
    async def _check_device_connections(self) -> Dict[str, Any]:
        """检查设备连接"""
        try:
            # 模拟设备连接检查
            await asyncio.sleep(1)
            return {
                "name": "device_connections",
                "success": True,
                "details": "所有设备连接正常",
                "checked_devices": 22
            }
        except Exception as e:
            return {
                "name": "device_connections",
                "success": False,
                "error": str(e)
            }

    async def _check_pressure_system(self) -> Dict[str, Any]:
        """检查压力系统"""
        try:
            await asyncio.sleep(0.5)
            return {
                "name": "pressure_system",
                "success": True,
                "details": "压力系统正常",
                "pressure_range": "0-400 bar"
            }
        except Exception as e:
            return {
                "name": "pressure_system",
                "success": False,
                "error": str(e)
            }

    async def _check_detector_system(self) -> Dict[str, Any]:
        """检查检测器系统"""
        try:
            await asyncio.sleep(0.5)
            return {
                "name": "detector_system",
                "success": True,
                "details": "检测器系统正常",
                "wavelength_range": "190-800 nm"
            }
        except Exception as e:
            return {
                "name": "detector_system",
                "success": False,
                "error": str(e)
            }

    async def _check_pump_system(self) -> Dict[str, Any]:
        """检查泵系统"""
        try:
            await asyncio.sleep(0.5)
            return {
                "name": "pump_system",
                "success": True,
                "details": "泵系统正常",
                "flow_range": "0.1-10 mL/min"
            }
        except Exception as e:
            return {
                "name": "pump_system",
                "success": False,
                "error": str(e)
            }

    async def _check_tube_racks(self) -> Dict[str, Any]:
        """检查试管架"""
        try:
            await asyncio.sleep(0.3)
            return {
                "name": "tube_racks",
                "success": True,
                "details": "试管架系统正常",
                "available_positions": 96
            }
        except Exception as e:
            return {
                "name": "tube_racks",
                "success": False,
                "error": str(e)
            }

    async def _check_temperature_system(self) -> Dict[str, Any]:
        """检查温度系统"""
        try:
            await asyncio.sleep(0.3)
            return {
                "name": "temperature_system",
                "success": True,
                "details": "温度控制系统正常",
                "temperature_range": "4-80°C"
            }
        except Exception as e:
            return {
                "name": "temperature_system",
                "success": False,
                "error": str(e)
            }

    # 私有方法 - 校准
    async def _calibrate_detector(self) -> Dict[str, Any]:
        """校准检测器"""
        try:
            await asyncio.sleep(2)
            return {
                "component": "detector",
                "success": True,
                "calibration_factor": 1.002,
                "drift_correction": 0.1
            }
        except Exception as e:
            return {
                "component": "detector",
                "success": False,
                "error": str(e)
            }

    async def _calibrate_pump_flow(self) -> Dict[str, Any]:
        """校准泵流量"""
        try:
            await asyncio.sleep(1.5)
            return {
                "component": "pump_flow",
                "success": True,
                "flow_correction_factor": 0.998,
                "accuracy_percent": 99.8
            }
        except Exception as e:
            return {
                "component": "pump_flow",
                "success": False,
                "error": str(e)
            }

    async def _calibrate_pressure_sensors(self) -> Dict[str, Any]:
        """校准压力传感器"""
        try:
            await asyncio.sleep(1)
            return {
                "component": "pressure_sensors",
                "success": True,
                "pressure_offset": 0.2,
                "linearity_error": 0.05
            }
        except Exception as e:
            return {
                "component": "pressure_sensors",
                "success": False,
                "error": str(e)
            }

    async def _calibrate_temperature(self) -> Dict[str, Any]:
        """校准温度"""
        try:
            await asyncio.sleep(1)
            return {
                "component": "temperature",
                "success": True,
                "temperature_offset": 0.1,
                "stability": 0.05
            }
        except Exception as e:
            return {
                "component": "temperature",
                "success": False,
                "error": str(e)
            }

    async def _execute_preprocessing_step(self, step: PreprocessingStep) -> Dict[str, Any]:
        """执行预处理步骤"""
        try:
            # 根据步骤类型执行不同操作
            if step.step_type == "prime_pumps":
                await self._prime_pumps(step.parameters)
            elif step.step_type == "equilibrate_column":
                await self._equilibrate_column(step.parameters)
            elif step.step_type == "wash_lines":
                await self._wash_lines(step.parameters)
            elif step.step_type == "check_baseline":
                await self._check_baseline(step.parameters)
            else:
                # 通用步骤处理
                await asyncio.sleep(step.duration_seconds or 1)

            return {
                "step_name": step.step_name,
                "success": True,
                "duration": step.duration_seconds or 1
            }
        except Exception as e:
            return {
                "step_name": step.step_name,
                "success": False,
                "error": str(e)
            }

    async def _prime_pumps(self, parameters: Dict[str, Any]):
        """启动泵"""
        await asyncio.sleep(parameters.get("duration", 30))

    async def _equilibrate_column(self, parameters: Dict[str, Any]):
        """平衡色谱柱"""
        await asyncio.sleep(parameters.get("duration", 300))

    async def _wash_lines(self, parameters: Dict[str, Any]):
        """清洗管路"""
        await asyncio.sleep(parameters.get("duration", 60))

    async def _check_baseline(self, parameters: Dict[str, Any]):
        """检查基线"""
        await asyncio.sleep(parameters.get("duration", 120))

    async def _get_all_device_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有设备状态"""
        # 模拟设备状态
        devices = {}
        for i in range(22):
            devices[f"device_{i:02d}"] = {
                "status": DeviceStatus.READY,
                "critical": i < 5  # 前5个设备为关键设备
            }
        return devices

    async def _log_system_check_event(self, result: SystemCheckResult):
        """记录系统检查事件"""
        try:
            await self.db_manager.log_system_event(
                "system_check",
                "info" if result.overall_success else "warning",
                "preprocessing_manager",
                f"系统检查完成: {result.overall_success}",
                result.dict()
            )
        except Exception as e:
            logger.error(f"记录系统检查事件失败: {e}")

    async def _log_calibration_event(self, result: CalibrationResult):
        """记录校准事件"""
        try:
            await self.db_manager.log_system_event(
                "system_calibration",
                "info" if result.overall_success else "warning",
                "preprocessing_manager",
                f"系统校准完成: {result.overall_success}",
                result.dict()
            )
        except Exception as e:
            logger.error(f"记录校准事件失败: {e}")