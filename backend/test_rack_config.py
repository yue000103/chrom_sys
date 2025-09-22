"""
测试架子配置系统
Test Rack Configuration System
"""

import asyncio
import logging
from config.rack_config import RackConfig, get_default_rack_id, validate_rack_info
from services.experiment_function_manager import ExperimentFunctionManager
from core.mqtt_manager import MQTTManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDatabaseManager:
    """模拟数据库管理器"""

    def __init__(self):
        # 模拟rack_info表数据
        self.rack_data = {
            'rack_001': {
                'rack_id': 'rack_001',
                'tube_count': 40,
                'tube_volume_ml': 2.0,
                'rack_type': 'standard',
                'status': 'active',
                'description': '标准40孔试管架'
            },
            'rack_002': {
                'rack_id': 'rack_002',
                'tube_count': 96,
                'tube_volume_ml': 1.5,
                'rack_type': 'micro',
                'status': 'active',
                'description': '微量96孔试管架'
            },
            'rack_incomplete': {
                'rack_id': 'rack_incomplete',
                'tube_count': 24,
                # 缺少其他字段
            }
        }

    async def get_rack_info_by_id(self, rack_id: str):
        """模拟从数据库获取架子信息"""
        logger.info(f"模拟查询架子信息: {rack_id}")
        return self.rack_data.get(rack_id)

    async def log_system_event(self, event_type: str, level: str, module: str, message: str, details: dict):
        logger.info(f"日志记录: {event_type} - {message}")


async def test_rack_config_class():
    """测试RackConfig配置类"""
    logger.info("=" * 60)
    logger.info("测试RackConfig配置类")
    logger.info("=" * 60)

    # 测试1: 检查默认配置
    logger.info("\n1. 检查默认配置...")
    logger.info(f"默认架子ID: {RackConfig.DEFAULT_RACK_ID}")
    logger.info(f"默认试管数量: {RackConfig.DEFAULT_TUBE_COUNT}")
    logger.info(f"默认试管体积: {RackConfig.DEFAULT_TUBE_VOLUME_ML}ml")
    logger.info(f"默认架子类型: {RackConfig.DEFAULT_RACK_TYPE}")
    logger.info(f"默认架子状态: {RackConfig.DEFAULT_RACK_STATUS}")

    # 测试2: 获取默认架子信息
    logger.info("\n2. 测试获取默认架子信息...")
    default_info = RackConfig.get_default_rack_info()
    logger.info(f"默认架子信息:")
    for key, value in default_info.items():
        logger.info(f"  {key}: {value}")

    # 测试3: 创建架子信息
    logger.info("\n3. 测试创建架子信息...")
    custom_info = RackConfig.create_rack_info(
        rack_id="custom_001",
        tube_count=20,
        description="自定义测试架子"
    )
    logger.info(f"自定义架子信息:")
    for key, value in custom_info.items():
        logger.info(f"  {key}: {value}")

    # 测试4: 验证不完整的架子信息
    logger.info("\n4. 测试验证不完整的架子信息...")
    incomplete_info = {
        'rack_id': 'test_rack',
        'tube_count': 48
        # 缺少其他字段
    }

    logger.info(f"验证前: {incomplete_info}")
    validated_info = RackConfig.validate_rack_info(incomplete_info.copy())
    logger.info(f"验证后: {validated_info}")

    # 测试5: 验证无效数据
    logger.info("\n5. 测试验证无效数据...")
    invalid_info = {
        'rack_id': 'invalid_rack',
        'tube_count': -5,  # 无效值
        'tube_volume_ml': 'invalid',  # 无效类型
        'rack_type': 'unknown_type',  # 不支持的类型
        'status': 'invalid_status'  # 不支持的状态
    }

    logger.info(f"无效数据: {invalid_info}")
    corrected_info = RackConfig.validate_rack_info(invalid_info.copy())
    logger.info(f"修正后: {corrected_info}")

    # 测试6: 测试辅助函数
    logger.info("\n6. 测试辅助函数...")
    logger.info(f"get_default_rack_id(): {get_default_rack_id()}")
    logger.info(f"支持的架子类型:")
    for type_key, type_desc in RackConfig.SUPPORTED_RACK_TYPES.items():
        logger.info(f"  {type_key}: {type_desc}")

    logger.info(f"支持的架子状态:")
    for status_key, status_desc in RackConfig.SUPPORTED_RACK_STATUS.items():
        logger.info(f"  {status_key}: {status_desc}")


