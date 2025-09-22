# 实验状态恢复功能测试

## 修复内容

已修复实验监控在导航后状态丢失的问题，现在包含以下改进：

### 1. 状态持久化增强
- ✅ 暂停/继续状态保存到 localStorage
- ✅ 当前预处理步骤位置保存
- ✅ 实验暂停状态标记保存

### 2. 状态恢复逻辑
- ✅ 组件挂载时自动恢复 localStorage 中的实验状态
- ✅ 恢复预处理进度和当前步骤
- ✅ 恢复暂停状态和计时器状态
- ✅ 错误处理和数据清理

### 3. 新增函数
- `restoreExperimentState()`: 从 localStorage 恢复实验状态
- 增强 `pauseExperiment()`: 保存暂停状态到 localStorage
- 增强 `resumeExperiment()`: 保存继续状态到 localStorage
- 增强 `nextPretreatmentStep()`: 保存步骤进度到 localStorage

## 测试步骤

### 测试用例1: 预处理状态恢复
1. 创建带有预处理步骤的实验（系统清洗+柱平衡）
2. 点击"开始实验"，确认进入预处理阶段
3. 等待几秒，点击"实时监控"跳转
4. 返回实验管理页面
5. ✅ 验证：实验监控区域应显示之前的实验
6. ✅ 验证：预处理进度应显示正确的步骤和倒计时

### 测试用例2: 暂停状态恢复
1. 开始实验并进入预处理阶段
2. 点击"暂停"按钮
3. 跳转到实时监控页面
4. 返回实验管理页面
5. ✅ 验证：应显示"继续"按钮而不是"暂停"按钮
6. ✅ 验证：计时器应保持暂停状态

### 测试用例3: 步骤进度恢复
1. 开始多步骤预处理实验
2. 手动点击"下一步"跳到第二个步骤
3. 跳转到实时监控页面
4. 返回实验管理页面
5. ✅ 验证：应显示正确的当前步骤（第二步）
6. ✅ 验证：步骤进度条应正确显示

### 测试用例4: 数据清理
1. 在 localStorage 中手动创建无效的实验数据
2. 刷新页面
3. ✅ 验证：应自动清理无效数据，不出现错误
4. ✅ 验证：控制台应显示清理日志

## 代码改进点

### 关键修改
```javascript
// 1. 新增状态恢复函数
const restoreExperimentState = () => {
    try {
        const savedExperiment = localStorage.getItem('currentExperiment');
        if (savedExperiment) {
            const experiment = JSON.parse(savedExperiment);
            selectedExperiment.value = experiment;

            if (experiment.status === 'pretreatment') {
                showPretreatmentProgress.value = true;
                calculatePretreatmentSteps(experiment);

                // 恢复步骤位置
                if (experiment.currentPretreatmentStep !== undefined) {
                    currentPretreatmentStep.value = experiment.currentPretreatmentStep;
                }

                // 恢复暂停状态
                if (experiment.experimentPaused) {
                    experimentPaused.value = true;
                } else {
                    startPretreatmentStep();
                }
            }
        }
    } catch (error) {
        console.error("恢复实验状态失败:", error);
        localStorage.removeItem('currentExperiment');
    }
};

// 2. 组件挂载时恢复状态
onMounted(() => {
    fetchAllExperiments();
    restoreExperimentState(); // 新增
});

// 3. 状态变更时保存到 localStorage
const pauseExperiment = (experiment) => {
    experimentPaused.value = true;
    experiment.experimentPaused = true; // 新增
    localStorage.setItem('currentExperiment', JSON.stringify(experiment)); // 新增
    // ...
};
```

## 验证要点

1. **状态一致性**: 确保界面状态与 localStorage 数据一致
2. **计时器恢复**: 暂停的实验恢复后不应自动开始计时
3. **步骤准确性**: 预处理步骤应从正确位置继续
4. **数据安全**: 损坏的数据应被自动清理
5. **用户体验**: 状态恢复应该无缝，用户感知不到中断

## 解决的问题

- ❌ **原问题**: 跳转实时监控后返回，实验监控界面清空
- ✅ **已解决**: 实验状态完整保持，包括预处理进度、暂停状态、当前步骤等
- ✅ **改进**: 增加了错误处理和数据验证机制