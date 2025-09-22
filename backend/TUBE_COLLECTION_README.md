# 试管收集积分功能实现文档

## 概述

本功能实现了液相色谱系统中的试管收集积分计算，根据用户选择的方法参数（流速和收集体积）自动计算每根试管的收集时间，并在达到预设时间后自动切换试管。

## 核心功能

### 1. 积分计算
- **公式**: `收集时间(秒) = collection_volume_ml / flow_rate_ml_min * 60`
- **实时监控**: 每100ms检查一次收集状态
- **精确控制**: 确保每根试管收集的体积准确

### 2. 试管切换
- **自动切换**: 收集完成后自动切换到下一个试管（1-40）
- **硬件控制**: 包含停止当前收集、移动位置、开始新收集的完整流程
- **错误处理**: 切换失败时暂停实验并记录错误

### 3. 数据格式
- **存储格式**: `[[start_time, end_time, tube_id], ...]`
- **MQTT推送**: 每次切换试管时推送收集数据
- **缓存管理**: 实时存储在内存中，实验结束后保存到数据库

## 文件结构

### services/tube_manager.py
```python
class TubeCollectionManager:
    """试管收集管理器 - 试管业务逻辑"""

    def is_collection_complete(self, tube_start_time, current_time) -> bool:
        """积分函数 - 检查试管收集是否完成"""

    async def switch_to_tube(self, tube_id: int) -> bool:
        """切换到指定试管 - 硬件操作"""

    def create_tube_data(self, start_time, end_time, tube_id) -> List[float]:
        """创建试管数据 - 格式: [start, end, tube_id]"""
```

### services/experiment_function_manager.py
```python
class ExperimentFunctionManager:
    """实验功能管理器 - 实验业务逻辑"""

    async def _execute_during_experiment_phase(self, experiment_id, progress):
        """实验执行阶段 - 集成试管收集监控"""

    async def _handle_tube_collection_complete(self, experiment_id, progress, current_time):
        """处理试管收集完成 - 切换试管并推送数据"""
```

### models/experiment_function_models.py
```python
class ExperimentProgress(BaseModel):
    """实验进度模型 - 包含试管收集字段"""

    tube_collection_cache: List[List[float]] = []  # [[start, end, tube_id], ...]
    current_tube_id: int = 1
    tube_start_time: float = 0.0
    experiment_start_timestamp: float = 0.0
```

## 使用示例

### 1. 初始化试管收集管理器
```python
flow_rate = 10.0      # ml/min
volume = 2.0          # ml
tube_manager = TubeCollectionManager(flow_rate, volume)

# 计算结果: 每根试管收集时间 = 2.0/10.0*60 = 12秒
```

### 2. 实验流程
```python
# 启动实验时自动初始化试管收集
config = ExperimentConfig(
    experiment_id="exp_001",
    method_id="method_001",  # 包含flow_rate_ml_min和collection_volume_ml
    ...
)
progress = await experiment_manager.start_experiment(config)

# 实验过程中自动执行试管收集循环
while current_tube_id <= 40:
    if tube_manager.is_collection_complete(tube_start_time, current_time):
        # 切换试管
        await tube_manager.switch_to_tube(next_tube_id)
        # MQTT推送数据
        # 更新缓存
```

### 3. 数据示例
```python
# 试管收集缓存示例
tube_collection_cache = [
    [0.0, 12.0, 1],      # 试管1: 0-12秒
    [12.0, 24.0, 2],     # 试管2: 12-24秒
    [24.0, 36.0, 3],     # 试管3: 24-36秒
    # ... 直到试管40
]

# MQTT推送数据示例
{
    "experiment_id": "exp_001",
    "tube_data": [12.0, 24.0, 2],  # [start, end, tube_id]
    "timestamp": "2023-12-15T10:30:25"
}
```

## 配置参数

### 方法参数（从数据库获取）
- `flow_rate_ml_min`: 流速 (ml/min)
- `collection_volume_ml`: 每根试管收集体积 (ml)

### 系统参数
- 试管数量: 40个
- 检查间隔: 100ms
- 切换超时: 200ms（硬件操作）

## 测试验证

### 运行测试
```bash
cd backend
python test_tube_collection.py
```

### 测试内容
1. **基础功能测试**: 初始化、积分计算、试管切换
2. **时间计算测试**: 不同参数组合的收集时间验证
3. **进度计算测试**: 实时进度和剩余时间估算
4. **完整流程测试**: 模拟实验的完整执行过程

### 测试结果
```
试管收集管理器初始化: 流速=10.0ml/min, 收集体积=2.0ml, 每管时间=12.00秒
✓ 积分函数验证通过
✓ 试管切换成功
✓ 数据格式正确
✓ 时间计算准确
```

## 性能特性

### 1. 高精度控制
- 100ms检查间隔确保切换精度
- 时间补偿机制处理暂停/恢复

### 2. 稳定性保障
- 异常处理覆盖所有关键路径
- 硬件操作失败时自动停止实验

### 3. 数据完整性
- 实时缓存确保数据不丢失
- MQTT推送提供实时监控

### 4. 扩展性设计
- 模块化设计便于功能扩展
- 参数化配置支持不同实验需求

## 注意事项

1. **依赖关系**: 需要先初始化MQTT和数据库管理器
2. **参数验证**: 流速和体积必须大于0
3. **错误处理**: 试管切换失败会导致实验停止
4. **时间同步**: 使用系统时间戳确保一致性

## 后续扩展

1. **多通道支持**: 支持并行收集多个样品
2. **智能切换**: 根据检测信号动态调整切换时机
3. **历史分析**: 收集数据的统计分析和优化建议
4. **远程监控**: Web界面实时显示收集状态