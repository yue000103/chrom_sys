import { ref, computed } from 'vue'

export function useGradientControl() {
    // 梯度值 - 流动相A保持恒定80%，B保持20%
    const gradientValues = ref({
        solutionA: 80,
        solutionB: 20,
        solutionC: 0,
        solutionD: 0,
    })

    // 梯度时间控制
    const selectedGradientTime = ref("")

    // 可用梯度时间选项
    const availableGradientTimes = ref([
        { label: "立即执行", value: "immediate" },
        { label: "1分钟后", value: "1min" },
        { label: "2分钟后", value: "2min" },
        { label: "5分钟后", value: "5min" },
        { label: "10分钟后", value: "10min" },
        { label: "15分钟后", value: "15min" },
        { label: "20分钟后", value: "20min" },
        { label: "30分钟后", value: "30min" },
    ])

    // 梯度历史记录
    const gradientHistory = ref([])

    // 梯度总和验证
    const gradientSum = computed(() => {
        return gradientValues.value.solutionA +
               gradientValues.value.solutionB +
               gradientValues.value.solutionC +
               gradientValues.value.solutionD
    })

    // 梯度是否有效
    const isGradientValid = computed(() => {
        return gradientSum.value === 100
    })

    // 当前梯度配置
    const currentGradientConfig = computed(() => {
        return {
            ...gradientValues.value,
            timestamp: new Date().toISOString(),
            isValid: isGradientValid.value
        }
    })

    // 应用梯度变更
    const applyGradientChange = () => {
        if (!selectedGradientTime.value) {
            console.log("请选择执行时间")
            return false
        }

        if (!isGradientValid.value) {
            console.log("梯度总和必须为100%")
            return false
        }

        const gradientChangeData = {
            executionTime: selectedGradientTime.value,
            solutions: {
                solutionA: gradientValues.value.solutionA,
                solutionB: gradientValues.value.solutionB,
                solutionC: gradientValues.value.solutionC,
                solutionD: gradientValues.value.solutionD,
            },
            timestamp: new Date().toISOString(),
        }

        console.log("发送梯度调整指令到后端:", gradientChangeData)

        // 添加到历史记录
        addToHistory(gradientChangeData)

        // 模拟发送到后端
        // 这里可以调用实际的API接口
        // await deviceApi.setGradientChange(gradientChangeData);

        // 显示成功消息（可以使用 Element Plus 的 Message 组件）
        console.log(
            `梯度调整已设置：${
                selectedGradientTime.value === "immediate"
                    ? "立即执行"
                    : selectedGradientTime.value
            }执行`
        )

        // 清空选择
        selectedGradientTime.value = ""
        return true
    }

    // 添加到历史记录
    const addToHistory = (gradientData) => {
        gradientHistory.value.unshift({
            id: Date.now(),
            ...gradientData,
            appliedAt: new Date().toISOString()
        })

        // 限制历史记录数量
        if (gradientHistory.value.length > 50) {
            gradientHistory.value = gradientHistory.value.slice(0, 50)
        }
    }

    // 重置梯度值
    const resetGradientValues = () => {
        gradientValues.value = {
            solutionA: 80,
            solutionB: 20,
            solutionC: 0,
            solutionD: 0,
        }
        console.log("梯度值已重置")
    }

    // 设置预设梯度
    const setPresetGradient = (preset) => {
        const presets = {
            "高A": { solutionA: 90, solutionB: 10, solutionC: 0, solutionD: 0 },
            "高B": { solutionA: 10, solutionB: 90, solutionC: 0, solutionD: 0 },
            "平衡": { solutionA: 50, solutionB: 50, solutionC: 0, solutionD: 0 },
            "默认": { solutionA: 80, solutionB: 20, solutionC: 0, solutionD: 0 },
        }

        if (presets[preset]) {
            gradientValues.value = { ...presets[preset] }
            console.log(`应用预设梯度: ${preset}`)
        }
    }

    // 更新单个溶液比例
    const updateSolutionPercentage = (solution, percentage) => {
        const maxValue = Math.min(100, Math.max(0, percentage))
        gradientValues.value[solution] = maxValue

        // 自动调整其他溶液比例以保持总和为100%
        autoAdjustGradient(solution)
    }

    // 自动调整梯度比例
    const autoAdjustGradient = (changedSolution) => {
        const solutions = ['solutionA', 'solutionB', 'solutionC', 'solutionD']
        const otherSolutions = solutions.filter(s => s !== changedSolution)

        const changedValue = gradientValues.value[changedSolution]
        const remainingPercentage = 100 - changedValue

        // 按比例分配剩余百分比
        const otherValues = otherSolutions.map(s => gradientValues.value[s])
        const otherSum = otherValues.reduce((sum, val) => sum + val, 0)

        if (otherSum > 0) {
            otherSolutions.forEach(solution => {
                const ratio = gradientValues.value[solution] / otherSum
                gradientValues.value[solution] = Math.round(remainingPercentage * ratio)
            })
        } else {
            // 如果其他溶液都是0，则平均分配
            const avgPercentage = Math.floor(remainingPercentage / otherSolutions.length)
            otherSolutions.forEach((solution, index) => {
                gradientValues.value[solution] = index === 0
                    ? remainingPercentage - avgPercentage * (otherSolutions.length - 1)
                    : avgPercentage
            })
        }
    }

    // 获取梯度变化趋势
    const getGradientTrend = () => {
        if (gradientHistory.value.length < 2) return "stable"

        const recent = gradientHistory.value[0]
        const previous = gradientHistory.value[1]

        const recentA = recent.solutions.solutionA
        const previousA = previous.solutions.solutionA

        if (recentA > previousA) return "increasing"
        if (recentA < previousA) return "decreasing"
        return "stable"
    }

    // 验证梯度配置
    const validateGradientConfig = (config = gradientValues.value) => {
        const sum = Object.values(config).reduce((total, value) => total + value, 0)
        const errors = []

        if (sum !== 100) {
            errors.push(`梯度总和为${sum}%，必须为100%`)
        }

        Object.entries(config).forEach(([key, value]) => {
            if (value < 0 || value > 100) {
                errors.push(`${key}的值${value}%超出有效范围(0-100%)`)
            }
        })

        return {
            isValid: errors.length === 0,
            errors
        }
    }

    // 模拟从后端获取可用时间
    const fetchAvailableGradientTimes = async () => {
        // 模拟API调用延迟
        setTimeout(() => {
            // 模拟从后端返回的时间选项
            const backendTimes = [
                { label: "立即执行", value: "immediate" },
                { label: "1分钟后", value: "1min" },
                { label: "2分钟后", value: "2min" },
                { label: "5分钟后", value: "5min" },
                { label: "10分钟后", value: "10min" },
                { label: "15分钟后", value: "15min" },
                { label: "20分钟后", value: "20min" },
                { label: "30分钟后", value: "30min" },
            ]

            availableGradientTimes.value = backendTimes
            console.log("从后端获取到可用时间选项:", backendTimes)
        }, 500) // 模拟500ms网络延迟
    }

    return {
        // 响应式状态
        gradientValues,
        selectedGradientTime,
        availableGradientTimes,
        gradientHistory,

        // 计算属性
        gradientSum,
        isGradientValid,
        currentGradientConfig,

        // 主要操作方法
        applyGradientChange,
        resetGradientValues,
        setPresetGradient,
        updateSolutionPercentage,

        // 工具方法
        autoAdjustGradient,
        getGradientTrend,
        validateGradientConfig,
        addToHistory,
        fetchAvailableGradientTimes
    }
}