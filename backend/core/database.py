"""
SQLite数据库连接管理
液相色谱仪控制系统
"""

import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite数据库管理器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径
            db_dir = Path(__file__).parent.parent / "data" / "database"
            self.db_path = db_dir / "chromatography.db"
        else:
            self.db_path = Path(db_path)

        self.connection_pool = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化数据库连接"""
        try:
            # 确保数据库目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # 检查数据库是否存在，不存在则初始化
            if not self.db_path.exists():
                logger.info("数据库不存在，开始初始化...")
                await self._initialize_database()

            # 测试连接
            await self.test_connection()
            logger.info(f"数据库连接成功: {self.db_path}")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    async def _initialize_database(self):
        """初始化数据库结构"""
        try:
            # 执行数据库初始化脚本
            init_script = self.db_path.parent / "init_database.py"
            if init_script.exists():
                import subprocess
                result = subprocess.run([
                    "python", str(init_script), "--init", "--db-path", str(self.db_path)
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("数据库初始化脚本执行成功")
                else:
                    logger.error(f"数据库初始化脚本执行失败: {result.stderr}")
                    raise Exception(f"数据库初始化失败: {result.stderr}")
            else:
                logger.warning("未找到数据库初始化脚本，使用基本初始化")
                await self._basic_initialize()

        except Exception as e:
            logger.error(f"数据库初始化过程失败: {e}")
            raise

    async def _basic_initialize(self):
        """基本数据库初始化"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        # 创建基本的设备配置表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS device_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id VARCHAR(50) UNIQUE NOT NULL,
                device_name VARCHAR(100) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                communication_type VARCHAR(20) NOT NULL,
                connection_params TEXT,
                status VARCHAR(20) DEFAULT 'inactive',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接（异步上下文管理器）"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 启用字典式访问
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
            finally:
                conn.close()

    async def test_connection(self):
        """测试数据库连接"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result[0] == 1

    # 设备配置操作
    async def get_device_config(self, device_id: str = None) -> List[Dict]:
        """获取设备配置"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            if device_id:
                cursor.execute(
                    "SELECT * FROM device_config WHERE device_id = ?", (device_id,)
                )
                result = cursor.fetchone()
                return [dict(result)] if result else []
            else:
                cursor.execute("SELECT * FROM device_config")
                results = cursor.fetchall()
                return [dict(row) for row in results]

    async def update_device_status(self, device_id: str, status: str):
        """更新设备状态"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE device_config SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE device_id = ?",
                (status, device_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    # 传感器数据操作
    async def insert_sensor_data(self, device_id: str, value: float, data_type: str = None,
                                unit: str = None, raw_data: Dict = None):
        """插入传感器数据"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sensor_data (device_id, value, data_type, unit, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                device_id,
                value,
                data_type,
                unit,
                json.dumps(raw_data) if raw_data else None
            ))
            conn.commit()
            return cursor.lastrowid

    async def get_sensor_data(self, device_id: str = None, limit: int = 100,
                             start_time: str = None, end_time: str = None) -> List[Dict]:
        """获取传感器数据"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM sensor_data WHERE 1=1"
            params = []

            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]

    # 审计日志操作
    async def log_audit(self, user_id: str, action_type: str, target_type: str,
                       target_id: str, action_description: str, result: str = "success",
                       before_state: Dict = None, after_state: Dict = None,
                       error_message: str = None):
        """记录审计日志"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            log_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            cursor.execute('''
                INSERT INTO audit_logs (
                    log_id, user_id, action_type, target_type, target_id,
                    action_description, before_state, after_state, result, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id, user_id, action_type, target_type, target_id,
                action_description,
                json.dumps(before_state) if before_state else None,
                json.dumps(after_state) if after_state else None,
                result, error_message
            ))
            conn.commit()
            return log_id

    async def log_system_event(self, event_type: str, severity: str, source: str,
                              message: str, details: Dict = None):
        """记录系统事件"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            cursor.execute('''
                INSERT INTO system_events (event_id, event_type, severity, source, message, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                event_id, event_type, severity, source, message,
                json.dumps(details) if details else None
            ))
            conn.commit()
            return event_id

    async def log_device_operation(self, device_id: str, operation_type: str,
                                  operation_name: str = None, parameters: Dict = None,
                                  result: str = "success", response_time: int = None,
                                  error_code: str = None, error_message: str = None):
        """记录设备操作日志"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            log_id = f"device_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            cursor.execute('''
                INSERT INTO device_operation_logs (
                    log_id, device_id, operation_type, operation_name, parameters,
                    result, response_time, error_code, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id, device_id, operation_type, operation_name,
                json.dumps(parameters) if parameters else None,
                result, response_time, error_code, error_message
            ))
            conn.commit()
            return log_id

    # MQTT消息日志
    async def log_mqtt_message(self, topic: str, payload: str, direction: str = "publish",
                               qos: int = 0, retained: bool = False, device_id: str = None):
        """记录MQTT消息到数据库"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mqtt_messages (topic, payload, direction, qos, retained, device_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                topic,
                payload,
                direction,
                qos,
                1 if retained else 0,
                device_id
            ))
            conn.commit()
            return cursor.lastrowid

    # 分析方法操作
    async def get_methods(self, method_type: str = None, is_active: bool = True) -> List[Dict]:
        """获取分析方法列表"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM method_storage WHERE 1=1"
            params = []

            if method_type:
                query += " AND method_type = ?"
                params.append(method_type)

            if is_active is not None:
                query += " AND is_active = ?"
                params.append(1 if is_active else 0)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]

    # 数据库统计信息
    async def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # 获取各表的记录数
            tables = ['device_config', 'sensor_data', 'audit_logs', 'system_events', 'method_storage']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                except Exception as e:
                    stats[f"{table}_count"] = f"Error: {e}"

            # 获取数据库大小
            stats['database_size_bytes'] = self.db_path.stat().st_size
            stats['database_size_mb'] = round(stats['database_size_bytes'] / 1024 / 1024, 2)

            # 最新传感器数据时间
            try:
                cursor.execute("SELECT MAX(timestamp) FROM sensor_data")
                result = cursor.fetchone()
                stats['latest_sensor_data'] = result[0] if result[0] else None
            except:
                stats['latest_sensor_data'] = None

            return stats

# 创建全局数据库管理器实例
db_manager = DatabaseManager()

# 便捷函数
async def get_db():
    """获取数据库管理器实例"""
    if not hasattr(db_manager, '_initialized'):
        await db_manager.initialize()
        db_manager._initialized = True
    return db_manager