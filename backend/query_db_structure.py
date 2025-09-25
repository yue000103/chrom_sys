"""
查询数据库结构的脚本
"""
import sqlite3
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def query_database_structure():
    """查询数据库结构"""
    db_path = 'data/database/chromatography.db'

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tables = [row[0] for row in cursor.fetchall()]

        print('数据库表结构信息')
        print('='*80)
        print(f'数据库文件: {db_path}')
        print(f'总表数: {len(tables)}')
        print()

        # 遍历每个表获取结构
        for table_name in tables:
            print(f'表名: {table_name}')
            print('-'*80)

            # 获取表结构信息
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()

            print(f'{"字段名":<20} | {"数据类型":<15} | {"是否为空":<8} | {"主键":<4} | {"默认值":<15}')
            print('-'*80)

            for col in columns:
                name = col['name']
                col_type = col['type']
                notnull = 'NOT NULL' if col['notnull'] else 'NULL'
                pk = 'PK' if col['pk'] else ''
                default_val = str(col['dflt_value']) if col['dflt_value'] is not None else ''

                print(f'{name:<20} | {col_type:<15} | {notnull:<8} | {pk:<4} | {default_val:<15}')

            # 获取表中记录数
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'记录数: {count}')
            print()

        conn.close()

    except Exception as e:
        print(f'错误: {e}')
        return False

    return True

if __name__ == '__main__':
    query_database_structure()