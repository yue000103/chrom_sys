"""
数据库初始化脚本
Database Initialization Script
"""

import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager


async def create_database_schema(db_path: Path):
    """创建完整的数据库结构"""

    # 确保目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")

        logger.info("创建数据库表结构...")

        # 1. 设备配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id VARCHAR(50) UNIQUE NOT NULL,
                device_name VARCHAR(100) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                device_model VARCHAR(100),
                communication_type VARCHAR(20) NOT NULL,
                connection_params TEXT,
                status VARCHAR(20) DEFAULT 'inactive',
                is_mock BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 传感器数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_type VARCHAR(50),
                value REAL NOT NULL,
                unit VARCHAR(20),
                raw_data TEXT,
                quality_flag INTEGER DEFAULT 1,
                FOREIGN KEY (device_id) REFERENCES device_config(device_id)
            )
        ''')

        # 3. 实验数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id VARCHAR(100) PRIMARY KEY,
                experiment_name VARCHAR(200) NOT NULL,
                experiment_type VARCHAR(50),
                method_id VARCHAR(100),
                operator VARCHAR(100),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                description TEXT,
                parameters TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 4. 方法配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_methods (
                method_id VARCHAR(100) PRIMARY KEY,
                method_name VARCHAR(200) NOT NULL,
                method_type VARCHAR(50),
                parameters TEXT,
                gradient_program TEXT,
                flow_rate REAL,
                column_temperature REAL,
                injection_volume REAL,
                detection_wavelength REAL,
                run_time REAL,
                status VARCHAR(20) DEFAULT 'active',
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. 色谱峰数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chromatography_peaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id VARCHAR(100) NOT NULL,
                peak_number INTEGER,
                retention_time REAL,
                peak_area REAL,
                peak_height REAL,
                peak_width REAL,
                peak_symmetry REAL,
                resolution REAL,
                theoretical_plates INTEGER,
                compound_name VARCHAR(200),
                concentration REAL,
                unit VARCHAR(20),
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            )
        ''')

        # 6. 系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                log_level VARCHAR(20),
                module VARCHAR(100),
                message TEXT,
                user VARCHAR(100),
                device_id VARCHAR(50),
                experiment_id VARCHAR(100),
                error_code VARCHAR(50),
                stack_trace TEXT
            )
        ''')

        # 7. 校准数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calibration_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id VARCHAR(50) NOT NULL,
                calibration_type VARCHAR(50),
                calibration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                calibrated_by VARCHAR(100),
                standard_values TEXT,
                measured_values TEXT,
                calibration_curve TEXT,
                r_squared REAL,
                status VARCHAR(20) DEFAULT 'valid',
                valid_until TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (device_id) REFERENCES device_config(device_id)
            )
        ''')

        # 8. 试管信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tube_info (
                tube_id VARCHAR(100) PRIMARY KEY,
                rack_id VARCHAR(50),
                position VARCHAR(20),
                tube_type VARCHAR(50),
                volume_ml REAL,
                sample_name VARCHAR(200),
                sample_type VARCHAR(50),
                concentration REAL,
                concentration_unit VARCHAR(20),
                status VARCHAR(20) DEFAULT 'empty',
                experiment_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            )
        ''')

        # 9. MQTT消息历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mqtt_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                topic VARCHAR(200) NOT NULL,
                payload TEXT,
                qos INTEGER DEFAULT 0,
                retained BOOLEAN DEFAULT 0,
                direction VARCHAR(10), -- 'publish' or 'subscribe'
                device_id VARCHAR(50),
                processed BOOLEAN DEFAULT 0
            )
        ''')

        # 10. 数据质量指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                signal_to_noise_ratio REAL,
                baseline_drift REAL,
                peak_symmetry REAL,
                retention_time_reproducibility REAL,
                detector_linearity REAL,
                data_completeness_percentage REAL,
                quality_score REAL,
                notes TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            )
        ''')

        # 创建索引以提高查询性能
        logger.info("创建索引...")

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_device ON sensor_data(device_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_peaks_experiment ON chromatography_peaks(experiment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mqtt_timestamp ON mqtt_messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mqtt_topic ON mqtt_messages(topic)')

        # 插入初始设备配置
        logger.info("插入初始设备配置...")

        initial_devices = [
            ('detector_1', '检测器1', 'detector', 'UV-2000', 'serial', '{"port": "ttyAMA3", "baudrate": 57600}', 'inactive', 1),
            ('pressure_sensor_1', '压力传感器1', 'pressure_sensor', 'PS-100', 'i2c', '{"address": "0x48"}', 'inactive', 1),
            ('pump_1', '泵控制器1', 'pump_controller', 'PUMP-4000', 'serial', '{"port": "ttyAMA2", "baudrate": 9600}', 'inactive', 1),
            ('relay_1', '继电器1', 'relay_controller', 'RELAY-8CH', 'gpio', '{"pins": [17, 27, 22, 10, 9, 11, 5, 6]}', 'inactive', 1),
            ('bubble_sensor_1', '气泡传感器1', 'bubble_sensor', 'BS-200', 'gpio', '{"pin": 23}', 'inactive', 1),
        ]

        for device in initial_devices:
            cursor.execute('''
                INSERT OR IGNORE INTO device_config
                (device_id, device_name, device_type, device_model, communication_type, connection_params, status, is_mock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', device)

        # 插入示例方法
        cursor.execute('''
            INSERT OR IGNORE INTO analysis_methods
            (method_id, method_name, method_type, flow_rate, column_temperature,
             injection_volume, detection_wavelength, run_time, created_by)
            VALUES
            ('method_001', '标准分析方法', 'standard', 1.0, 30.0, 20.0, 254.0, 60.0, 'system')
        ''')

        conn.commit()
        logger.info("数据库初始化完成!")

        # 显示创建的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"创建的表: {[table[0] for table in tables]}")

        # 显示数据库文件信息
        db_size = db_path.stat().st_size / 1024  # KB
        logger.info(f"数据库文件: {db_path}")
        logger.info(f"数据库大小: {db_size:.2f} KB")

    except Exception as e:
        logger.error(f"创建数据库时出错: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


async def main():
    """主函数"""
    # 设置数据库路径
    db_dir = Path(__file__).parent / "data" / "database"
    db_path = db_dir / "chromatography.db"

    logger.info("=" * 60)
    logger.info("液相色谱仪控制系统 - 数据库初始化")
    logger.info("=" * 60)

    # 检查数据库是否已存在
    if db_path.exists():
        logger.warning(f"数据库已存在: {db_path}")
        response = input("是否要重新创建数据库? (y/n): ")
        if response.lower() != 'y':
            logger.info("取消操作")
            return
        else:
            logger.info("删除旧数据库...")
            db_path.unlink()

    # 创建数据库
    logger.info(f"创建数据库: {db_path}")
    await create_database_schema(db_path)

    # 使用DatabaseManager测试连接
    logger.info("\n测试DatabaseManager连接...")
    db_manager = DatabaseManager(str(db_path))
    await db_manager.initialize()

    if await db_manager.test_connection():
        logger.info("✓ DatabaseManager连接测试成功!")
    else:
        logger.error("✗ DatabaseManager连接测试失败!")

    # 获取设备配置
    devices = await db_manager.get_device_config()
    logger.info(f"\n已注册设备: {len(devices)} 个")
    for device in devices:
        logger.info(f"  - {device['device_id']}: {device['device_name']} ({device['device_type']})")

    logger.info("\n" + "=" * 60)
    logger.info("数据库初始化完成!")
    logger.info("数据库路径: " + str(db_path))
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())