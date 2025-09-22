# MQTT预处理状态实施方案

## ✅ 已完成的修改

### 1. MQTT集成
- ✅ 导入并使用现有的`mqtt-service.js`
- ✅ 在组件挂载时自动连接MQTT
- ✅ 订阅`system/preprocessing_status`主题
- ✅ 在组件卸载时断开MQTT连接

### 2. 状态管理重构
**移除的状态变量:**
- `totalPretreatmentSteps` (不再需要计算总步骤数)
- `remainingStepTime` (不再使用前端计时器)
- `stepProgress` (不再显示进度条)
- `stepTimer` (移除前端计时器)
- `currentStepDuration` (不再需要)
- `currentStepStartTime` (不再需要)

**新增的状态变量:**
- `preprocessingStatus`: 当前步骤的状态 ('started'/'completed')
- `mqttConnected`: MQTT连接状态
- `currentPretreatmentStep`: 当前步骤名称 (string类型，而非数字)

### 3. MQTT消息处理

**订阅的消息格式:**
```javascript
{
    "action": "preprocessing_sequence|purge_column|purge_system|column_equilibration",
    "experiment_id": 实验ID,
    "status": "started|completed",
    "timestamp": "时间戳"
}
```

**支持的消息序列:**
1. `preprocessing_sequence` - started (整体开始)
2. `purge_column` - started/completed (吹扫柱子)
3. `purge_system` - started/completed (吹扫系统)
4. `column_equilibration` - started/completed (柱平衡)
5. `preprocessing_sequence` - completed (整体完成)

### 4. API集成

**新增的后端API调用:**
- `POST /api/experiment-control/start/{experimentId}` - 开始实验
- `POST /api/experiment-control/pause/{experimentId}` - 暂停实验
- `POST /api/experiment-control/resume/{experimentId}` - 继续实验
- `POST /api/experiment-control/terminate/{experimentId}` - 终止实验

### 5. 界面优化

**新的预处理显示:**
- ✅ MQTT连接状态指示器
- ✅ 当前步骤标题和描述显示
- ✅ 旋转图标显示正在运行的步骤
- ✅ 对号图标显示已完成的步骤
- ✅ 预处理步骤清单，实时高亮当前步骤
- ✅ 移除了进度条和倒计时（改为"正在运行"状态显示）

**控制按钮调整:**
- ❌ 移除了"下一步"按钮（步骤由MQTT消息自动推进）
- ✅ 保留暂停/继续按钮（通过后端API）
- ✅ 保留终止按钮（通过后端API）
- ✅ 保留跳转实时监控按钮

## 🔧 实施要点

### 1. 消息验证
- 检查实验ID匹配，只处理当前实验的消息
- 忽略不相关实验的预处理消息

### 2. 状态持久化
- 将MQTT接收的状态保存到localStorage
- 页面刷新或导航后能正确恢复状态

### 3. 错误处理
- MQTT连接失败时显示警告状态
- API调用失败时回滚界面状态
- 损坏的localStorage数据自动清理

### 4. 用户体验
- 实时消息提示（ElMessage）显示步骤进展
- 动画效果显示正在运行的步骤
- 清晰的状态标识和色彩编码

## 📋 测试场景

### 测试用例1: 完整预处理流程
1. 创建包含所有预处理步骤的实验
2. 点击"开始实验"
3. 验证MQTT消息接收和界面更新
4. 检查每个步骤的开始/完成状态
5. 确认自动跳转到实时监控

### 测试用例2: MQTT连接状态
1. 断开网络连接
2. 验证MQTT状态指示器显示"未连接"
3. 恢复连接后验证自动重连

### 测试用例3: 暂停/继续功能
1. 在预处理过程中点击暂停
2. 验证后端API调用和状态更新
3. 点击继续，验证恢复正常

### 测试用例4: 状态恢复
1. 开始预处理后跳转到其他页面
2. 返回实验管理页面
3. 验证状态完整恢复

## 🎯 关键改进

### 1. 去中心化控制
- 前端不再控制步骤进度
- 完全依赖后端MQTT消息驱动
- 提高了系统可靠性

### 2. 实时性增强
- 真实反映后端设备状态
- 消除前端计时器不准确的问题
- 支持多客户端同步

### 3. 可扩展性
- 轻松添加新的预处理步骤
- 统一的消息处理架构
- 便于后续功能扩展

## ⚠️ 注意事项

### 1. 后端依赖
- 需要后端实现对应的实验控制API
- 需要后端发送MQTT预处理状态消息
- 确保消息格式与前端期望一致

### 2. MQTT配置
- 确认MQTT broker配置正确
- 验证主题订阅权限
- 监控MQTT连接稳定性

### 3. 向后兼容
- 保留了localStorage状态恢复机制
- 旧的实验数据仍可正常显示
- 渐进式升级支持

## 🚀 部署清单

- [x] 前端代码更新完成
- [ ] 后端实验控制API实现
- [ ] 后端MQTT消息发送逻辑
- [ ] MQTT broker配置验证
- [ ] 端到端测试
- [ ] 生产环境部署

## 📊 性能优化

### 1. 消息频率控制
- 避免过于频繁的状态更新消息
- 合并连续的状态变更

### 2. 内存管理
- 及时清理无关的MQTT消息
- 优化localStorage存储大小

### 3. 网络优化
- 使用QoS级别控制消息可靠性
- 实现断线重连机制

这个实施方案将预处理控制完全迁移到了MQTT消息驱动模式，提供了更准确、实时的状态反馈，同时保持了良好的用户体验。