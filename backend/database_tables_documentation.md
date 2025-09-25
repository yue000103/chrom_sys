# 液相色谱系统数据库表结构文档

## 数据库概览
本文档描述了液相色谱控制系统的SQLite数据库结构，包含各个表的字段定义、数据类型、约束条件和业务用途。

**数据库文件路径：** `D:\back\chromatography_system\backend\data\database\chromatography.db`
**总表数：** 15个表
**数据库类型：** SQLite

---

## 1. 设备配置表 (device_config)

**用途：** 存储系统中各种设备的配置信息和状态
**记录数：** 5条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| device_id | VARCHAR(50) | NOT NULL | - | 设备唯一标识符 |
| device_name | VARCHAR(100) | NOT NULL | - | 设备名称 |
| device_type | VARCHAR(50) | NOT NULL | - | 设备类型(detector/pump_controller/pressure_sensor等) |
| device_model | VARCHAR(100) | NULL | - | 设备型号 |
| communication_type | VARCHAR(20) | NOT NULL | - | 通信方式(serial/i2c/gpio/mqtt等) |
| connection_params | TEXT | NULL | - | 连接参数(JSON格式) |
| status | VARCHAR(20) | NULL | 'inactive' | 设备状态(active/inactive/error/maintenance) |
| is_mock | BOOLEAN | NULL | 0 | 是否为模拟设备 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

---

## 2. 色谱峰数据表 (chromatography_peaks)

**用途：** 存储色谱分析中检测到的峰信息和定量结果
**记录数：** 2条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| experiment_id | VARCHAR(100) | NOT NULL | - | 实验ID，关联experiments表 |
| peak_number | INTEGER | NULL | - | 峰编号 |
| retention_time | REAL | NULL | - | 保留时间(min) |
| peak_area | REAL | NULL | - | 峰面积 |
| peak_height | REAL | NULL | - | 峰高 |
| peak_width | REAL | NULL | - | 峰宽(min) |
| peak_symmetry | REAL | NULL | - | 峰对称性 |
| resolution | REAL | NULL | - | 分离度 |
| theoretical_plates | INTEGER | NULL | - | 理论塔板数 |
| compound_name | VARCHAR(200) | NULL | - | 化合物名称 |
| concentration | REAL | NULL | - | 浓度 |
| unit | VARCHAR(20) | NULL | - | 浓度单位 |
| detector_signals | TEXT | NULL | - | 检测器信号数据(JSON格式) |
| peak_count | INTEGER | NULL | - | 峰数量 |

---

## 3. 系统日志表 (system_logs)

**用途：** 记录系统运行过程中的各种日志信息
**记录数：** 0条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| timestamp | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 日志时间戳 |
| log_level | VARCHAR(20) | NULL | - | 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| module | VARCHAR(100) | NULL | - | 产生日志的模块名称 |
| message | TEXT | NULL | - | 日志消息内容 |
| user | VARCHAR(100) | NULL | - | 相关用户 |
| device_id | VARCHAR(50) | NULL | - | 相关设备ID |
| experiment_id | VARCHAR(100) | NULL | - | 相关实验ID |
| error_code | VARCHAR(50) | NULL | - | 错误代码 |
| stack_trace | TEXT | NULL | - | 错误堆栈信息 |

---

## 4. MQTT消息历史表 (mqtt_messages)

**用途：** 记录系统中所有MQTT消息的收发历史
**记录数：** 7,768条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| timestamp | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 消息时间戳 |
| topic | VARCHAR(200) | NOT NULL | - | MQTT主题 |
| payload | TEXT | NULL | - | 消息内容 |
| qos | INTEGER | NULL | 0 | 服务质量等级(0/1/2) |
| retained | BOOLEAN | NULL | 0 | 是否为保留消息 |
| direction | VARCHAR(10) | NULL | - | 消息方向(publish/subscribe) |
| device_id | VARCHAR(50) | NULL | - | 相关设备ID |
| processed | BOOLEAN | NULL | 0 | 是否已处理 |
| batch_id | VARCHAR(50) | NULL | - | 批处理ID |
| batch_timestamp | TIMESTAMP | NULL | - | 批处理时间戳 |

---

## 5. 数据质量指标表 (data_quality_metrics)

**用途：** 存储实验数据的质量评估指标
**记录数：** 0条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| experiment_id | VARCHAR(100) | NOT NULL | - | 实验ID，关联experiments表 |
| timestamp | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 评估时间 |
| signal_to_noise_ratio | REAL | NULL | - | 信噪比 |
| baseline_drift | REAL | NULL | - | 基线漂移 |
| peak_symmetry | REAL | NULL | - | 峰对称性 |
| retention_time_reproducibility | REAL | NULL | - | 保留时间重现性 |
| detector_linearity | REAL | NULL | - | 检测器线性度 |
| data_completeness_percentage | REAL | NULL | - | 数据完整性百分比 |
| quality_score | REAL | NULL | - | 综合质量得分 |
| notes | TEXT | NULL | - | 质量评估备注 |

