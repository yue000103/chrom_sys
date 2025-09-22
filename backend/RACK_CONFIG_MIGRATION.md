# 架子配置迁移文档

## 概述

成功将架子（试管架）的默认配置从 `ExperimentFunctionManager` 类中迁移到独立的配置文件 `config/rack_config.py` 中，实现了配置的集中管理和多类共享。

## 迁移内容

### 📁 新增文件

**config/rack_config.py** - 架子配置核心文件
- `RackConfig` 类：集中管理所有架子相关配置
- 模块级别函数：提供便捷的访问接口
- 数据验证和默认值处理

### 🔧 修改文件

**services/experiment_function_manager.py**
- 移除了类内部的配置常量
- 导入并使用 `RackConfig` 配置类
- 简化了 `_get_current_rack_info()` 方法

## 配置详情

### 🎯 默认配置值

```python
# 位置: config/rack_config.py
DEFAULT_RACK_ID = 'rack_001'          # 默认试管架ID
DEFAULT_TUBE_COUNT = 40               # 默认试管数量
DEFAULT_TUBE_VOLUME_ML = 2.0         # 默认试管体积(ml)
DEFAULT_RACK_TYPE = 'standard'       # 默认架子类型
DEFAULT_RACK_STATUS = 'active'       # 默认架子状态
```

### 🔍 支持的枚举值

**架子类型**:
- `standard`: 标准试管架
- `micro`: 微量试管架
- `large`: 大容量试管架
- `custom`: 自定义试管架

**架子状态**:
- `active`: 活跃
- `inactive`: 非活跃
- `maintenance`: 维护中
- `disabled`: 已禁用

## 使用方式

### 1. 基础用法

```python
from config.rack_config import RackConfig

# 获取默认值
rack_id = RackConfig.DEFAULT_RACK_ID
tube_count = RackConfig.DEFAULT_TUBE_COUNT

# 获取完整默认配置
default_info = RackConfig.get_default_rack_info()
```

### 2. 便捷函数

```python
from config.rack_config import get_default_rack_id, validate_rack_info

# 获取默认架子ID
rack_id = get_default_rack_id()

# 验证架子信息
user_input = {'rack_id': 'test', 'tube_count': 20}
validated = validate_rack_info(user_input)
```

### 3. 数据验证和补全

```python
# 不完整的数据
incomplete_data = {
    'rack_id': 'test_rack',
    'tube_count': 48
    # 缺少其他字段
}

# 自动补全默认值
complete_data = RackConfig.validate_rack_info(incomplete_data)
# 结果: 包含所有必需字段，缺失字段使用默认值
```

### 4. 创建自定义配置

```python
# 创建自定义架子配置
custom_rack = RackConfig.create_rack_info(
    rack_id="custom_001",
    tube_count=60,
    tube_volume_ml=1.5,
    rack_type="large",
    description="大容量自定义架子"
)
```

## 在不同类中的使用示例

### 试管管理器 (TubeManager)

```python
from config.rack_config import RackConfig

class TubeManager:
    def __init__(self):
        self.default_rack_id = RackConfig.DEFAULT_RACK_ID
        self.default_tube_count = RackConfig.DEFAULT_TUBE_COUNT

    def get_max_tubes(self):
        return self.default_tube_count
```

### 硬件控制器 (HardwareController)

```python
from config.rack_config import RackConfig

class HardwareController:
    def __init__(self):
        self.rack_info = RackConfig.get_default_rack_info()

    def move_to_position(self, tube_id: int):
        max_tubes = self.rack_info['tube_count']
        if tube_id > max_tubes:
            raise ValueError(f"超出架子容量: {max_tubes}")
```

### API控制器 (APIController)

```python
from config.rack_config import RackConfig, validate_rack_info

class APIController:
    def get_rack_config(self):
        return {
            'default_config': RackConfig.get_default_rack_info(),
            'supported_types': RackConfig.SUPPORTED_RACK_TYPES
        }

    def update_rack_config(self, user_input):
        validated = validate_rack_info(user_input)
        # 保存到数据库...
        return validated
```

## 优势

### ✅ 集中管理
- 所有架子配置都在一个文件中
- 修改配置只需要在一个地方进行
- 避免了重复的常量定义

### ✅ 类型安全
- 完整的数据验证机制
- 自动类型检查和转换
- 枚举值验证

### ✅ 易于扩展
- 支持新的架子类型和状态
- 可以轻松添加新的配置项
- 向后兼容的设计

### ✅ 多类共享
- 任何类都可以导入和使用配置
- 统一的访问接口
- 减少代码重复

### ✅ 健壮性
- 完善的默认值处理
- 异常情况的回退机制
- 数据完整性保证

## 测试验证

### 🧪 测试覆盖

1. **配置类功能测试**: 默认值、创建、验证
2. **集成测试**: ExperimentFunctionManager 使用新配置
3. **异常处理测试**: 数据库异常、无效数据
4. **多类访问测试**: 不同类使用相同配置

### ✅ 测试结果

所有测试通过，包括：
- ✅ 默认配置正确加载
- ✅ 数据验证和补全功能正常
- ✅ 异常情况正确处理
- ✅ 多类可以正常访问配置
- ✅ 向后兼容性保持

## 配置修改指南

### 修改默认架子

```python
# 在 config/rack_config.py 中修改
DEFAULT_RACK_ID = 'rack_002'  # 改为其他架子
```

### 添加新的架子类型

```python
# 在 SUPPORTED_RACK_TYPES 中添加
SUPPORTED_RACK_TYPES = {
    'standard': '标准试管架',
    'micro': '微量试管架',
    'large': '大容量试管架',
    'custom': '自定义试管架',
    'ultra_micro': '超微量试管架'  # 新增类型
}
```

### 修改默认试管数量

```python
# 在 config/rack_config.py 中修改
DEFAULT_TUBE_COUNT = 96  # 改为96孔
DEFAULT_TUBE_VOLUME_ML = 1.5  # 对应调整体积
```

## 后续建议

1. **配置文件化**: 可以进一步将配置移到 JSON/YAML 文件中
2. **环境变量支持**: 支持通过环境变量覆盖默认配置
3. **配置热更新**: 实现运行时配置更新功能
4. **配置验证CLI**: 创建命令行工具验证配置文件

## 总结

架子配置成功从类内部迁移到独立配置文件，实现了：
- 🎯 **集中管理**: 所有架子配置在一处管理
- 🔄 **多类共享**: 任何类都可以使用相同配置
- 🛡️ **数据安全**: 完整的验证和默认值机制
- 📈 **易于维护**: 配置修改和扩展更加便捷

配置系统现在更加模块化、可维护和可扩展！