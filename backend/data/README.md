# 数据库操作工具类使用说明

基于 `D:\back\chromatograph\src\devices\sqllite\SQLiteDB.py` 改进的通用数据库操作类，专为液相色谱仪控制系统设计。

## 文件说明

- `database_utils.py` - 主要的数据库操作类
- `database_examples.py` - 详细的使用示例
- `README.md` - 本说明文档

## 核心特性

### 1. 通用CRUD操作
- ✅ **创建表** - `create_table()`
- ✅ **插入数据** - `insert_data()` (支持单条/批量)
- ✅ **查询数据** - `query_data()` (支持复杂条件)
- ✅ **更新数据** - `update_data()`
- ✅ **删除数据** - `delete_data()`
- ✅ **联表查询** - `query_joined_data()`

### 2. 业务特定操作
- 设备配置管理 - `get_device_config()`, `update_device_status()`
- 传感器数据 - `get_sensor_data()`
- 分析方法管理 - `get_analysis_methods()`
- 实验跟踪 - `get_experiments()`

### 3. 数据库管理工具
- 表结构查询 - `get_table_info()`
- 统计信息 - `get_database_stats()`
- 自定义SQL - `execute_custom_query()`
- 数据库备份 - `backup_database()`

## 快速开始

### 基础使用

```python
from database_utils import ChromatographyDB, get_db_instance

# 获取数据库实例
db = get_db_instance()

# 查询所有设备
devices = db.get_device_config()
print(f"设备数量: {len(devices)}")

# 插入传感器数据
sensor_data = {
    "device_id": "pressure_sensor_1",
    "value": 1.25,
    "data_type": "pressure",
    "unit": "bar"
}
db.insert_data("sensor_data", sensor_data)
```

### 高级查询

```python
# 条件查询
high_pressure = db.query_data(
    "sensor_data",
    where_condition="data_type = ? AND value > ?",
    where_params=("pressure", 1.2),
    order_by="timestamp DESC",
    limit=10
)

# 联表查询
experiment_methods = db.query_joined_data(
    "experiments", "analysis_methods",
    "experiments.method_id = analysis_methods.method_id",
    "experiments.experiment_name, analysis_methods.method_name"
)

# 自定义SQL
stats = db.execute_custom_query("""
    SELECT device_id, COUNT(*) as count, AVG(value) as avg_value
    FROM sensor_data
    GROUP BY device_id
""")
```

## 支持的数据表

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| `device_config` | 设备配置 | device_id, device_name, status |
| `sensor_data` | 传感器数据 | device_id, value, timestamp |
| `experiments` | 实验记录 | experiment_id, method_id, status |
| `analysis_methods` | 分析方法 | method_id, method_name, parameters |
| `chromatography_peaks` | 色谱峰数据 | experiment_id, retention_time, peak_area |
| `system_logs` | 系统日志 | log_level, message, timestamp |
| `mqtt_messages` | MQTT消息 | topic, payload, direction |

## 主要改进

相比原始的 SQLiteDB.py，新版本具有以下改进：

### 1. 更好的错误处理
- 使用上下文管理器确保连接正确关闭
- 自动事务管理，出错时回滚
- 详细的日志记录

### 2. 数据类型支持
- 自动处理JSON数据的序列化/反序列化
- 支持字典式数据访问（sqlite3.Row）
- 类型安全的参数传递

### 3. 业务特定功能
- 针对液相色谱系统优化的查询方法
- 预定义的表名常量
- 常用操作的便捷函数

### 4. 增强的查询功能
- 支持复杂条件查询
- 分页和排序支持
- 联表查询支持多种JOIN类型

### 5. 数据库管理
- 表结构检查
- 统计信息获取
- 数据库备份功能

## 使用建议

### 1. 维护操作
```python
# 获取数据库统计
stats = db.get_database_stats()
print(f"数据库大小: {stats['database_size_mb']} MB")

# 查看表结构
table_info = db.get_table_info("sensor_data")
for col in table_info:
    print(f"{col['name']}: {col['type']}")

# 备份数据库
db.backup_database()
```

### 2. 性能优化
- 使用批量插入减少事务开销
- 为查询条件添加合适的索引
- 定期清理历史数据

### 3. 错误处理
- 总是检查操作返回值
- 使用try-catch处理异常
- 监控日志文件

## 运行示例

```bash
# 测试数据库工具类
cd D:/back/chromatography_system/backend/data
python database_utils.py

# 运行详细示例
python database_examples.py
```

## 注意事项

1. **线程安全**: 数据库连接使用 `check_same_thread=False`，支持多线程访问
2. **事务管理**: 每个操作都会自动提交，出错时回滚
3. **JSON支持**: 自动处理字典和列表的JSON序列化
4. **日志记录**: 使用标准logging模块，可配置日志级别
5. **路径处理**: 使用pathlib确保跨平台兼容性

## 联系信息

如有问题或建议，请联系开发团队。