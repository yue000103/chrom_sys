import { ref, computed } from 'vue'

export function useDeviceStatus() {
    // 当前数值
    const currentValues = ref({
        uv: 0.156, // 保持兼容性，主要用于压力显示
        uv254: 0.156, // UV254nm波长
        uv280: 0.132, // UV280nm波长
        pressure: 185,
        flowRate: 1.0,
        temperature: 25.5,
        ambientTemp: 22.3,
    })

    // 系统状态
    const systemStatus = ref({
        overall: "online",
        pump: "online",
        detector: "online",
        valve: "online",
    })

    // 液位状态
    const liquidLevels = ref({
        solutionA: 75,
        solutionB: 68,
        solutionC: 45,
        solutionD: 92,
        waste: 25,
    })

    // 压力等级判断
    const getPressureClass = (pressure) => {
        if (pressure > 350) return "danger"
        if (pressure > 200) return "warning"
        return "normal"
    }

    // 液位颜色判断
    const getLiquidColor = (level) => {
        if (level < 20) return "#f56c6c"
        if (level < 50) return "#e6a23c"
        return "#67c23a"
    }

    // 废液颜色判断
    const getWasteColor = (level) => {
        if (level > 95) return "#f56c6c"
        if (level > 80) return "#e6a23c"
        return "#67c23a"
    }

    // 压力监控状态
    const pressureStatus = computed(() => {
        return getPressureClass(currentValues.value.pressure)
    })

    // 系统整体状态
    const overallStatus = computed(() => {
        const statuses = Object.values(systemStatus.value)
        if (statuses.every(status => status === 'online')) return 'online'
        if (statuses.some(status => status === 'error')) return 'error'
        if (statuses.some(status => status === 'warning')) return 'warning'
        return 'offline'
    })

    // 液位警告
    const liquidWarnings = computed(() => {
        const warnings = []
        Object.entries(liquidLevels.value).forEach(([key, level]) => {
            if (key === 'waste' && level > 90) {
                warnings.push(`废液液位过高: ${level}%`)
            } else if (key !== 'waste' && level < 20) {
                warnings.push(`${key}液位过低: ${level}%`)
            }
        })
        return warnings
    })

    // 更新设备状态
    const updateDeviceStatus = (status) => {
        Object.assign(systemStatus.value, status)
    }

    // 更新当前数值
    const updateCurrentValues = (values) => {
        Object.assign(currentValues.value, values)
    }

    // 更新液位
    const updateLiquidLevels = (levels) => {
        Object.assign(liquidLevels.value, levels)
    }

    // 紧急停止
    const emergencyStop = () => {
        console.log("紧急停止")
        // 更新系统状态为停止
        updateDeviceStatus({
            overall: "offline",
            pump: "offline",
            detector: "offline",
            valve: "offline",
        })
    }

    return {
        // 响应式状态
        currentValues,
        systemStatus,
        liquidLevels,

        // 计算属性
        pressureStatus,
        overallStatus,
        liquidWarnings,

        // 工具方法
        getPressureClass,
        getLiquidColor,
        getWasteColor,

        // 更新方法
        updateDeviceStatus,
        updateCurrentValues,
        updateLiquidLevels,
        emergencyStop
    }
}