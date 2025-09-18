"""
检查数据库中的传感器数据和MQTT消息
"""
import sqlite3
from pathlib import Path
import json
from datetime import datetime

# 数据库路径
db_path = Path(__file__).parent / "data" / "database" / "chromatography.db"

print(f"数据库路径: {db_path}")
print("=" * 60)

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 检查传感器数据表
print("1. 传感器数据 (sensor_data):")
print("-" * 40)
cursor.execute("SELECT COUNT(*) FROM sensor_data")
count = cursor.fetchone()[0]
print(f"总记录数: {count}")

if count > 0:
    # 获取最新的10条记录
    cursor.execute("""
        SELECT * FROM sensor_data
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    records = cursor.fetchall()

    print("\n最新10条记录:")
    for record in records:
        print(f"  设备: {record['device_id']}, 类型: {record['data_type']}, "
              f"值: {record['value']:.2f}, 时间: {record['timestamp']}")

    # 统计每个设备的数据量
    cursor.execute("""
        SELECT device_id, COUNT(*) as count,
               MIN(value) as min_val, MAX(value) as max_val, AVG(value) as avg_val
        FROM sensor_data
        GROUP BY device_id
    """)
    device_stats = cursor.fetchall()

    print("\n设备数据统计:")
    for stat in device_stats:
        print(f"  {stat['device_id']}: {stat['count']}条记录, "
              f"范围: {stat['min_val']:.2f}-{stat['max_val']:.2f}, "
              f"平均值: {stat['avg_val']:.2f}")

# 2. 检查MQTT消息表
print("\n2. MQTT消息记录 (mqtt_messages):")
print("-" * 40)
cursor.execute("SELECT COUNT(*) FROM mqtt_messages")
count = cursor.fetchone()[0]
print(f"总记录数: {count}")

if count > 0:
    # 获取最新的5条记录
    cursor.execute("""
        SELECT * FROM mqtt_messages
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    records = cursor.fetchall()

    print("\n最新5条消息:")
    for record in records:
        payload_preview = record['payload'][:50] + "..." if len(record['payload']) > 50 else record['payload']
        print(f"  主题: {record['topic']}, 方向: {record['direction']}, "
              f"时间: {record['timestamp']}")
        print(f"    数据: {payload_preview}")

    # 统计每个主题的消息量
    cursor.execute("""
        SELECT topic, COUNT(*) as count
        FROM mqtt_messages
        GROUP BY topic
        ORDER BY count DESC
        LIMIT 10
    """)
    topic_stats = cursor.fetchall()

    print("\n主题消息统计 (Top 10):")
    for stat in topic_stats:
        print(f"  {stat['topic']}: {stat['count']}条消息")

# 3. 检查设备配置表
print("\n3. 设备配置 (device_config):")
print("-" * 40)
cursor.execute("SELECT * FROM device_config")
devices = cursor.fetchall()

print(f"已配置设备数: {len(devices)}")
for device in devices:
    print(f"  {device['device_id']}: {device['device_name']} ({device['device_type']}) "
          f"- 状态: {device['status']}, Mock: {device['is_mock']}")

# 4. 数据库大小
db_size = db_path.stat().st_size / 1024
print(f"\n数据库文件大小: {db_size:.2f} KB")

conn.close()
print("=" * 60)
print("检查完成!")