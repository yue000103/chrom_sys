"""
试管收集功能测试脚本
Test Tube Collection Functionality
"""

import asyncio
import logging
import time
from datetime import datetime
from services.tube_manager import TubeCollectionManager
from models.experiment_function_models import (
    ExperimentConfig,
    ExperimentProgress,
    ExperimentStatus,
    ExperimentPhase
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockMQTTManager:
    """模拟MQTT管理器"""

    async def publish_data(self, topic: str, data: dict):
        logger.info(f"MQTT推送: {topic} -> {data}")


class MockDatabaseManager:
    """模拟数据库管理器"""

    async def log_system_event(self, event_type: str, level: str, module: str, message: str, details: dict):
        logger.info(f"日志记录: {event_type} - {message}")


async def test_tube_collection_manager():
    """测试试管收集管理器"""
    logger.info("=" * 60)
    logger.info("测试试管收集管理器")
    logger.info("=" * 60)

    # 测试1: 初始化管理器
    logger.info("\n1. 测试初始化...")
    flow_rate = 10.0  # ml/min
    collection_volume = 2.0  # ml

    tube_manager = TubeCollectionManager(flow_rate, collection_volume)
    logger.info(f"收集时间: {tube_manager.get_collection_time_per_tube():.2f}秒")

    # 测试2: 积分函数
    logger.info("\n2. 测试积分函数...")
    start_time = 0.0

    # 测试收集未完成
    current_time = 5.0  # 5秒
    is_complete = tube_manager.is_collection_complete(start_time, current_time)
    logger.info(f"5秒时是否完成: {is_complete}")

    # 测试收集完成
    current_time = 15.0  # 15秒（大于12秒的收集时间）
    is_complete = tube_manager.is_collection_complete(start_time, current_time)
    logger.info(f"15秒时是否完成: {is_complete}")

    # 测试3: 试管数据创建
    logger.info("\n3. 测试试管数据创建...")
    tube_data = tube_manager.create_tube_data(0.0, 12.0, 1)
    logger.info(f"试管数据: {tube_data}")

    # 测试4: 试管切换
    logger.info("\n4. 测试试管切换...")
    success = await tube_manager.switch_to_tube(2)
    logger.info(f"切换结果: {success}")

    # 测试5: 状态信息
    logger.info("\n5. 测试状态信息...")
    status = tube_manager.get_status_info()
    logger.info(f"状态信息: {status}")

    return True


async def test_experiment_flow():
    """测试完整实验流程"""
    logger.info("\n" + "=" * 60)
    logger.info("测试完整实验流程")
    logger.info("=" * 60)

    # 模拟实验管理器
    from services.experiment_function_manager import ExperimentFunctionManager

    mqtt_manager = MockMQTTManager()
    db_manager = MockDatabaseManager()

    experiment_manager = ExperimentFunctionManager(mqtt_manager, db_manager)

    # 创建实验配置
    config = ExperimentConfig(
        experiment_id="test_exp_001",
        experiment_name="试管收集测试实验",
        method_id="method_001",
        sample_id="sample_001",
        user_id="test_user"
    )

    try:
        # 启动实验
        logger.info("\n启动实验...")
        progress = await experiment_manager.start_experiment(config)
        logger.info(f"实验启动成功: {progress.experiment_id}")

        # 等待一段时间让实验运行
        logger.info("\n等待实验运行...")
        await asyncio.sleep(5)

        # 检查实验进度
        current_progress = await experiment_manager.get_experiment_progress(config.experiment_id)
        if current_progress:
            logger.info(f"当前进度: {current_progress.progress_percentage:.1f}%")
            logger.info(f"当前步骤: {current_progress.current_step}")
            logger.info(f"当前试管: {current_progress.current_tube_id}")
            logger.info(f"收集缓存: {len(current_progress.tube_collection_cache)} 个试管")

        # 暂停实验
        logger.info("\n暂停实验...")
        await experiment_manager.pause_experiment(config.experiment_id, "test_user", "测试暂停")
        await asyncio.sleep(2)

        # 恢复实验
        logger.info("\n恢复实验...")
        await experiment_manager.resume_experiment(config.experiment_id, "test_user")
        await asyncio.sleep(3)

        # 停止实验
        logger.info("\n停止实验...")
        result = await experiment_manager.stop_experiment(config.experiment_id, "test_user", "测试完成")
        logger.info(f"实验结果: {result.final_status}")

    except Exception as e:
        logger.error(f"实验测试失败: {e}")


async def test_collection_timing():
    """测试收集时间计算"""
    logger.info("\n" + "=" * 60)
    logger.info("测试收集时间计算")
    logger.info("=" * 60)

    # 不同参数的测试用例
    test_cases = [
        {"flow_rate": 10.0, "volume": 2.0, "expected_time": 12.0},  # 2ml / 10ml/min * 60 = 12秒
        {"flow_rate": 5.0, "volume": 1.0, "expected_time": 12.0},   # 1ml / 5ml/min * 60 = 12秒
        {"flow_rate": 20.0, "volume": 4.0, "expected_time": 12.0},  # 4ml / 20ml/min * 60 = 12秒
        {"flow_rate": 8.0, "volume": 1.6, "expected_time": 12.0},   # 1.6ml / 8ml/min * 60 = 12秒
    ]

    for i, case in enumerate(test_cases):
        logger.info(f"\n测试用例 {i+1}:")
        logger.info(f"  流速: {case['flow_rate']} ml/min")
        logger.info(f"  体积: {case['volume']} ml")

        manager = TubeCollectionManager(case['flow_rate'], case['volume'])
        actual_time = manager.get_collection_time_per_tube()

        logger.info(f"  计算时间: {actual_time:.2f}秒")
        logger.info(f"  预期时间: {case['expected_time']:.2f}秒")
        logger.info(f"  结果: {'✓' if abs(actual_time - case['expected_time']) < 0.1 else '✗'}")


async def test_progress_calculation():
    """测试进度计算"""
    logger.info("\n" + "=" * 60)
    logger.info("测试进度计算")
    logger.info("=" * 60)

    flow_rate = 12.0  # ml/min
    volume = 2.4      # ml
    manager = TubeCollectionManager(flow_rate, volume)

    collection_time = manager.get_collection_time_per_tube()
    logger.info(f"每管收集时间: {collection_time:.2f}秒")

    # 测试不同时间点的进度
    test_times = [0, 2, 5, 8, 10, 12, 15]

    for test_time in test_times:
        progress = manager.get_collection_progress(test_time, 0)
        logger.info(f"时间 {test_time:2d}秒: 进度 {progress:5.1f}%")

    # 测试剩余时间估算
    logger.info(f"\n剩余时间估算:")
    current_tube = 5
    tube_start = 0
    current_time = 6  # 当前试管已运行6秒

    remaining = manager.estimate_remaining_time(current_tube, tube_start, current_time)
    logger.info(f"当前试管 {current_tube}, 已运行 {current_time}秒")
    logger.info(f"估算剩余时间: {remaining:.1f}秒 ({remaining/60:.1f}分钟)")


async def main():
    """主测试函数"""
    logger.info("液相色谱试管收集功能测试")
    logger.info("Test Tube Collection Functionality")

    try:
        # 测试1: 试管收集管理器基础功能
        await test_tube_collection_manager()

        # 测试2: 收集时间计算
        await test_collection_timing()

        # 测试3: 进度计算
        await test_progress_calculation()

        # 测试4: 完整实验流程（可选，需要更多依赖）
        # await test_experiment_flow()

        logger.info("\n" + "=" * 60)
        logger.info("所有测试完成!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())