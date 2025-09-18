"""
基础数据处理器
提供所有数据处理器的基础功能和接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """数据处理器基类"""

    def __init__(self, name: str):
        self.name = name
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.processed_count = 0
        self.error_count = 0
        self.last_process_time: Optional[datetime] = None

    @abstractmethod
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据的抽象方法
        :param data: 原始数据
        :return: 处理后的数据
        """
        pass

    async def start(self):
        """启动处理器"""
        if self.is_running:
            logger.warning(f"{self.name} 已在运行")
            return

        self.is_running = True
        logger.info(f"{self.name} 已启动")

    async def stop(self):
        """停止处理器"""
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"{self.name} 已停止")

    def format_data(self, device_id: str, device_type: str, data: Any,
                   status: str = "normal", mode: str = "online") -> Dict[str, Any]:
        """
        格式化设备数据为标准格式
        :param device_id: 设备ID
        :param device_type: 设备类型
        :param data: 设备数据
        :param status: 设备状态
        :param mode: 设备模式 (mock/online)
        :return: 格式化后的数据
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "device_type": device_type,
            "data": data,
            "status": status,
            "mode": mode
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证数据有效性
        :param data: 待验证的数据
        :return: 是否有效
        """
        required_fields = ["device_id", "device_type", "data"]

        for field in required_fields:
            if field not in data:
                logger.warning(f"数据缺少必需字段: {field}")
                return False

        return True

    async def handle_error(self, error: Exception, data: Optional[Dict[str, Any]] = None):
        """
        统一错误处理
        :param error: 异常对象
        :param data: 相关数据
        """
        self.error_count += 1
        error_info = {
            "processor": self.name,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        logger.error(f"{self.name} 处理错误: {error_info}")
        return error_info

    def get_statistics(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "last_process_time": self.last_process_time.isoformat() if self.last_process_time else None,
            "error_rate": self.error_count / max(self.processed_count, 1)
        }

    async def batch_process(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量处理数据
        :param data_list: 数据列表
        :return: 处理结果列表
        """
        results = []

        for data in data_list:
            try:
                result = await self.process_data(data)
                results.append(result)
                self.processed_count += 1
                self.last_process_time = datetime.now()
            except Exception as e:
                error_info = await self.handle_error(e, data)
                results.append(error_info)

        return results


class DataFilter:
    """数据过滤器"""

    @staticmethod
    def filter_by_device_type(data_list: List[Dict[str, Any]], device_type: str) -> List[Dict[str, Any]]:
        """按设备类型过滤"""
        return [data for data in data_list if data.get("device_type") == device_type]

    @staticmethod
    def filter_by_status(data_list: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        """按状态过滤"""
        return [data for data in data_list if data.get("status") == status]

    @staticmethod
    def filter_by_mode(data_list: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
        """按模式过滤 (mock/online)"""
        return [data for data in data_list if data.get("mode") == mode]

    @staticmethod
    def filter_by_time_range(data_list: List[Dict[str, Any]],
                            start_time: datetime,
                            end_time: datetime) -> List[Dict[str, Any]]:
        """按时间范围过滤"""
        filtered = []
        for data in data_list:
            timestamp_str = data.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if start_time <= timestamp <= end_time:
                        filtered.append(data)
                except (ValueError, TypeError):
                    continue
        return filtered


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_pressure(value: float, min_val: float = 0, max_val: float = 100) -> bool:
        """验证压力值"""
        return min_val <= value <= max_val

    @staticmethod
    def validate_flow_rate(value: float, min_val: float = 0, max_val: float = 10) -> bool:
        """验证流速"""
        return min_val <= value <= max_val

    @staticmethod
    def validate_temperature(value: float, min_val: float = -50, max_val: float = 200) -> bool:
        """验证温度"""
        return min_val <= value <= max_val

    @staticmethod
    def validate_signal(value: float, min_val: float = 0, max_val: float = 10000) -> bool:
        """验证检测信号"""
        return min_val <= value <= max_val

    @staticmethod
    def validate_valve_position(position: int, max_positions: int = 6) -> bool:
        """验证阀门位置"""
        return 1 <= position <= max_positions