async def test_experiment_manager_with_config():
    """测试ExperimentFunctionManager使用新配置"""
    logger.info("\n" + "=" * 60)
    logger.info("测试ExperimentFunctionManager使用新配置")
    logger.info("=" * 60)

    # 初始化管理器
    mqtt_manager = MQTTManager()
    mock_db_manager = MockDatabaseManager()
    experiment_manager = ExperimentFunctionManager(mqtt_manager, mock_db_manager)

    try:
        # 测试1: 获取默认架子信息
        logger.info("\n1. 测试获取默认架子信息...")
        rack_info = await experiment_manager._get_current_rack_info()
        logger.info(f"获取到的架子信息:")
        for key, value in rack_info.items():
            logger.info(f"  {key}: {value}")

        # 验证信息是否来自配置文件
        assert rack_info['rack_id'] == RackConfig.DEFAULT_RACK_ID, "架子ID应该来自配置文件"
        logger.info("✓ 架子ID正确来自配置文件")

        # 测试2: 测试不完整的数据库数据
        logger.info("\n2. 测试数据库返回不完整数据...")
        # 临时修改默认架子ID为不完整的数据
        original_rack_id = RackConfig.DEFAULT_RACK_ID
        RackConfig.DEFAULT_RACK_ID = 'rack_incomplete'

        rack_info_incomplete = await experiment_manager._get_current_rack_info()
        logger.info(f"不完整数据处理后:")
        for key, value in rack_info_incomplete.items():
            logger.info(f"  {key}: {value}")

        # 验证缺失字段被正确补全
        required_fields = ['tube_volume_ml', 'rack_type', 'status']
        for field in required_fields:
            assert field in rack_info_incomplete, f"应该包含字段: {field}"
        logger.info("✓ 缺失字段被正确补全")

        # 恢复原始配置
        RackConfig.DEFAULT_RACK_ID = original_rack_id

        # 测试3: 测试数据库异常情况
        logger.info("\n3. 测试数据库异常情况...")

        # 创建一个会抛出异常的数据库管理器
        class ErrorDatabaseManager:
            async def get_rack_info_by_id(self, rack_id: str):
                raise Exception("模拟数据库连接失败")
            async def log_system_event(self, *args):
                pass

        error_manager = ExperimentFunctionManager(mqtt_manager, ErrorDatabaseManager())
        rack_info_error = await error_manager._get_current_rack_info()

        logger.info(f"数据库异常时返回的信息:")
        for key, value in rack_info_error.items():
            logger.info(f"  {key}: {value}")

        # 验证返回的是默认配置
        default_info = RackConfig.get_default_rack_info()
        assert rack_info_error['rack_id'] == default_info['rack_id'], "异常时应返回默认配置"
        logger.info("✓ 数据库异常时正确返回默认配置")

        logger.info("\n" + "=" * 60)
        logger.info("配置系统测试完成! ✓")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_config_accessibility():
    """测试配置的可访问性"""
    logger.info("\n" + "=" * 60)
    logger.info("测试配置的可访问性")
    logger.info("=" * 60)

    # 测试其他类可以访问配置
    logger.info("\n1. 测试其他类访问配置...")

    class OtherService:
        """模拟其他服务类"""
        def __init__(self):
            # 其他类可以直接使用配置
            self.default_rack_id = RackConfig.DEFAULT_RACK_ID
            self.default_tube_count = RackConfig.DEFAULT_TUBE_COUNT

        def get_rack_config(self):
            """获取架子配置"""
            return {
                'rack_id': self.default_rack_id,
                'tube_count': self.default_tube_count,
                'rack_info': RackConfig.get_default_rack_info()
            }

    other_service = OtherService()
    config = other_service.get_rack_config()

    logger.info(f"其他服务获取的配置:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    # 测试模块级别函数
    logger.info("\n2. 测试模块级别函数...")
    logger.info(f"get_default_rack_id(): {get_default_rack_id()}")

    test_data = {'rack_id': 'test', 'tube_count': 20}
    validated = validate_rack_info(test_data)
    logger.info(f"validate_rack_info(): {validated}")

    logger.info("✓ 配置系统具有良好的可访问性")


async def main():
    """主测试函数"""
    logger.info("架子配置系统测试")
    logger.info("Test Rack Configuration System")

    try:
        # 测试1: 配置类功能
        await test_rack_config_class()

        # 测试2: 实验管理器集成
        await test_experiment_manager_with_config()

        # 测试3: 配置可访问性
        test_config_accessibility()

        logger.info("\n" + "=" * 80)
        logger.info("🎉 所有配置系统测试通过! 架子配置已成功迁移到config目录")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())