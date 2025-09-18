"""
数据聚合器
聚合所有设备数据，生成系统总体状态和统计信息
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import asyncio

logger = logging.getLogger(__name__)


class DataAggregator:
    """数据聚合器"""

    def __init__(self):
        self.device_data_cache = {}  # 设备最新数据缓存
        self.historical_data = defaultdict(list)  # 历史数据
        self.statistics = defaultdict(lambda: defaultdict(float))  # 统计信息
        self.aggregation_interval = 5.0  # 聚合间隔（秒）
        self.max_history_size = 1000  # 每个设备最大历史记录数
        self.is_running = False
        self._aggregator_task = None

    async def start(self):
        """启动聚合器"""
        if self.is_running:
            logger.warning("数据聚合器已在运行")
            return

        self.is_running = True
        self._aggregator_task = asyncio.create_task(self._aggregation_loop())
        logger.info("数据聚合器已启动")

    async def stop(self):
        """停止聚合器"""
        self.is_running = False

        if self._aggregator_task:
            self._aggregator_task.cancel()
            try:
                await self._aggregator_task
            except asyncio.CancelledError:
                pass

        logger.info("数据聚合器已停止")

    def update_device_data(self, device_id: str, data: Dict[str, Any]):
        """
        更新设备数据
        :param device_id: 设备ID
        :param data: 设备数据
        """
        # 更新缓存
        self.device_data_cache[device_id] = {
            **data,
            "last_update": datetime.now().isoformat()
        }

        # 添加到历史记录
        self.historical_data[device_id].append({
            "timestamp": datetime.now().isoformat(),
            "data": data
        })

        # 限制历史记录大小
        if len(self.historical_data[device_id]) > self.max_history_size:
            self.historical_data[device_id].pop(0)

        # 更新统计信息
        self._update_statistics(device_id, data)

    def _update_statistics(self, device_id: str, data: Dict[str, Any]):
        """更新统计信息"""
        device_type = data.get("device_type", "unknown")

        # 更新设备计数
        self.statistics[device_type]["count"] += 1

        # 根据设备类型更新特定统计
        if device_type == "pressure_sensor":
            pressure = data.get("data", {}).get("pressure", 0)
            self._update_value_statistics(device_type, "pressure", pressure)

        elif device_type == "detector":
            signal = data.get("data", {}).get("signal", 0)
            self._update_value_statistics(device_type, "signal", signal)

        elif device_type == "pump_controller":
            pumps = data.get("data", {}).get("pumps", {})
            for pump_id, pump_data in pumps.items():
                flow_rate = pump_data.get("flow_rate", 0)
                self._update_value_statistics(f"{device_type}_{pump_id}", "flow_rate", flow_rate)

    def _update_value_statistics(self, category: str, metric: str, value: float):
        """更新数值统计"""
        stats = self.statistics[category][metric]
        if not isinstance(stats, dict):
            self.statistics[category][metric] = {
                "min": value,
                "max": value,
                "sum": value,
                "count": 1,
                "avg": value
            }
        else:
            stats["min"] = min(stats["min"], value)
            stats["max"] = max(stats["max"], value)
            stats["sum"] += value
            stats["count"] += 1
            stats["avg"] = stats["sum"] / stats["count"]

    async def _aggregation_loop(self):
        """聚合循环"""
        try:
            while self.is_running:
                await self._perform_aggregation()
                await asyncio.sleep(self.aggregation_interval)

        except asyncio.CancelledError:
            logger.info("聚合循环被取消")
        except Exception as e:
            logger.error(f"聚合循环错误: {e}")

    async def _perform_aggregation(self):
        """执行数据聚合"""
        try:
            aggregated_data = await self.get_aggregated_data()
            logger.debug(f"聚合完成: {len(aggregated_data.get('devices', {}))} 个设备")

        except Exception as e:
            logger.error(f"数据聚合错误: {e}")

    async def get_aggregated_data(self) -> Dict[str, Any]:
        """获取聚合数据"""
        current_time = datetime.now()

        # 系统总体状态
        system_status = await self._calculate_system_status()

        # 设备摘要
        devices_summary = self._get_devices_summary()

        # 告警统计
        alerts = self._get_alerts()

        # 性能指标
        performance_metrics = self._calculate_performance_metrics()

        return {
            "timestamp": current_time.isoformat(),
            "system_status": system_status,
            "devices": devices_summary,
            "alerts": alerts,
            "performance": performance_metrics,
            "statistics": dict(self.statistics)
        }

    async def _calculate_system_status(self) -> Dict[str, Any]:
        """计算系统总体状态"""
        total_devices = len(self.device_data_cache)
        online_devices = sum(
            1 for d in self.device_data_cache.values()
            if d.get("mode") == "online"
        )
        mock_devices = sum(
            1 for d in self.device_data_cache.values()
            if d.get("mode") == "mock"
        )

        # 检查设备状态
        normal_count = sum(
            1 for d in self.device_data_cache.values()
            if d.get("status") in ["normal", "idle", "stopped"]
        )
        warning_count = sum(
            1 for d in self.device_data_cache.values()
            if "warning" in str(d.get("status", "")).lower()
        )
        error_count = sum(
            1 for d in self.device_data_cache.values()
            if "error" in str(d.get("status", "")).lower()
        )

        # 确定系统总体状态
        if error_count > 0:
            overall_status = "error"
        elif warning_count > 0:
            overall_status = "warning"
        elif total_devices == 0:
            overall_status = "no_devices"
        else:
            overall_status = "normal"

        return {
            "overall_status": overall_status,
            "total_devices": total_devices,
            "online_devices": online_devices,
            "mock_devices": mock_devices,
            "normal_count": normal_count,
            "warning_count": warning_count,
            "error_count": error_count
        }

    def _get_devices_summary(self) -> Dict[str, Any]:
        """获取设备摘要"""
        summary = {}

        for device_id, data in self.device_data_cache.items():
            device_type = data.get("device_type", "unknown")
            status = data.get("status", "unknown")
            mode = data.get("mode", "unknown")

            summary[device_id] = {
                "type": device_type,
                "status": status,
                "mode": mode,
                "last_update": data.get("last_update")
            }

            # 添加关键数据
            device_data = data.get("data", {})
            if device_type == "pressure_sensor":
                summary[device_id]["pressure"] = device_data.get("pressure")
            elif device_type == "detector":
                summary[device_id]["signal"] = device_data.get("signal")
            elif device_type == "pump_controller":
                pumps = device_data.get("pumps", {})
                summary[device_id]["pumps_status"] = {
                    pid: p.get("status") for pid, p in pumps.items()
                }

        return summary

    def _get_alerts(self) -> List[Dict[str, Any]]:
        """获取告警信息"""
        alerts = []

        for device_id, data in self.device_data_cache.items():
            device_type = data.get("device_type", "unknown")
            status = data.get("status", "normal")
            device_data = data.get("data", {})

            # 检查压力告警
            if device_type == "pressure_sensor":
                pressure = device_data.get("pressure", 0)
                if pressure > 10.0:
                    alerts.append({
                        "device_id": device_id,
                        "type": "high_pressure",
                        "severity": "warning",
                        "message": f"高压告警: {pressure} MPa",
                        "timestamp": datetime.now().isoformat()
                    })

            # 检查气泡告警
            elif "bubble" in device_type:
                bubble_count = device_data.get("bubble_count", 0)
                if bubble_count > 0:
                    alerts.append({
                        "device_id": device_id,
                        "type": "bubble_detected",
                        "severity": "warning",
                        "message": f"检测到{bubble_count}个气泡",
                        "timestamp": datetime.now().isoformat()
                    })

            # 检查设备错误状态
            if "error" in str(status).lower():
                alerts.append({
                    "device_id": device_id,
                    "type": "device_error",
                    "severity": "error",
                    "message": f"设备错误: {status}",
                    "timestamp": datetime.now().isoformat()
                })

        return alerts

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        metrics = {}

        # 数据更新率
        recent_updates = sum(
            1 for d in self.device_data_cache.values()
            if d.get("last_update") and
            datetime.fromisoformat(d["last_update"]) > datetime.now() - timedelta(seconds=10)
        )
        metrics["update_rate"] = recent_updates / max(len(self.device_data_cache), 1)

        # 平均响应时间（模拟）
        metrics["avg_response_time"] = 50  # ms

        # 数据完整性
        metrics["data_completeness"] = len(self.device_data_cache) / 22  # 总共22个设备

        return metrics

    def get_device_history(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取设备历史数据
        :param device_id: 设备ID
        :param limit: 返回记录数限制
        :return: 历史数据列表
        """
        history = self.historical_data.get(device_id, [])
        return history[-limit:] if len(history) > limit else history

    def clear_history(self, device_id: Optional[str] = None):
        """
        清除历史数据
        :param device_id: 设备ID，如果为None则清除所有
        """
        if device_id:
            self.historical_data[device_id] = []
            logger.info(f"清除设备{device_id}的历史数据")
        else:
            self.historical_data.clear()
            logger.info("清除所有设备的历史数据")

    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            "device_count": len(self.device_data_cache),
            "total_records": sum(len(h) for h in self.historical_data.values()),
            "statistics": dict(self.statistics)
        }