---

## 6. 传感器数据表 (sensor_data)

**用途：** 存储各种传感器的实时数据和历史数据
**记录数：** 2,006条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY | - | 自增主键 |
| timestamp | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 数据时间戳 |
| data_type | VARCHAR(20) | NULL | - | 数据类型(pressure/flow/absorbance等) |
| value | REAL | NOT NULL | - | 传感器数值 |
| unit | VARCHAR(20) | NULL | - | 数值单位 |
| quality_flag | INTEGER | NULL | 1 | 数据质量标志(1=正常, 0=异常) |

---

## 7. 色谱柱信息表 (column_info)

**用途：** 管理色谱柱的规格参数和使用信息
**记录数：** 3条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| column_id | INTEGER | PRIMARY KEY | - | 色谱柱ID |
| column_code | TEXT | NOT NULL | - | 色谱柱编码 |
| specification_g | INTEGER | NULL | - | 规格(g) |
| max_pressure_bar | INTEGER | NULL | - | 最大承压(bar) |
| flow_rate_ml_min | REAL | NULL | - | 推荐流速(ml/min) |
| column_volume_cv_ml | REAL | NULL | - | 柱体积(ml) |
| sample_load_amount | TEXT | NULL | - | 样品载量描述 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |

---

## 8. 试管操作记录表 (tube_operations)

**用途：** 记录自动进样器对试管执行的各种操作
**记录数：** 6条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| operation_id | INTEGER | PRIMARY KEY | - | 操作ID |
| tube_id | TEXT | NOT NULL | - | 试管ID |
| operation_type | TEXT | NOT NULL | - | 操作类型(pickup/inject/wash/move) |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |

---

## 9. SMILES分子管理表 (smiles_management)

**用途：** 存储分子的SMILES表示法和相关化学信息
**记录数：** 4条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| smiles_id | INTEGER | PRIMARY KEY | - | SMILES记录ID |
| smiles_description | TEXT | NOT NULL | - | SMILES描述 |
| smiles_string | TEXT | NULL | - | SMILES字符串 |
| molecular_formula | TEXT | NULL | - | 分子式 |
| molecular_weight | REAL | NULL | - | 分子量 |
| compound_name | VARCHAR(200) | NULL | - | 化合物名称 |
| cas_number | VARCHAR(50) | NULL | - | CAS登记号 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

---

## 10. 试管阀路径表 (tube_valve_path)

**用途：** 记录试管进样时的阀门切换路径配置
**记录数：** 20条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| path_id | INTEGER | PRIMARY KEY | - | 路径ID |
| module_number | INTEGER | NOT NULL | - | 模块编号 |
| tube_number | INTEGER | NOT NULL | - | 试管编号 |
| sequence_order | INTEGER | NOT NULL | - | 执行顺序 |
| device_code | VARCHAR(50) | NOT NULL | - | 设备代码 |
| device_type | VARCHAR(30) | NOT NULL | - | 设备类型 |
| action_type | VARCHAR(30) | NOT NULL | - | 动作类型 |
| target_position | INTEGER | NULL | - | 目标位置 |
| description | VARCHAR(200) | NULL | - | 操作描述 |
| is_required | BOOLEAN | NULL | 1 | 是否必须执行 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

---

## 11. 设备映射表 (device_mapping)

**用途：** 管理设备的逻辑映射和物理地址对应关系
**记录数：** 19条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| mapping_id | INTEGER | PRIMARY KEY | - | 映射ID |
| device_code | VARCHAR(50) | NOT NULL | - | 设备代码 |
| controller_type | VARCHAR(50) | NOT NULL | - | 控制器类型 |
| physical_id | VARCHAR(50) | NOT NULL | - | 物理ID/地址 |
| controller_instance | VARCHAR(50) | NULL | - | 控制器实例 |
| device_description | VARCHAR(200) | NULL | - | 设备描述 |
| is_active | BOOLEAN | NULL | 1 | 是否启用 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

---

## 12. 试管架信息表 (rack_info)

**用途：** 管理试管架的配置和位置信息
**记录数：** 4条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| rack_id | INTEGER | PRIMARY KEY | - | 试管架ID |
| tube_volume_ml | REAL | NOT NULL | - | 试管体积(ml) |
| tube_count | INTEGER | NOT NULL | - | 试管数量 |
| rack_name | VARCHAR(100) | NOT NULL | - | 试管架名称 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |
| status | VARCHAR(10) | NULL | "未使用" | 试管架状态 |

---

## 13. 实验历史表 (experiment_history)

