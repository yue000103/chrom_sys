"""
数据库操作示例代码
Database Operations Examples

演示如何使用ChromatographyDB类进行各种数据库操作
"""

from database_utils import ChromatographyDB, get_db_instance
from datetime import datetime
import json


def basic_crud_examples():
    """基础增删改查操作示例"""
    print("=== 基础CRUD操作示例 ===")

    # 获取数据库实例
    db = get_db_instance()

    # 1. 插入设备配置
    print("\n1. 插入设备配置:")
    device_data = {
        "device_id": "test_device_001",
        "device_name": "测试设备1",
        "device_type": "detector",
        "device_model": "UV-2000",
        "communication_type": "serial",
        "connection_params": json.dumps({"port": "COM3", "baudrate": 9600}),
        "status": "active",
        "is_mock": 1
    }

    success = db.insert_data("device_config", device_data)
    print(f"插入结果: {success}")

    # 2. 查询设备配置
    print("\n2. 查询设备配置:")
    devices = db.get_device_config("test_device_001")
    print(f"查询结果: {json.dumps(devices, ensure_ascii=False, indent=2)}")

    # 3. 更新设备状态
    print("\n3. 更新设备状态:")
    success = db.update_device_status("test_device_001", "inactive")
    print(f"更新结果: {success}")

    # 4. 查询更新后的设备
    devices = db.get_device_config("test_device_001")
    print(f"更新后状态: {devices[0]['status'] if devices else 'Not found'}")

    # 5. 删除测试设备
    print("\n5. 删除测试设备:")
    deleted = db.delete_data("device_config", "device_id = ?", ("test_device_001",))
    print(f"删除行数: {deleted}")


def sensor_data_examples():
    """传感器数据操作示例"""
    print("\n=== 传感器数据操作示例 ===")

    db = get_db_instance()

    # 1. 批量插入传感器数据
    print("\n1. 批量插入传感器数据:")
    sensor_data_list = [
        {
            "device_id": "pressure_sensor_1",
            "value": 1.25,
            "data_type": "pressure",
            "unit": "bar",
            "raw_data": json.dumps({"raw_value": 1250, "calibrated": True})
        },
        {
            "device_id": "pressure_sensor_1",
            "value": 1.28,
            "data_type": "pressure",
            "unit": "bar",
            "raw_data": json.dumps({"raw_value": 1280, "calibrated": True})
        },
        {
            "device_id": "detector_1",
            "value": 0.156,
            "data_type": "absorbance",
            "unit": "AU",
            "raw_data": json.dumps({"wavelength": 254, "bandwidth": 4})
        }
    ]

    success = db.insert_data("sensor_data", sensor_data_list)
    print(f"批量插入结果: {success}")

    # 2. 查询特定设备的传感器数据
    print("\n2. 查询压力传感器数据:")
    pressure_data = db.get_sensor_data(device_id="pressure_sensor_1", limit=10)
    print(f"压力传感器数据量: {len(pressure_data)}")
    if pressure_data:
        print(f"最新数据: {json.dumps(pressure_data[0], ensure_ascii=False, indent=2)}")

    # 3. 查询时间范围内的数据
    print("\n3. 查询最近的传感器数据:")
    recent_data = db.get_sensor_data(limit=5)
    print(f"最近5条数据:")
    for i, data in enumerate(recent_data):
        print(f"  {i+1}. {data['device_id']}: {data['value']} {data['unit']} ({data['timestamp']})")


def method_management_examples():
    """分析方法管理示例"""
    print("\n=== 分析方法管理示例 ===")

    db = get_db_instance()

    # 1. 创建新的分析方法
    print("\n1. 创建新的分析方法:")
    method_data = {
        "method_id": "method_test_001",
        "method_name": "测试方法-咖啡因分析",
        "method_type": "analytical",
        "parameters": json.dumps({
            "mobile_phase_A": "水",
            "mobile_phase_B": "甲醇",
            "gradient": [
                {"time": 0, "B_percent": 5},
                {"time": 5, "B_percent": 30},
                {"time": 15, "B_percent": 80},
                {"time": 20, "B_percent": 5}
            ]
        }),
        "flow_rate": 1.0,
        "column_temperature": 30.0,
        "injection_volume": 20.0,
        "detection_wavelength": 254.0,
        "run_time": 25.0,
        "status": "active",
        "created_by": "admin"
    }

    success = db.insert_data("analysis_methods", method_data)
    print(f"方法创建结果: {success}")

    # 2. 查询分析方法
    print("\n2. 查询分析方法:")
    methods = db.get_analysis_methods(method_type="analytical")
    print(f"分析型方法数量: {len(methods)}")
    for method in methods:
        print(f"  - {method['method_id']}: {method['method_name']}")

    # 3. 更新方法状态
    print("\n3. 更新方法状态:")
    affected = db.update_data(
        "analysis_methods",
        {"status": "under_review", "updated_at": datetime.now().isoformat()},
        "method_id = ?",
        ("method_test_001",)
    )
    print(f"更新影响行数: {affected}")


