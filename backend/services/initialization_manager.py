"""
初始化管理器
Initialization Manager
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from models.initialization_models import (
    SystemInitConfig,
    DeviceConfig,
    DeviceInitResult,
    InitializationResult
)
from models.base_models import DeviceType, CommunicationType

logger = logging.getLogger(__name__)


class InitializationManager:
    """系统初始化管理器"""

    def __init__(self):
        self.mqtt_manager: Optional[MQTTManager] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.initialized_devices: Dict[str, Any] = {}
        self.initialization_status = {
            "mqtt": False,
            "database": False,
            "devices": False,
            "system_ready": False
        }

    async def initialize_system(self, config: SystemInitConfig) -> InitializationResult:
        """初始化整个系统"""
        start_time = datetime.now()
        logger.info("开始系统初始化...")

        total_devices = len(config.host_devices) + len(config.collect_devices)
        device_results: List[DeviceInitResult] = []
        failed_devices: List[str] = []

        try:
            # 1. 初始化数据库
            if config.database_path:
                database_success = await self._initialize_database(config.database_path)
                self.initialization_status["database"] = database_success

            # 2. 初始化MQTT
            if config.enable_mqtt:
                mqtt_success = await self._initialize_mqtt(config.mqtt_broker, config.mqtt_port)
                self.initialization_status["mqtt"] = mqtt_success

            # 3. 初始化设备
            if config.enable_hardware:
                device_results = await self._initialize_devices(
                    config.host_devices + config.collect_devices
                )

                # 统计设备初始化结果
                successful_devices = sum(1 for result in device_results if result.success)
                failed_devices = [result.device_id for result in device_results if not result.success]

                self.initialization_status["devices"] = len(failed_devices) == 0
            else:
                successful_devices = 0

            # 4. 系统就绪检查
            system_ready = await self._check_system_readiness()
            self.initialization_status["system_ready"] = system_ready

            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            # 生成初始化结果
            result = InitializationResult(
                total_devices=total_devices,
                initialized_devices=successful_devices,
                failed_devices=failed_devices,
                device_results=device_results,
                initialization_time=total_time,
                success=system_ready,
                mqtt_connected=self.initialization_status["mqtt"],
                database_ready=self.initialization_status["database"]
            )

            if result.success:
                logger.info(f"系统初始化成功! 耗时: {total_time:.2f}秒")
                await self._log_initialization_success(result)
            else:
                logger.error(f"系统初始化失败! 错误设备: {failed_devices}")
                await self._log_initialization_failure(result)

            return result

        except Exception as e:
            logger.error(f"系统初始化过程中发生异常: {e}")
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            return InitializationResult(
                total_devices=total_devices,
                initialized_devices=0,
                failed_devices=["system_error"],
                device_results=[],
                initialization_time=total_time,
                success=False,
                mqtt_connected=False,
                database_ready=False
            )

    async def _initialize_database(self, db_path: str) -> bool:
        """初始化数据库"""
        try:
            logger.info("初始化数据库连接...")
            self.db_manager = DatabaseManager(db_path)
            await self.db_manager.initialize()
            logger.info("数据库初始化成功")
            return True
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False

    async def _initialize_mqtt(self, broker: str, port: int) -> bool:
        """初始化MQTT连接"""
        try:
            logger.info(f"初始化MQTT连接: {broker}:{port}")
            self.mqtt_manager = MQTTManager()
            self.mqtt_manager.broker_host = broker
            self.mqtt_manager.broker_port = port

            success = await self.mqtt_manager.connect()
            if success:
                logger.info("MQTT连接初始化成功")
            else:
                logger.error("MQTT连接初始化失败")
            return success
        except Exception as e:
            logger.error(f"MQTT初始化失败: {e}")
            return False

    async def _initialize_devices(self, device_configs: List[DeviceConfig]) -> List[DeviceInitResult]:
        """初始化设备"""
        logger.info(f"开始初始化 {len(device_configs)} 个设备...")
        device_results = []

        for device_config in device_configs:
            result = await self._initialize_single_device(device_config)
            device_results.append(result)

            # 记录初始化结果
            if result.success:
                self.initialized_devices[device_config.device_id] = {
                    "config": device_config,
                    "initialized_at": datetime.now(),
                    "status": "active"
                }
                logger.info(f"设备 {device_config.device_name} 初始化成功")
            else:
                logger.error(f"设备 {device_config.device_name} 初始化失败: {result.error_message}")

        return device_results

    async def _initialize_single_device(self, device_config: DeviceConfig) -> DeviceInitResult:
        """初始化单个设备"""
        start_time = datetime.now()

        try:
            # 根据设备类型和通信方式进行初始化
            if device_config.communication_type == CommunicationType.SERIAL:
                success = await self._initialize_serial_device(device_config)
            elif device_config.communication_type == CommunicationType.HTTP:
                success = await self._initialize_http_device(device_config)
            else:
                success = False
                error_msg = f"不支持的通信类型: {device_config.communication_type}"

            end_time = datetime.now()
            init_time = (end_time - start_time).total_seconds()

            return DeviceInitResult(
                device_id=device_config.device_id,
                device_name=device_config.device_name,
                success=success,
                error_message=error_msg if not success else None,
                initialization_time=init_time
            )

        except Exception as e:
            end_time = datetime.now()
            init_time = (end_time - start_time).total_seconds()

            return DeviceInitResult(
                device_id=device_config.device_id,
                device_name=device_config.device_name,
                success=False,
                error_message=str(e),
                initialization_time=init_time
            )

    async def _initialize_serial_device(self, device_config: DeviceConfig) -> bool:
        """初始化串口设备"""
        try:
            # 这里将来集成硬件抽象层
            # 目前先模拟初始化
            await asyncio.sleep(0.1)  # 模拟初始化时间
            return True
        except Exception as e:
            logger.error(f"串口设备初始化失败: {e}")
            return False

    async def _initialize_http_device(self, device_config: DeviceConfig) -> bool:
        """初始化HTTP设备"""
        try:
            # 这里将来集成硬件抽象层
            # 目前先模拟初始化
            await asyncio.sleep(0.1)  # 模拟初始化时间
            return True
        except Exception as e:
            logger.error(f"HTTP设备初始化失败: {e}")
            return False

    async def _check_system_readiness(self) -> bool:
        """检查系统就绪状态"""
        try:
            # 检查核心组件状态
            mqtt_ready = self.initialization_status.get("mqtt", False)
            database_ready = self.initialization_status.get("database", False)
            devices_ready = self.initialization_status.get("devices", False)

            # 系统就绪需要满足最基本的要求
            basic_ready = database_ready  # 至少需要数据库

            logger.info(f"系统就绪检查 - MQTT: {mqtt_ready}, 数据库: {database_ready}, 设备: {devices_ready}")

            return basic_ready

        except Exception as e:
            logger.error(f"系统就绪检查失败: {e}")
            return False

    async def _log_initialization_success(self, result: InitializationResult):
        """记录初始化成功日志"""
        if self.db_manager:
            try:
                await self.db_manager.log_system_event(
                    "initialization",
                    "info",
                    "system",
                    "系统初始化成功",
                    {
                        "total_devices": result.total_devices,
                        "initialized_devices": result.initialized_devices,
                        "initialization_time": result.initialization_time
                    }
                )
            except Exception as e:
                logger.error(f"记录初始化成功日志失败: {e}")

    async def _log_initialization_failure(self, result: InitializationResult):
        """记录初始化失败日志"""
        if self.db_manager:
            try:
                await self.db_manager.log_system_event(
                    "initialization",
                    "error",
                    "system",
                    "系统初始化失败",
                    {
                        "failed_devices": result.failed_devices,
                        "initialization_time": result.initialization_time
                    }
                )
            except Exception as e:
                logger.error(f"记录初始化失败日志失败: {e}")

    async def get_initialization_status(self) -> Dict[str, Any]:
        """获取初始化状态"""
        return {
            "status": self.initialization_status,
            "initialized_devices": list(self.initialized_devices.keys()),
            "device_count": len(self.initialized_devices),
            "system_ready": self.initialization_status.get("system_ready", False)
        }

    async def reinitialize_device(self, device_id: str) -> DeviceInitResult:
        """重新初始化指定设备"""
        if device_id not in self.initialized_devices:
            return DeviceInitResult(
                device_id=device_id,
                device_name="unknown",
                success=False,
                error_message="设备未找到",
                initialization_time=0.0
            )

        device_info = self.initialized_devices[device_id]
        device_config = device_info["config"]

        logger.info(f"重新初始化设备: {device_config.device_name}")
        result = await self._initialize_single_device(device_config)

        if result.success:
            self.initialized_devices[device_id]["status"] = "active"
            self.initialized_devices[device_id]["reinitialized_at"] = datetime.now()

        return result

    async def shutdown_system(self):
        """关闭系统"""
        logger.info("开始关闭系统...")

        # 关闭MQTT连接
        if self.mqtt_manager:
            await self.mqtt_manager.disconnect()
            logger.info("MQTT连接已关闭")

        # 关闭设备
        for device_id in self.initialized_devices:
            self.initialized_devices[device_id]["status"] = "shutdown"

        # 重置状态
        self.initialization_status = {
            "mqtt": False,
            "database": False,
            "devices": False,
            "system_ready": False
        }

        logger.info("系统关闭完成")