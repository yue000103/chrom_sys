"""
通用数据库操作工具类
Universal Database Operations Utility Class

基于SQLiteDB.py改进，提供更完善的增删改查功能
支持液相色谱仪控制系统的所有数据表操作
"""

import sqlite3
import logging
import os
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("DatabaseUtils")


class ChromatographyDB:
    """
    液相色谱系统数据库操作类
    Universal Database Operations for Chromatography System
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 使用默认数据库路径
            base_dir = Path(__file__).parent
            self.db_path = base_dir / "database" / "chromatography.db"
        else:
            self.db_path = Path(db_path)

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 数据库表名常量
        self.TABLES = {
            'device_config': 'device_config',
            'sensor_data': 'sensor_data',
            'experiments': 'experiments',
            'analysis_methods': 'analysis_methods',
            'chromatography_peaks': 'chromatography_peaks',
            'system_logs': 'system_logs',
            'calibration_data': 'calibration_data',
            'tube_info': 'tube_info',
            'mqtt_messages': 'mqtt_messages',
            'data_quality_metrics': 'data_quality_metrics'
        }

        logger.info(f"数据库初始化: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接上下文管理器

        Yields:
            sqlite3.Cursor: 数据库游标对象
        """
        connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row  # 启用字典式访问
        cursor = connection.cursor()
        try:
            yield cursor
        except Exception as e:
            connection.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        else:
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    # ============= 基础CRUD操作 =============

    def create_table(self, table_name: str, columns: str) -> bool:
        """
        创建数据表

        Args:
            table_name: 表名
            columns: 列定义，如 "id INTEGER PRIMARY KEY, name TEXT NOT NULL"

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.get_connection() as cursor:
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
                cursor.execute(create_sql)
                logger.info(f"表创建成功: {table_name}")
                return True
        except Exception as e:
            logger.error(f"创建表失败 {table_name}: {e}")
            return False

    def drop_table(self, table_name: str) -> bool:
        """
        删除数据表

        Args:
            table_name: 表名

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.get_connection() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(f"表删除成功: {table_name}")
                return True
        except Exception as e:
            logger.error(f"删除表失败 {table_name}: {e}")
            return False

    def insert_data(self, table_name: str, data: Union[Dict, List[Dict]],
                   columns: Optional[List[str]] = None) -> bool:
        """
        插入数据（支持单条或批量）

        Args:
            table_name: 表名
            data: 数据字典或字典列表
            columns: 指定列名列表（可选，自动从data推断）

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.get_connection() as cursor:
                # 处理单条数据
                if isinstance(data, dict):
                    data = [data]

                if not data:
                    logger.warning("没有数据要插入")
                    return False

                # 获取列名
                if columns is None:
                    columns = list(data[0].keys())

                # 构建SQL语句
                placeholders = ", ".join(["?"] * len(columns))
                columns_str = ", ".join(columns)
                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                # 准备数据
                values_list = []
                for item in data:
                    values = []
                    for col in columns:
                        value = item.get(col)
                        # 处理JSON数据
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, ensure_ascii=False)
                        values.append(value)
                    values_list.append(tuple(values))

                # 执行插入
                cursor.executemany(sql, values_list)
                logger.info(f"插入数据成功: {table_name}, 记录数: {len(values_list)}")
                return True

        except Exception as e:
            logger.error(f"插入数据失败 {table_name}: {e}")
            return False

    def update_data(self, table_name: str, set_data: Dict[str, Any],
                   where_condition: str, where_params: Tuple = ()) -> int:
        """
        更新数据

        Args:
            table_name: 表名
            set_data: 要更新的字段和值的字典
            where_condition: WHERE条件，如 "id = ? AND status = ?"
            where_params: WHERE条件的参数

        Returns:
            int: 影响的行数
        """
        try:
            with self.get_connection() as cursor:
                # 构建SET子句
                set_clauses = []
                set_values = []
                for key, value in set_data.items():
                    set_clauses.append(f"{key} = ?")
                    # 处理JSON数据
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    set_values.append(value)

                set_clause = ", ".join(set_clauses)

                # 构建完整SQL
                sql = f"UPDATE {table_name} SET {set_clause}"
                params = set_values

                if where_condition:
                    sql += f" WHERE {where_condition}"
                    params.extend(where_params)

                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                logger.info(f"更新数据成功: {table_name}, 影响行数: {affected_rows}")
                return affected_rows

        except Exception as e:
            logger.error(f"更新数据失败 {table_name}: {e}")
            return 0

    def delete_data(self, table_name: str, where_condition: str,
                   where_params: Tuple = ()) -> int:
        """
        删除数据

        Args:
            table_name: 表名
            where_condition: WHERE条件
            where_params: WHERE条件的参数

        Returns:
            int: 删除的行数
        """
        try:
            with self.get_connection() as cursor:
                sql = f"DELETE FROM {table_name} WHERE {where_condition}"
                cursor.execute(sql, where_params)
                deleted_rows = cursor.rowcount
                logger.info(f"删除数据成功: {table_name}, 删除行数: {deleted_rows}")
                return deleted_rows

        except Exception as e:
            logger.error(f"删除数据失败 {table_name}: {e}")
            return 0

    def query_data(self, table_name: str, columns: str = "*",
                  where_condition: Optional[str] = None,
                  where_params: Tuple = (),
                  order_by: Optional[str] = None,
                  limit: Optional[int] = None) -> List[Dict]:
        """
        查询数据

        Args:
            table_name: 表名
            columns: 要查询的列，如 "id, name" 或 "*"
            where_condition: WHERE条件
            where_params: WHERE条件的参数
            order_by: 排序条件，如 "created_at DESC"
            limit: 限制返回的记录数

        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            with self.get_connection() as cursor:
                sql = f"SELECT {columns} FROM {table_name}"
                params = list(where_params)

                if where_condition:
                    sql += f" WHERE {where_condition}"

                if order_by:
                    sql += f" ORDER BY {order_by}"

                if limit:
                    sql += f" LIMIT {limit}"

                cursor.execute(sql, params)
                results = cursor.fetchall()

                # 转换为字典列表
                result_list = []
                for row in results:
                    row_dict = dict(row)
                    # 尝试解析JSON字段
                    for key, value in row_dict.items():
                        if isinstance(value, str) and value.strip().startswith(('{"', '[')):
                            try:
                                row_dict[key] = json.loads(value)
                            except:
                                pass  # 如果不是JSON，保持原值
                    result_list.append(row_dict)

                logger.debug(f"查询数据成功: {table_name}, 返回 {len(result_list)} 条记录")
                return result_list

        except Exception as e:
            logger.error(f"查询数据失败 {table_name}: {e}")
            return []

    def query_joined_data(self, table1: str, table2: str, join_condition: str,
                         columns: str = "*", where_condition: Optional[str] = None,
                         where_params: Tuple = (), join_type: str = "INNER") -> List[Dict]:
        """
        联表查询

        Args:
            table1: 第一个表名
            table2: 第二个表名
            join_condition: 联接条件，如 "table1.id = table2.foreign_id"
            columns: 要查询的列
            where_condition: WHERE条件
            where_params: WHERE条件的参数
            join_type: 联接类型，如 "INNER", "LEFT", "RIGHT"

        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            with self.get_connection() as cursor:
                sql = f"SELECT {columns} FROM {table1} {join_type} JOIN {table2} ON {join_condition}"

                if where_condition:
                    sql += f" WHERE {where_condition}"

                cursor.execute(sql, where_params)
                results = cursor.fetchall()

                result_list = [dict(row) for row in results]
                logger.debug(f"联表查询成功: {table1} JOIN {table2}, 返回 {len(result_list)} 条记录")
                return result_list

        except Exception as e:
            logger.error(f"联表查询失败 {table1} JOIN {table2}: {e}")
            return []

    # ============= 业务特定操作 =============

    def get_device_config(self, device_id: Optional[str] = None) -> List[Dict]:
        """获取设备配置"""
        if device_id:
            return self.query_data(self.TABLES['device_config'],
                                 where_condition="device_id = ?",
                                 where_params=(device_id,))
        return self.query_data(self.TABLES['device_config'])

    def update_device_status(self, device_id: str, status: str) -> bool:
        """更新设备状态"""
        affected = self.update_data(
            self.TABLES['device_config'],
            {"status": status, "updated_at": datetime.now().isoformat()},
            "device_id = ?",
            (device_id,)
        )
        return affected > 0

    def get_analysis_methods(self, method_type: Optional[str] = None,
                           status: str = "active") -> List[Dict]:
        """获取分析方法"""
        conditions = []
        params = []

        if method_type:
            conditions.append("method_type = ?")
            params.append(method_type)

        if status:
            conditions.append("status = ?")
            params.append(status)

        where_condition = " AND ".join(conditions) if conditions else None

        return self.query_data(
            self.TABLES['analysis_methods'],
            where_condition=where_condition,
            where_params=tuple(params),
            order_by="created_at DESC"
        )

    def get_experiments(self, status: Optional[str] = None,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        """获取实验记录"""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if start_date:
            conditions.append("start_time >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("start_time <= ?")
            params.append(end_date)

        where_condition = " AND ".join(conditions) if conditions else None

        return self.query_data(
            self.TABLES['experiments'],
            where_condition=where_condition,
            where_params=tuple(params),
            order_by="start_time DESC"
        )

    def get_sensor_data(self, device_id: Optional[str] = None,
                       start_time: Optional[str] = None,
                       end_time: Optional[str] = None,
                       limit: int = 1000) -> List[Dict]:
        """获取传感器数据"""
        conditions = []
        params = []

        if device_id:
            conditions.append("device_id = ?")
            params.append(device_id)

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        where_condition = " AND ".join(conditions) if conditions else None

        return self.query_data(
            self.TABLES['sensor_data'],
            where_condition=where_condition,
            where_params=tuple(params),
            order_by="timestamp DESC",
            limit=limit
        )

    # ============= 数据库管理工具 =============

    def get_table_info(self, table_name: str) -> List[Dict]:
        """获取表结构信息"""
        try:
            with self.get_connection() as cursor:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                return [dict(col) for col in columns]
        except Exception as e:
            logger.error(f"获取表信息失败 {table_name}: {e}")
            return []

    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        try:
            with self.get_connection() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                return [table['name'] for table in tables]
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []

    def execute_custom_query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """执行自定义SQL查询"""
        try:
            with self.get_connection() as cursor:
                cursor.execute(sql, params)
                if sql.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    return [{"affected_rows": cursor.rowcount}]
        except Exception as e:
            logger.error(f"执行自定义查询失败: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {
            "database_path": str(self.db_path),
            "database_size_mb": round(self.db_path.stat().st_size / 1024 / 1024, 2),
            "tables": {}
        }

        for table in self.get_all_tables():
            if table != 'sqlite_sequence':
                result = self.query_data(table, "COUNT(*) as count")
                stats["tables"][table] = result[0]["count"] if result else 0

        return stats

    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """备份数据库"""
        if backup_path is None:
            backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False


# ============= 便捷函数 =============

def get_db_instance(db_path: Optional[str] = None) -> ChromatographyDB:
    """获取数据库实例"""
    return ChromatographyDB(db_path)


if __name__ == "__main__":
    # 使用示例
    db = ChromatographyDB()

    # 获取数据库统计信息
    stats = db.get_database_stats()
    print("数据库统计信息:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    # 获取所有设备配置
    devices = db.get_device_config()
    print(f"\n设备配置数量: {len(devices)}")

    # 获取分析方法
    methods = db.get_analysis_methods()
    print(f"分析方法数量: {len(methods)}")