**用途：** 记录实验执行过程的详细历史信息
**记录数：** 0条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| history_id | INTEGER | PRIMARY KEY | - | 历史记录ID |
| experiment_id | INTEGER | NOT NULL | - | 实验ID |
| start_time | TIMESTAMP | NULL | - | 开始时间 |
| end_time | TIMESTAMP | NULL | - | 结束时间 |
| elution_curve | TEXT | NULL | - | 洗脱曲线数据(JSON格式) |
| tube_operations | TEXT | NULL | - | 试管操作记录(JSON格式) |
| tube_collection | TEXT | NULL | - | 试管收集记录(JSON格式) |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |

---

## 14. 实验数据表 (experiments)

**用途：** 记录实验的基本信息、参数和执行配置
**记录数：** 6条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| experiment_id | INTEGER | PRIMARY KEY | - | 实验ID |
| experiment_name | VARCHAR(200) | NULL | - | 实验名称 |
| experiment_type | VARCHAR(50) | NULL | - | 实验类型 |
| method_id | VARCHAR(100) | NULL | - | 关联的分析方法ID |
| operator | VARCHAR(100) | NULL | - | 操作员姓名 |
| status | VARCHAR(20) | NULL | - | 实验状态(pending/running/completed/failed) |
| description | TEXT | NULL | - | 实验描述 |
| created_at | TIMESTAMP | NULL | - | 创建时间 |
| experiment_description | TEXT | NULL | - | 详细实验描述 |
| purge_system | BOOLEAN | NULL | - | 是否清洗系统 |
| purge_column | BOOLEAN | NULL | - | 是否清洗色谱柱 |
| purge_column_time_min | INTEGER | NULL | - | 色谱柱清洗时间(分钟) |
| column_balance | BOOLEAN | NULL | - | 是否色谱柱平衡 |
| column_balance_time_min | INTEGER | NULL | - | 色谱柱平衡时间(分钟) |
| is_peak_driven | BOOLEAN | NULL | - | 是否峰驱动模式 |
| collection_volume_ml | REAL | NULL | - | 收集体积(ml) |
| wash_volume_ml | REAL | NULL | - | 清洗体积(ml) |
| wash_cycles | INTEGER | NULL | - | 清洗次数 |
| scheduled_start_time | TIMESTAMP | NULL | - | 计划开始时间 |
| priority | INTEGER | NULL | - | 实验优先级 |
| updated_at | TIMESTAMP | NULL | - | 更新时间 |
| column_conditioning_solution | INTEGER | NULL | - | 色谱柱预处理溶液编号 |

---

## 15. 分析方法表 (methods)

**用途：** 存储完整的液相色谱分析方法配置
**记录数：** 6条

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| method_id | INTEGER | PRIMARY KEY | - | 方法ID |
| method_name | TEXT | NOT NULL | - | 方法名称 |
| column_id | INTEGER | NOT NULL | - | 关联色谱柱ID |
| flow_rate_ml_min | INTEGER | NOT NULL | - | 流速(ml/min) |
| run_time_min | INTEGER | NOT NULL | - | 运行时间(min) |
| detector_wavelength | TEXT | NOT NULL | - | 检测波长(nm) |
| peak_driven | BLOB | NULL | 0 | 是否峰驱动模式 |
| gradient_elution_mode | TEXT | NOT NULL | - | 梯度洗脱模式(manual/auto) |
| gradient_time_table | TEXT | NULL | - | 梯度时间表(JSON格式) |
| auto_gradient_params | TEXT | NULL | - | 自动梯度参数(JSON格式) |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |
| smiles_id | INTEGER | NULL | - | 关联SMILES分子ID |

---

## 数据库关系图

### 主要外键关系：
```
experiments (experiment_id) → chromatography_peaks (experiment_id)
experiments (experiment_id) → data_quality_metrics (experiment_id)
experiments (experiment_id) → experiment_history (experiment_id)
column_info (column_id) → methods (column_id)
smiles_management (smiles_id) → methods (smiles_id)
```

### 表数据统计：
- **mqtt_messages**: 7,768条记录（活跃度最高）
- **sensor_data**: 2,006条记录
- **tube_valve_path**: 20条配置记录
- **device_mapping**: 19条映射记录
- **experiments**: 6条实验记录
- **methods**: 6条方法记录
- **tube_operations**: 6条操作记录
- **device_config**: 5条设备配置
- **smiles_management**: 4条分子记录
- **rack_info**: 4条试管架信息
- **column_info**: 3条色谱柱信息
- **chromatography_peaks**: 2条峰数据
- **system_logs**: 0条日志记录
- **data_quality_metrics**: 0条质量数据
- **experiment_history**: 0条历史记录

---

**文档生成时间：** 2025-09-25
**数据库文件：** chromatography.db
**数据库引擎：** SQLite
**系统：** 液相色谱仪控制系统