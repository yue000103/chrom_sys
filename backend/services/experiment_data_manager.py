"""
实验数据管理器
Experiment Data Manager
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from core.mqtt_manager import MQTTManager
from data.database_utils import ChromatographyDB
from models.experiment_data_models import (
    SensorDataPoint,
    PeakInfo,
    ExperimentDataSummary,
    DataQualityMetrics,
    DataExportRequest,
    DataExportFormat,
    ProcessingParameters,
    BaselineInfo,
    DataType,
    DataQuality
)

logger = logging.getLogger(__name__)


class ExperimentDataManager:
    """实验数据管理器"""

    def __init__(self, mqtt_manager: MQTTManager):
        self.mqtt_manager = mqtt_manager
        self.db = ChromatographyDB()
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.data_buffers: Dict[str, List[SensorDataPoint]] = {}
        self.processing_queue: List[Dict[str, Any]] = []

    async def start_data_collection(self, experiment_id: str, collection_config: Dict[str, Any]) -> bool:
        """开始数据采集"""
        logger.info(f"开始数据采集: {experiment_id}")

        if experiment_id in self.active_experiments:
            raise ValueError(f"实验 {experiment_id} 数据采集已在进行中")

        # 初始化实验数据结构
        self.active_experiments[experiment_id] = {
            "start_time": datetime.now(),
            "config": collection_config,
            "status": "collecting",
            "total_data_points": 0,
            "last_data_time": None,
            "sampling_rate_hz": collection_config.get("sampling_rate", 10),
            "devices": collection_config.get("devices", ["detector", "pressure", "flow"])
        }

        self.data_buffers[experiment_id] = []

        # 发布数据采集开始消息
        await self.mqtt_manager.publish_data(
            "data/collection_started",
            {
                "experiment_id": experiment_id,
                "devices": self.active_experiments[experiment_id]["devices"],
                "sampling_rate": self.active_experiments[experiment_id]["sampling_rate_hz"],
                "timestamp": datetime.now().isoformat()
            }
        )

        # 启动数据采集任务
        asyncio.create_task(self._collect_data_loop(experiment_id))

        logger.info(f"数据采集已启动: {experiment_id}")
        return True

    async def stop_data_collection(self, experiment_id: str) -> ExperimentDataSummary:
        """停止数据采集"""
        logger.info(f"停止数据采集: {experiment_id}")

        if experiment_id not in self.active_experiments:
            raise ValueError(f"实验 {experiment_id} 数据采集未在进行中")

        experiment_info = self.active_experiments[experiment_id]
        experiment_info["status"] = "stopped"
        experiment_info["end_time"] = datetime.now()

        # 计算数据摘要
        data_points = self.data_buffers.get(experiment_id, [])
        summary = await self._generate_data_summary(experiment_id, data_points)

        # 保存数据到数据库
        await self._save_experiment_data(experiment_id, data_points, summary)

        # 清理内存中的数据
        self.active_experiments.pop(experiment_id, None)
        self.data_buffers.pop(experiment_id, None)

        # 发布数据采集完成消息
        await self.mqtt_manager.publish_data(
            "data/collection_completed",
            {
                "experiment_id": experiment_id,
                "total_data_points": summary.total_data_points,
                "duration_minutes": summary.duration_minutes,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"数据采集已完成: {experiment_id}")
        return summary

    async def add_data_point(self, experiment_id: str, data_point: SensorDataPoint) -> bool:
        """添加数据点"""
        if experiment_id not in self.active_experiments:
            return False

        experiment_info = self.active_experiments[experiment_id]
        if experiment_info["status"] != "collecting":
            return False

        # 添加数据点到缓冲区
        self.data_buffers[experiment_id].append(data_point)
        experiment_info["total_data_points"] += 1
        experiment_info["last_data_time"] = data_point.timestamp

        # 定期发布实时数据状态
        if experiment_info["total_data_points"] % 100 == 0:
            await self.mqtt_manager.publish_data(
                "data/real_time_status",
                {
                    "experiment_id": experiment_id,
                    "total_points": experiment_info["total_data_points"],
                    "last_value": data_point.value,
                    "timestamp": datetime.now().isoformat()
                }
            )

        return True

    async def process_experiment_data(self, experiment_id: str, processing_params: ProcessingParameters) -> Dict[str, Any]:
        """处理实验数据"""
        logger.info(f"开始处理实验数据: {experiment_id}")

        # 获取原始数据
        raw_data = await self._get_experiment_raw_data(experiment_id)
        if not raw_data:
            raise ValueError(f"未找到实验 {experiment_id} 的数据")

        processing_result = {
            "experiment_id": experiment_id,
            "processing_start_time": datetime.now(),
            "steps_completed": [],
            "processing_errors": []
        }

        try:
            # 步骤1: 基线校正
            if processing_params.baseline_correction:
                corrected_data = await self._apply_baseline_correction(raw_data, processing_params)
                processing_result["steps_completed"].append("baseline_correction")
                logger.info("基线校正完成")
            else:
                corrected_data = raw_data

            # 步骤2: 噪声滤波
            if processing_params.noise_filtering:
                filtered_data = await self._apply_noise_filtering(corrected_data, processing_params)
                processing_result["steps_completed"].append("noise_filtering")
                logger.info("噪声滤波完成")
            else:
                filtered_data = corrected_data

            # 步骤3: 峰检测
            if processing_params.peak_detection:
                peaks = await self._detect_peaks(filtered_data, processing_params)
                processing_result["detected_peaks"] = len(peaks)
                processing_result["steps_completed"].append("peak_detection")
                logger.info(f"峰检测完成，检测到 {len(peaks)} 个峰")
            else:
                peaks = []

            # 步骤4: 数据质量评估
            quality_metrics = await self._assess_data_quality(filtered_data, peaks)
            processing_result["quality_metrics"] = quality_metrics

            # 保存处理结果
            await self._save_processed_data(experiment_id, {
                "processed_data": filtered_data,
                "detected_peaks": peaks,
                "quality_metrics": quality_metrics,
                "processing_parameters": processing_params.dict()
            })

            processing_result["processing_end_time"] = datetime.now()
            processing_result["success"] = True

            logger.info(f"数据处理完成: {experiment_id}")
            return processing_result

        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            processing_result["processing_errors"].append(str(e))
            processing_result["success"] = False
            return processing_result

    async def detect_peaks(self, experiment_id: str, detection_params: Dict[str, Any]) -> List[PeakInfo]:
        """峰检测"""
        logger.info(f"执行峰检测: {experiment_id}")

        # 获取处理后的数据
        processed_data = await self._get_experiment_processed_data(experiment_id)
        if not processed_data:
            # 如果没有处理后的数据，使用原始数据
            processed_data = await self._get_experiment_raw_data(experiment_id)

        if not processed_data:
            raise ValueError(f"未找到实验 {experiment_id} 的数据")

        # 执行峰检测
        peaks = await self._detect_peaks_with_params(processed_data, detection_params)

        # 保存峰检测结果
        await self._save_peak_detection_results(experiment_id, peaks, detection_params)

        # 发布峰检测完成消息
        await self.mqtt_manager.publish_data(
            "data/peak_detection_completed",
            {
                "experiment_id": experiment_id,
                "detected_peaks": len(peaks),
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"峰检测完成: {experiment_id}, 检测到 {len(peaks)} 个峰")
        return peaks

    async def export_experiment_data(self, export_request: DataExportRequest) -> Dict[str, Any]:
        """导出实验数据"""
        logger.info(f"导出实验数据: {export_request.experiment_id}")

        export_result = {
            "experiment_id": export_request.experiment_id,
            "export_format": export_request.export_format,
            "export_start_time": datetime.now(),
            "files_created": [],
            "success": False
        }

        try:
            # 获取数据
            raw_data = await self._get_experiment_raw_data(export_request.experiment_id)
            processed_data = await self._get_experiment_processed_data(export_request.experiment_id)
            peaks = await self._get_experiment_peaks(export_request.experiment_id)
            metadata = await self._get_experiment_metadata(export_request.experiment_id)

            # 根据格式导出
            if export_request.export_format == DataExportFormat.CSV:
                files = await self._export_to_csv(export_request, raw_data, processed_data, peaks, metadata)
            elif export_request.export_format == DataExportFormat.EXCEL:
                files = await self._export_to_excel(export_request, raw_data, processed_data, peaks, metadata)
            elif export_request.export_format == DataExportFormat.JSON:
                files = await self._export_to_json(export_request, raw_data, processed_data, peaks, metadata)
            else:
                raise ValueError(f"不支持的导出格式: {export_request.export_format}")

            export_result["files_created"] = files
            export_result["export_end_time"] = datetime.now()
            export_result["success"] = True

            logger.info(f"数据导出完成: {export_request.experiment_id}")
            return export_result

        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            export_result["error"] = str(e)
            export_result["export_end_time"] = datetime.now()
            return export_result

    async def get_data_quality_metrics(self, experiment_id: str) -> DataQualityMetrics:
        """获取数据质量指标"""
        raw_data = await self._get_experiment_raw_data(experiment_id)
        if not raw_data:
            raise ValueError(f"未找到实验 {experiment_id} 的数据")

        return await self._calculate_quality_metrics(raw_data)

    async def get_experiment_summary(self, experiment_id: str) -> ExperimentDataSummary:
        """获取实验数据摘要"""
        return await self._get_stored_experiment_summary(experiment_id)

    # 私有方法

    async def _collect_data_loop(self, experiment_id: str):
        """数据采集循环"""
        experiment_info = self.active_experiments[experiment_id]
        sampling_interval = 1.0 / experiment_info["sampling_rate_hz"]

        try:
            while experiment_info["status"] == "collecting":
                # 模拟从硬件设备读取数据
                data_points = await self._simulate_sensor_readings(experiment_id)

                for data_point in data_points:
                    await self.add_data_point(experiment_id, data_point)

                await asyncio.sleep(sampling_interval)

        except Exception as e:
            logger.error(f"数据采集循环异常: {e}")
            experiment_info["status"] = "error"

    async def _simulate_sensor_readings(self, experiment_id: str) -> List[SensorDataPoint]:
        """模拟传感器读数"""
        current_time = datetime.now()
        data_points = []

        experiment_info = self.active_experiments[experiment_id]
        devices = experiment_info["devices"]

        for i, device in enumerate(devices):
            # 模拟不同设备的数据
            if device == "detector":
                value = np.random.normal(0.5, 0.1)  # 模拟检测器信号
                data_type = DataType.DETECTOR
                unit = "AU"
            elif device == "pressure":
                value = np.random.normal(200, 5)     # 模拟压力传感器
                data_type = DataType.PRESSURE
                unit = "bar"
            elif device == "flow":
                value = np.random.normal(1.0, 0.02)  # 模拟流量传感器
                data_type = DataType.FLOW
                unit = "mL/min"
            else:
                value = np.random.random()
                data_type = DataType.DETECTOR  # 默认类型
                unit = "AU"

            # 生成唯一的数据ID
            data_id = f"{experiment_id}_{device}_{int(current_time.timestamp() * 1000)}_{i}"

            data_point = SensorDataPoint(
                data_id=data_id,
                experiment_id=experiment_id,
                device_id=device,
                timestamp=current_time,
                value=value,
                unit=unit,
                data_type=data_type,
                quality=DataQuality.GOOD
            )
            data_points.append(data_point)

        return data_points

    async def _generate_data_summary(self, experiment_id: str, data_points: List[SensorDataPoint]) -> ExperimentDataSummary:
        """生成数据摘要"""
        if not data_points:
            return ExperimentDataSummary(
                experiment_id=experiment_id,
                total_data_points=0,
                duration_minutes=0,
                sampling_rate_hz=0,
                data_quality_score=0
            )

        start_time = min(dp.timestamp for dp in data_points)
        end_time = max(dp.timestamp for dp in data_points)
        duration = (end_time - start_time).total_seconds() / 60

        # 按设备分组
        devices_data = {}
        for dp in data_points:
            if dp.device_id not in devices_data:
                devices_data[dp.device_id] = []
            devices_data[dp.device_id].append(dp)

        return ExperimentDataSummary(
            experiment_id=experiment_id,
            start_time=start_time,
            end_time=end_time,
            total_data_points=len(data_points),
            duration_minutes=duration,
            sampling_rate_hz=len(data_points) / (duration * 60) if duration > 0 else 0,
            devices_count=len(devices_data),
            data_quality_score=95.0  # 简化处理
        )

    async def _apply_baseline_correction(self, data: List[SensorDataPoint], params: ProcessingParameters) -> List[SensorDataPoint]:
        """应用基线校正"""
        # 简化的基线校正实现
        if not data:
            return data

        # 计算移动平均作为基线
        window_size = params.baseline_window_size or 50
        corrected_data = []

        for i, point in enumerate(data):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(data), i + window_size // 2)
            baseline = np.mean([dp.value for dp in data[start_idx:end_idx]])

            corrected_point = SensorDataPoint(
                data_id=f"{point.data_id}_corrected",
                experiment_id=point.experiment_id,
                device_id=point.device_id,
                timestamp=point.timestamp,
                value=point.value - baseline,
                unit=point.unit,
                data_type=point.data_type,
                quality=point.quality
            )
            corrected_data.append(corrected_point)

        return corrected_data

    async def _apply_noise_filtering(self, data: List[SensorDataPoint], params: ProcessingParameters) -> List[SensorDataPoint]:
        """应用噪声滤波"""
        # 简化的滤波实现（移动平均）
        if not data:
            return data

        filter_window = params.filter_window_size or 5
        filtered_data = []

        for i, point in enumerate(data):
            start_idx = max(0, i - filter_window // 2)
            end_idx = min(len(data), i + filter_window // 2)
            filtered_value = np.mean([dp.value for dp in data[start_idx:end_idx]])

            filtered_point = SensorDataPoint(
                data_id=f"{point.data_id}_filtered",
                experiment_id=point.experiment_id,
                device_id=point.device_id,
                timestamp=point.timestamp,
                value=filtered_value,
                unit=point.unit,
                data_type=point.data_type,
                quality=point.quality
            )
            filtered_data.append(filtered_point)

        return filtered_data

    async def _detect_peaks(self, data: List[SensorDataPoint], params: ProcessingParameters) -> List[PeakInfo]:
        """检测峰"""
        return await self._detect_peaks_with_params(data, {
            "threshold": params.peak_threshold or 0.1,
            "min_peak_height": params.min_peak_height or 0.05,
            "min_peak_width": params.min_peak_width or 0.1
        })

    async def _detect_peaks_with_params(self, data: List[SensorDataPoint], params: Dict[str, Any]) -> List[PeakInfo]:
        """使用指定参数检测峰"""
        if not data:
            return []

        # 简化的峰检测算法
        threshold = params.get("threshold", 0.1)
        min_height = params.get("min_peak_height", 0.05)
        min_width = params.get("min_peak_width", 0.1)

        peaks = []
        values = [dp.value for dp in data]
        # 计算相对于第一个数据点的时间差（分钟）
        if data:
            start_time = data[0].timestamp
            times = [(dp.timestamp - start_time).total_seconds() / 60 for dp in data]
        else:
            times = []

        # 寻找局部最大值
        for i in range(1, len(values) - 1):
            if (values[i] > values[i-1] and values[i] > values[i+1] and
                values[i] > threshold and values[i] > min_height):

                # 计算峰宽（简化）
                peak_width = self._calculate_peak_width(values, i, min_height)

                if peak_width >= min_width:
                    peak = PeakInfo(
                        experiment_id=data[i].experiment_id,
                        peak_id=f"peak_{len(peaks)+1:03d}",
                        peak_number=len(peaks)+1,
                        retention_time=times[i],
                        height=values[i],
                        area=values[i] * peak_width,  # 简化面积计算
                        width_at_half_height=peak_width,
                        baseline_start=times[max(0, i-5)],
                        baseline_end=times[min(len(times)-1, i+5)],
                        confidence=0.9
                    )
                    peaks.append(peak)

        return peaks

    def _calculate_peak_width(self, values: List[float], peak_idx: int, baseline: float) -> float:
        """计算峰宽"""
        # 简化的峰宽计算
        half_height = (values[peak_idx] + baseline) / 2

        # 向左寻找半高点
        left_idx = peak_idx
        while left_idx > 0 and values[left_idx] > half_height:
            left_idx -= 1

        # 向右寻找半高点
        right_idx = peak_idx
        while right_idx < len(values) - 1 and values[right_idx] > half_height:
            right_idx += 1

        return (right_idx - left_idx) * 0.1  # 假设每个点代表0.1分钟

    async def _assess_data_quality(self, data: List[SensorDataPoint], peaks: List[PeakInfo]) -> DataQualityMetrics:
        """评估数据质量"""
        if not data:
            return DataQualityMetrics(
                experiment_id=data[0].experiment_id if data else "",
                overall_score=0,
                noise_level=0,
                baseline_stability=0,
                peak_resolution=0,
                signal_to_noise_ratio=0
            )

        values = [dp.value for dp in data]

        # 计算噪声水平
        noise_level = float(np.std(values))

        # 计算基线稳定性
        baseline_stability = 100 - (noise_level * 100)

        # 计算信噪比
        if peaks:
            max_signal = max(peak.height for peak in peaks)
            snr = max_signal / noise_level if noise_level > 0 else 100
        else:
            snr = 1

        # 计算峰分离度
        peak_resolution = self._calculate_peak_resolution(peaks)

        # 综合评分
        overall_score = min(100, (baseline_stability + min(snr*10, 50) + peak_resolution) / 3)

        return DataQualityMetrics(
            experiment_id=data[0].experiment_id,
            overall_score=overall_score,
            noise_level=noise_level,
            baseline_stability=baseline_stability,
            peak_resolution=peak_resolution,
            signal_to_noise_ratio=snr
        )

    def _calculate_peak_resolution(self, peaks: List[PeakInfo]) -> float:
        """计算峰分离度"""
        if len(peaks) < 2:
            return 100

        # 简化的分离度计算
        min_resolution = 100
        for i in range(len(peaks) - 1):
            current_peak = peaks[i]
            next_peak = peaks[i + 1]

            time_diff = next_peak.retention_time - current_peak.retention_time
            width_sum = current_peak.width_at_half_height + next_peak.width_at_half_height

            resolution = (2 * time_diff) / width_sum if width_sum > 0 else 0
            min_resolution = min(min_resolution, resolution * 50)  # 转换为0-100分数

        return max(0, min(100, min_resolution))

    # 数据存储相关方法
    async def _save_experiment_data(self, experiment_id: str, data_points: List[SensorDataPoint], summary: ExperimentDataSummary):
        """保存实验数据到数据库"""
        try:
            # 这里应该实现实际的数据库保存逻辑
            await self.db_manager.log_system_event(
                "data_saved",
                "info",
                "data_manager",
                f"保存实验数据: {experiment_id}",
                {
                    "experiment_id": experiment_id,
                    "data_points": len(data_points),
                    "summary": summary.dict()
                }
            )
        except Exception as e:
            logger.error(f"保存实验数据失败: {e}")

    async def _save_processed_data(self, experiment_id: str, processed_result: Dict[str, Any]):
        """保存处理后的数据"""
        try:
            await self.db_manager.log_system_event(
                "data_processed",
                "info",
                "data_manager",
                f"保存处理后数据: {experiment_id}",
                processed_result
            )
        except Exception as e:
            logger.error(f"保存处理后数据失败: {e}")

    async def _save_peak_detection_results(self, experiment_id: str, peaks: List[PeakInfo], params: Dict[str, Any]):
        """保存峰检测结果"""
        try:
            await self.db_manager.log_system_event(
                "peaks_detected",
                "info",
                "data_manager",
                f"保存峰检测结果: {experiment_id}",
                {
                    "experiment_id": experiment_id,
                    "peaks_count": len(peaks),
                    "detection_params": params
                }
            )
        except Exception as e:
            logger.error(f"保存峰检测结果失败: {e}")

    # 数据检索相关方法
    async def _get_experiment_raw_data(self, experiment_id: str) -> List[SensorDataPoint]:
        """获取实验原始数据"""
        # 这里应该实现从数据库获取数据的逻辑
        # 目前返回空列表
        return []

    async def _get_experiment_processed_data(self, experiment_id: str) -> List[SensorDataPoint]:
        """获取实验处理后数据"""
        return []

    async def _get_experiment_peaks(self, experiment_id: str) -> List[PeakInfo]:
        """获取实验峰信息"""
        return []

    async def _get_experiment_metadata(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验元数据"""
        return {}

    async def _get_stored_experiment_summary(self, experiment_id: str) -> ExperimentDataSummary:
        """获取存储的实验摘要"""
        # 这里应该实现从数据库获取摘要的逻辑
        return ExperimentDataSummary(
            experiment_id=experiment_id,
            total_data_points=0,
            duration_minutes=0,
            sampling_rate_hz=0,
            data_quality_score=0
        )

    async def _calculate_quality_metrics(self, data: List[SensorDataPoint]) -> DataQualityMetrics:
        """计算数据质量指标"""
        return await self._assess_data_quality(data, [])

    # 数据导出相关方法
    async def _export_to_csv(self, request: DataExportRequest, raw_data, processed_data, peaks, metadata) -> List[str]:
        """导出为CSV格式"""
        # 实现CSV导出逻辑
        return [f"{request.experiment_id}_data.csv"]

    async def _export_to_excel(self, request: DataExportRequest, raw_data, processed_data, peaks, metadata) -> List[str]:
        """导出为Excel格式"""
        # 实现Excel导出逻辑
        return [f"{request.experiment_id}_data.xlsx"]

    async def _export_to_json(self, request: DataExportRequest, raw_data, processed_data, peaks, metadata) -> List[str]:
        """导出为JSON格式"""
        # 实现JSON导出逻辑
        return [f"{request.experiment_id}_data.json"]

    def get_experiment_steps(self, experiment_id: str) -> List[str]:
        """
        根据experiment_id获取实验的所有步骤列表

        Args:
            experiment_id: 实验ID

        Returns:
            List[str]: 按顺序排列的实验步骤列表
        """
        try:
            # 查询实验信息
            experiments = self.db.query_data(
                "experiments",
                where_condition="experiment_id = ?",
                where_params=(experiment_id,)
            )

            if not experiments:
                logger.warning(f"未找到实验ID: {experiment_id}，返回默认步骤")
                return ["collect", "post_processing"]

            experiment = experiments[0]
            steps = []

            # 按照预处理顺序添加步骤

            # 1. 吹扫柱子
            if experiment.get('purge_column') == 1:
                steps.append("purge_column")

            # 2. 吹扫系统
            if experiment.get('purge_system') == 1:
                steps.append("purge_system")

            # 3. 润柱 (柱平衡)
            if experiment.get('column_balance') == 1:
                steps.append("column_equilibration")

            # 4. 收集 (固定步骤)
            steps.append("collect")

            # 5. 后处理 (固定步骤)
            steps.append("post_processing")

            logger.info(f"获取实验步骤: {experiment_id} -> {steps}")
            return steps

        except Exception as e:
            logger.error(f"获取实验步骤失败: {e}")
            # 返回最基本的步骤
            return ["collect", "post_processing"]