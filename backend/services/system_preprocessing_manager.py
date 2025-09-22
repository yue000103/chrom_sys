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
# from models.system_preprocessing_models import (
#     SystemCheckConfig,
#     SystemCheckResult,
#     PreprocessingSequence,
#     PreprocessingStep,
#     CalibrationResult,
#     SystemReadinessResult
# )
from models.base_models import DeviceStatus
from hardware.host_devices.detector import DetectorController
from hardware.host_devices.pump_controller import PumpController
from hardware.host_devices.bubble_sensor import BubbleSensorHost
from hardware.host_devices.relay_controller import RelayController
from hardware.collect_devices.multi_valve import MultiValveController

logger = logging.getLogger(__name__)


class SystemPreprocessingManager:
    """系统预处理管理器"""

    def __init__(self, mqtt_manager: MQTTManager, db_manager: DatabaseManager):
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        self.system_ready = False
        self.last_check_time: Optional[datetime] = None

        # 初始化硬件设备控制器
        self.detector = DetectorController(mock=True)
        self.pump_controller = PumpController(mock=True)
        self.bubble_sensor = BubbleSensorHost(mock=True)
        self.relay_controller = RelayController(mock=True)
        self.multi_valve = MultiValveController(mock=True)
        self.current_experiment_id: Optional[int] = None



    async def initialize_devices(self, wavelength: float = None, flow_rates: Dict[str, float] = None, gradient_profile: Dict[str, Any] = None) -> bool:
        """
        初始化设备
        如果提供了参数，使用提供的参数；否则根据current_experiment_id从数据库获取方法参数
        :param wavelength: 检测器波长（可选，如果不提供则从method获取）
        :param flow_rates: 四元泵流速设置 {'A': 1.0, 'B': 0.5, 'C': 0.0, 'D': 0.0}（可选）
        :param gradient_profile: 梯度洗脱参数（可选）
        :return: 初始化结果，任何一个步骤失败都返回False
        """
        logger.info("开始设备初始化...")

        try:
            # 如果没有提供参数且有current_experiment_id，则从数据库获取方法参数
            if (wavelength is None or flow_rates is None or gradient_profile is None) and self.current_experiment_id:
                method_params = await self._get_method_parameters_from_experiment(self.current_experiment_id)
                if method_params:
                    if wavelength is None:
                        wavelength = method_params.get('wavelength', 254.0)
                    if flow_rates is None:
                        flow_rates = method_params.get('flow_rates')

                    logger.info(f"从实验ID {self.current_experiment_id} 获取方法参数")
                else:
                    logger.warning(f"无法获取实验ID {self.current_experiment_id} 的方法参数，使用默认值")

            # 设置默认值
            if wavelength is None:
                wavelength = 254.0
            if flow_rates is None:
                flow_rates = {'A': 1.0, 'B': 0.0, 'C': 0.0, 'D': 0.0}

            # 1. 连接所有设备
            devices_connected = await self._connect_all_devices()
            if not devices_connected:
                return False

            # 2. 设置检测器波长
            wavelength_set = await self.detector.set_wavelength(wavelength)
            if not wavelength_set:
                logger.error(f"设置检测器波长失败: {wavelength}nm")
                return False
            logger.info(f"检测器波长设置成功: {wavelength}nm")

            # 3. 设置四元泵流速
            for pump_id, flow_rate in flow_rates.items():
                flow_rate_set = await self.pump_controller.set_flow_rate(pump_id, flow_rate)
                if not flow_rate_set:
                    logger.error(f"设置泵{pump_id}流速失败: {flow_rate} mL/min")
                    return False
                logger.info(f"泵{pump_id}流速设置成功: {flow_rate} mL/min")


            # 5. 检测气泡传感器状态
            # 读取所有气泡传感器，如果气1-气4均为True（检测到气泡），则返回False
            all_sensors = await self.bubble_sensor.read_all_sensors()
            bubble_detected_sensors = []

            for sensor_id in ['气1', '气2', '气3', '气4']:
                if sensor_id in all_sensors:
                    sensor_data = all_sensors[sensor_id]
                    if sensor_data.get('bubble_detected', False):
                        bubble_detected_sensors.append(sensor_id)

            # 如果所有传感器都检测到气泡，返回False
            if len(bubble_detected_sensors) == 4:
                logger.error("所有气泡传感器都检测到气泡，初始化失败")
                return False

            if bubble_detected_sensors:
                logger.warning(f"以下传感器检测到气泡: {', '.join(bubble_detected_sensors)}")
            else:
                logger.info("气泡传感器检查通过")

            logger.info("设备初始化完成")
            return True

        except Exception as e:
            logger.error(f"设备初始化过程中发生异常: {e}")
            return False

    async def _connect_all_devices(self) -> bool:
        """
        连接所有设备
        :return: 连接结果，任何一个设备连接失败都返回False
        """
        try:
            # 连接检测器
            detector_connected = await self.detector.connect()
            if not detector_connected:
                logger.error("检测器连接失败")
                return False
            logger.info("检测器连接成功")

            # 连接泵控制器
            pump_connected = await self.pump_controller.connect()
            if not pump_connected:
                logger.error("泵控制器连接失败")
                return False
            logger.info("泵控制器连接成功")

            # 初始化气泡传感器
            bubble_initialized = await self.bubble_sensor.initialize()
            if not bubble_initialized:
                logger.error("气泡传感器初始化失败")
                return False
            logger.info("气泡传感器初始化成功")

            logger.info("所有设备连接完成")
            return True

        except Exception as e:
            logger.error(f"设备连接过程中发生异常: {e}")
            return False

    async def _get_method_parameters_from_experiment(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        根据实验ID获取方法参数
        :param experiment_id: 实验ID
        :return: 方法参数字典
        """
        try:
            # 查询实验获取method_id
            experiment_query = """
                SELECT method_id FROM experiments WHERE id = ?
            """
            experiment_result = await self.db_manager.fetch_one(experiment_query, (experiment_id,))

            if not experiment_result:
                logger.error(f"未找到实验ID: {experiment_id}")
                return None

            method_id = experiment_result['method_id']
            logger.info(f"实验ID {experiment_id} 对应方法ID: {method_id}")

            # 查询方法获取参数
            method_query = """
                SELECT detection_parameters, gradient_program, initial_flow_rates
                FROM methods WHERE method_id = ?
            """
            method_result = await self.db_manager.fetch_one(method_query, (method_id,))

            if not method_result:
                logger.error(f"未找到方法ID: {method_id}")
                return None

            # 解析检测参数获取波长
            detection_params = method_result.get('detection_parameters', {})
            if isinstance(detection_params, str):
                import json
                detection_params = json.loads(detection_params)

            wavelength = detection_params.get('wavelength_nm', 254.0)

            # 解析梯度程序
            gradient_program = method_result.get('gradient_program', {})
            if isinstance(gradient_program, str):
                import json
                gradient_program = json.loads(gradient_program)

            # 解析初始流速
            flow_rates = method_result.get('initial_flow_rates', {})
            if isinstance(flow_rates, str):
                import json
                flow_rates = json.loads(flow_rates)

            # 如果没有初始流速，从梯度程序的第一步获取
            if not flow_rates and gradient_program:
                steps = gradient_program.get('steps', [])
                if steps and len(steps) > 0:
                    first_step = steps[0]
                    flow_rates = {
                        'A': first_step.get('flow_a_ml_min', 1.0),
                        'B': first_step.get('flow_b_ml_min', 0.0),
                        'C': first_step.get('flow_c_ml_min', 0.0),
                        'D': first_step.get('flow_d_ml_min', 0.0)
                    }

            return {
                'wavelength': wavelength,
                'flow_rates': flow_rates,
                'gradient_profile': gradient_program
            }

        except Exception as e:
            logger.error(f"获取方法参数失败: {e}")
            return None

    async def _get_experiment_column_balance_params(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取实验的柱平衡参数
        :param experiment_id: 实验ID
        :return: 柱平衡参数字典
        """
        try:
            experiment_query = """
                SELECT column_balance, column_balance_time_min, column_conditioning_solution
                FROM experiments WHERE id = ?
            """
            result = await self.db_manager.fetch_one(experiment_query, (experiment_id,))

            if not result:
                logger.error(f"未找到实验ID: {experiment_id}")
                return None

            return {
                'column_balance': result.get('column_balance', False),
                'column_balance_time_min': result.get('column_balance_time_min', 0),
                'column_conditioning_solution': result.get('column_conditioning_solution')
            }

        except Exception as e:
            logger.error(f"获取实验柱平衡参数失败: {e}")
            return None

    async def _get_experiment_purge_params(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取实验的吹扫系统参数
        :param experiment_id: 实验ID
        :return: 吹扫参数字典
        """
        try:
            experiment_query = """
                SELECT purge_system
                FROM experiments WHERE id = ?
            """
            result = await self.db_manager.fetch_one(experiment_query, (experiment_id,))

            if not result:
                logger.error(f"未找到实验ID: {experiment_id}")
                return None

            return {
                'purge_system': result.get('purge_system', False)
            }

        except Exception as e:
            logger.error(f"获取实验吹扫参数失败: {e}")
            return None

    async def _get_experiment_purge_column_params(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取实验的吹扫柱子参数
        :param experiment_id: 实验ID
        :return: 吹扫柱子参数字典
        """
        try:
            experiment_query = """
                SELECT purge_column, purge_column_time_min
                FROM experiments WHERE id = ?
            """
            result = await self.db_manager.fetch_one(experiment_query, (experiment_id,))

            if not result:
                logger.error(f"未找到实验ID: {experiment_id}")
                return None

            return {
                'purge_column': result.get('purge_column', False),
                'purge_column_time_min': result.get('purge_column_time_min', 0)
            }

        except Exception as e:
            logger.error(f"获取实验吹扫柱子参数失败: {e}")
            return None

    async def _equilibrate_column(self, parameters: Dict[str, Any]):
        """
        平衡色谱柱
        根据experiment中的column_balance参数执行柱平衡操作
        :param parameters: 可能包含实验ID或直接的平衡参数
        """
        logger.info("开始柱平衡操作...")

        try:
            # 获取柱平衡参数
            balance_params = None

            # 如果有current_experiment_id，从数据库获取参数
            if self.current_experiment_id:
                balance_params = await self._get_experiment_column_balance_params(self.current_experiment_id)

            # 如果parameters中直接提供了参数，优先使用
            if parameters:
                balance_params = {
                    'column_balance': parameters.get('column_balance', balance_params.get('column_balance', False) if balance_params else False),
                    'column_balance_time_min': parameters.get('column_balance_time_min', balance_params.get('column_balance_time_min', 0) if balance_params else 0),
                    'column_conditioning_solution': parameters.get('column_conditioning_solution', balance_params.get('column_conditioning_solution') if balance_params else None)
                }

            if not balance_params:
                logger.warning("未获取到柱平衡参数，跳过柱平衡")
                return

            # 检查是否需要执行柱平衡
            if not balance_params.get('column_balance', False):
                logger.info("实验设置不需要柱平衡，跳过")
                return

            balance_time_min = balance_params.get('column_balance_time_min', 0)
            conditioning_solution = balance_params.get('column_conditioning_solution')

            if balance_time_min <= 0:
                logger.warning("柱平衡时间为0或未设置，跳过柱平衡")
                return

            logger.info(f"开始柱平衡: 时间={balance_time_min}分钟, 润柱溶液={conditioning_solution}")

            # 发布开始消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "column_equilibration",
                        "experiment_id": self.current_experiment_id,
                        "time": balance_time_min,
                        "status": "started",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 1. 设置柱平衡的梯度洗脱程序
            # 通常柱平衡使用单一溶剂系统
            equilibration_gradient = {
                "steps": [
                    {
                        "time_min": balance_time_min,
                        "flow_a_ml_min": 1.0,  # 主要溶剂
                        "flow_b_ml_min": 0.0,
                        "flow_c_ml_min": 0.0,
                        "flow_d_ml_min": 0.0
                    }
                ],
                "total_duration": balance_time_min
            }

            # 如果指定了润柱溶液，调整流速配置
            if conditioning_solution:
                if conditioning_solution == 1:  # 假设1代表溶剂A
                    equilibration_gradient["steps"][0]["flow_a_ml_min"] = 1.0
                elif conditioning_solution == 2:  # 假设2代表溶剂B
                    equilibration_gradient["steps"][0]["flow_a_ml_min"] = 0.0
                    equilibration_gradient["steps"][0]["flow_b_ml_min"] = 1.0
                # 可以根据需要添加更多溶剂选项

            # 2. 设置梯度洗脱
            gradient_set = await self.pump_controller.set_gradient(equilibration_gradient)
            if not gradient_set:
                logger.error("设置柱平衡梯度失败")
                return

            # 3. 启动泵系统
            pumps_to_start = ['A']  # 默认启动A泵
            if conditioning_solution == 2:
                pumps_to_start = ['B']
            elif conditioning_solution == 3:
                pumps_to_start = ['C']
            elif conditioning_solution == 4:
                pumps_to_start = ['D']

            for pump_id in pumps_to_start:
                pump_started = await self.pump_controller.start_pump(pump_id)
                if not pump_started:
                    logger.error(f"启动泵{pump_id}失败")
                    return
                logger.info(f"泵{pump_id}启动成功")

            # 4. 开始计时等待
            logger.info(f"柱平衡进行中，等待 {balance_time_min} 分钟...")

            # 等待指定的平衡时间
            await asyncio.sleep(balance_time_min * 60)  # 转换为秒

            # 5. 停止泵
            for pump_id in pumps_to_start:
                pump_stopped = await self.pump_controller.stop_pump(pump_id)
                if not pump_stopped:
                    logger.warning(f"停止泵{pump_id}失败")
                else:
                    logger.info(f"泵{pump_id}停止成功")

            logger.info("柱平衡完成")

            # 发布完成消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "column_equilibration",
                        "experiment_id": self.current_experiment_id,
                        "time": balance_time_min,
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except Exception as e:
            logger.error(f"柱平衡过程中发生异常: {e}")
            # 确保在异常情况下也停止泵
            try:
                for pump_id in ['A', 'B', 'C', 'D']:
                    await self.pump_controller.stop_pump(pump_id)
            except:
                pass

    async def _purge_system(self, parameters: Dict[str, Any]):
        """
        吹扫系统
        根据experiment中的purge_system参数执行系统吹扫操作
        :param parameters: 可能包含实验ID或直接的吹扫参数
        """
        logger.info("开始吹扫系统操作...")

        try:
            # 获取吹扫参数
            purge_params = None

            # 如果有current_experiment_id，从数据库获取参数
            if self.current_experiment_id:
                purge_params = await self._get_experiment_purge_params(self.current_experiment_id)

            # 如果parameters中直接提供了参数，优先使用
            if parameters:
                purge_params = {
                    'purge_system': parameters.get('purge_system', purge_params.get('purge_system', False) if purge_params else False)
                }

            if not purge_params:
                logger.warning("未获取到吹扫参数，跳过吹扫系统")
                return

            # 检查是否需要执行吹扫
            if not purge_params.get('purge_system', False):
                logger.info("实验设置不需要吹扫系统，跳过")
                return

            logger.info("开始执行系统吹扫，等待50秒...")

            # 发布开始消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "purge_system",
                        "experiment_id": self.current_experiment_id,
                        "status": "started",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 等待50秒进行吹扫
            await asyncio.sleep(50)

            logger.info("吹扫系统完成")

            # 发布完成消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "purge_system",
                        "experiment_id": self.current_experiment_id,
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except Exception as e:
            logger.error(f"吹扫系统过程中发生异常: {e}")

    async def _purge_column(self, parameters: Dict[str, Any]):
        """
        吹扫柱子
        根据experiment中的purge_column参数执行柱子吹扫操作
        :param parameters: 可能包含实验ID或直接的吹扫参数
        """
        logger.info("开始吹扫柱子操作...")

        try:
            # 获取吹扫柱子参数
            purge_params = None

            # 如果有current_experiment_id，从数据库获取参数
            if self.current_experiment_id:
                purge_params = await self._get_experiment_purge_column_params(self.current_experiment_id)

            # 如果parameters中直接提供了参数，优先使用
            if parameters:
                purge_params = {
                    'purge_column': parameters.get('purge_column', purge_params.get('purge_column', False) if purge_params else False),
                    'purge_column_time_min': parameters.get('purge_column_time_min', purge_params.get('purge_column_time_min', 0) if purge_params else 0)
                }

            if not purge_params:
                logger.warning("未获取到吹扫柱子参数，跳过吹扫柱子")
                return

            # 检查是否需要执行吹扫柱子
            if not purge_params.get('purge_column', False):
                logger.info("实验设置不需要吹扫柱子，跳过")
                return

            purge_time_min = purge_params.get('purge_column_time_min', 0)
            if purge_time_min <= 0:
                logger.warning("吹扫柱子时间为0或未设置，跳过吹扫柱子")
                return

            logger.info(f"开始吹扫柱子: 时间={purge_time_min}分钟")

            # 发布开始消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "purge_column",
                        "experiment_id": self.current_experiment_id,
                        "time": purge_time_min,
                        "status": "started",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 1. 双1（高压电磁阀）开启
            dual1_on = await self.relay_controller.control_relay('双1', 'on')
            if not dual1_on:
                logger.error("开启双1（高压电磁阀）失败")
                return
            logger.info("双1（高压电磁阀）开启成功")

            # 2. 双2（低压电磁阀）关闭
            dual2_off = await self.relay_controller.control_relay('双2', 'off')
            if not dual2_off:
                logger.error("关闭双2（低压电磁阀）失败")
                return
            logger.info("双2（低压电磁阀）关闭成功")

            # 3. 多9开到通道5
            valve9_set = await self.multi_valve.set_position('多9', 5)
            if not valve9_set:
                logger.error("设置多9到通道5失败")
                return
            logger.info("多9设置到通道5成功")

            # 4. 开启泵2（气泵）
            pump2_on = await self.relay_controller.control_relay('泵2', 'on')
            if not pump2_on:
                logger.error("开启泵2（气泵）失败")
                return
            logger.info("泵2（气泵）开启成功")

            # 5. 开始计时等待
            logger.info(f"吹扫柱子进行中，等待 {purge_time_min} 分钟...")

            # 等待指定的吹扫时间
            await asyncio.sleep(purge_time_min * 60)  # 转换为秒

            # 6. 停止所有操作
            # 关闭泵2（气泵）
            pump2_off = await self.relay_controller.control_relay('泵2', 'off')
            if not pump2_off:
                logger.warning("关闭泵2（气泵）失败")
            else:
                logger.info("泵2（气泵）关闭成功")

            # 关闭双1（高压电磁阀）
            dual1_off = await self.relay_controller.control_relay('双1', 'off')
            if not dual1_off:
                logger.warning("关闭双1（高压电磁阀）失败")
            else:
                logger.info("双1（高压电磁阀）关闭成功")

            logger.info("吹扫柱子完成")

            # 发布完成消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "purge_column",
                        "experiment_id": self.current_experiment_id,
                        "time": purge_time_min,
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except Exception as e:
            logger.error(f"吹扫柱子过程中发生异常: {e}")
            # 确保在异常情况下也停止所有设备
            try:
                await self.relay_controller.control_relay('泵2', 'off')
                await self.relay_controller.control_relay('双1', 'off')
                await self.relay_controller.control_relay('双2', 'off')
            except:
                pass

    async def execute_preprocessing(self, experiment_id: int) -> bool:
        """
        执行预处理流程
        按顺序执行：吹扫柱子 -> 吹扫系统 -> 柱平衡
        :param experiment_id: 实验ID
        :return: 执行结果，全部成功返回True，任何一步失败返回False
        """
        logger.info(f"开始执行预处理流程，实验ID: {experiment_id}")

        # 设置当前实验ID
        self.current_experiment_id = experiment_id

        try:
            # 发布预处理开始消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "preprocessing_sequence",
                        "experiment_id": self.current_experiment_id,
                        "status": "started",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 1. 执行吹扫柱子
            logger.info("步骤1: 执行吹扫柱子")
            try:
                await self._purge_column({})
                logger.info("吹扫柱子执行完成")
            except Exception as e:
                logger.error(f"吹扫柱子执行失败: {e}")
                return False

            # 2. 执行吹扫系统
            logger.info("步骤2: 执行吹扫系统")
            try:
                await self._purge_system({})
                logger.info("吹扫系统执行完成")
            except Exception as e:
                logger.error(f"吹扫系统执行失败: {e}")
                return False

            # 3. 执行柱平衡
            logger.info("步骤3: 执行柱平衡")
            try:
                await self._equilibrate_column({})
                logger.info("柱平衡执行完成")
            except Exception as e:
                logger.error(f"柱平衡执行失败: {e}")
                return False

            logger.info("预处理流程全部完成")

            # 发布预处理完成消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "preprocessing_sequence",
                        "experiment_id": self.current_experiment_id,
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            return True

        except Exception as e:
            logger.error(f"预处理流程执行过程中发生异常: {e}")

            # 发布预处理失败消息
            if self.mqtt_manager:
                await self.mqtt_manager.publish_data(
                    "system/preprocessing_status",
                    {
                        "action": "preprocessing_sequence",
                        "experiment_id": self.current_experiment_id,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )

            return False