def experiment_tracking_examples():
    """实验跟踪示例"""
    print("\n=== 实验跟踪示例 ===")

    db = get_db_instance()

    # 1. 创建实验记录
    print("\n1. 创建实验记录:")
    experiment_data = {
        "experiment_id": "exp_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "experiment_name": "咖啡因含量测试-样品001",
        "experiment_type": "quantitative",
        "method_id": "method_test_001",
        "operator": "张三",
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "description": "测试样品中咖啡因含量分析",
        "parameters": json.dumps({
            "sample_volume": 1.0,
            "dilution_factor": 1,
            "expected_concentration": "50-100 mg/L"
        })
    }

    success = db.insert_data("experiments", experiment_data)
    print(f"实验创建结果: {success}")

    # 2. 查询运行中的实验
    print("\n2. 查询运行中的实验:")
    running_experiments = db.get_experiments(status="running")
    print(f"运行中实验数量: {len(running_experiments)}")

    # 3. 更新实验状态为完成
    if running_experiments:
        exp_id = running_experiments[0]["experiment_id"]
        print(f"\n3. 完成实验: {exp_id}")

        affected = db.update_data(
            "experiments",
            {
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "results": json.dumps({
                    "peak_area": 125643,
                    "retention_time": 8.52,
                    "concentration": 78.5,
                    "unit": "mg/L"
                })
            },
            "experiment_id = ?",
            (exp_id,)
        )
        print(f"更新结果: {affected}")


def advanced_query_examples():
    """高级查询示例"""
    print("\n=== 高级查询示例 ===")

    db = get_db_instance()

    # 1. 联表查询：实验和方法信息
    print("\n1. 联表查询 - 实验和方法:")
    joined_data = db.query_joined_data(
        "experiments", "analysis_methods",
        "experiments.method_id = analysis_methods.method_id",
        "experiments.experiment_id, experiments.experiment_name, analysis_methods.method_name, experiments.status",
        where_condition="experiments.status IN ('completed', 'running')"
    )

    print(f"联表查询结果: {len(joined_data)} 条记录")
    for record in joined_data[:3]:  # 显示前3条
        print(f"  实验: {record.get('experiment_name')} | 方法: {record.get('method_name')} | 状态: {record.get('status')}")

    # 2. 自定义SQL查询
    print("\n2. 自定义SQL查询 - 设备使用统计:")
    device_stats = db.execute_custom_query("""
        SELECT device_id, COUNT(*) as data_count,
               AVG(value) as avg_value,
               MIN(timestamp) as first_record,
               MAX(timestamp) as last_record
        FROM sensor_data
        GROUP BY device_id
        ORDER BY data_count DESC
    """)

    print("设备数据统计:")
    for stat in device_stats:
        print(f"  {stat['device_id']}: {stat['data_count']}条数据, 平均值: {stat.get('avg_value', 0):.2f}")

    # 3. 复杂条件查询
    print("\n3. 复杂条件查询 - 近期高压力数据:")
    high_pressure_data = db.query_data(
        "sensor_data",
        columns="device_id, value, timestamp",
        where_condition="data_type = ? AND value > ? AND timestamp > datetime('now', '-1 day')",
        where_params=("pressure", 1.2),
        order_by="value DESC",
        limit=5
    )

    print(f"高压力数据: {len(high_pressure_data)} 条记录")
    for data in high_pressure_data:
        print(f"  {data['device_id']}: {data['value']} bar at {data['timestamp']}")


def database_management_examples():
    """数据库管理示例"""
    print("\n=== 数据库管理示例 ===")

    db = get_db_instance()

    # 1. 获取数据库统计信息
    print("\n1. 数据库统计信息:")
    stats = db.get_database_stats()
    print(f"数据库路径: {stats['database_path']}")
    print(f"数据库大小: {stats['database_size_mb']} MB")
    print("表记录统计:")
    for table, count in stats['tables'].items():
        print(f"  {table}: {count} 条记录")

    # 2. 获取表结构信息
    print("\n2. 获取表结构 - sensor_data:")
    table_info = db.get_table_info("sensor_data")
    print("字段信息:")
    for col in table_info:
        print(f"  {col['name']}: {col['type']} {'(主键)' if col['pk'] else ''}")

    # 3. 获取所有表名
    print("\n3. 所有数据表:")
    tables = db.get_all_tables()
    print(f"表列表: {', '.join(tables)}")


def cleanup_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    db = get_db_instance()

    # 删除测试方法
    deleted_methods = db.delete_data("analysis_methods", "method_id LIKE ?", ("method_test_%",))
    print(f"删除测试方法: {deleted_methods} 条")

    # 删除测试实验
    deleted_experiments = db.delete_data("experiments", "experiment_id LIKE ?", ("exp_%",))
    print(f"删除测试实验: {deleted_experiments} 条")

    print("测试数据清理完成!")


if __name__ == "__main__":
    print("液相色谱数据库操作示例")
    print("=" * 50)

    try:
        # 运行各种示例
        basic_crud_examples()
        sensor_data_examples()
        method_management_examples()
        experiment_tracking_examples()
        advanced_query_examples()
        database_management_examples()

        # 清理测试数据
        cleanup_test_data()

    except Exception as e:
        print(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n示例演示完成!")