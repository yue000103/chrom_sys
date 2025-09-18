import { ref, computed } from 'vue'

export function usePeakDetection() {
    // 峰检测状态
    const peakDetectionStatus = ref("active")

    // 基线和噪声水平
    const currentBaseline = ref(0.025)
    const noiseLevel = ref(0.008)

    // 检测到的峰
    const detectedPeaks = ref([
        {
            id: 1,
            retentionTime: 5.2,
            height: 0.485,
            tubeId: 1,
            status: "completed",
        },
        {
            id: 2,
            retentionTime: 8.7,
            height: 0.332,
            tubeId: 2,
            status: "completed",
        },
        {
            id: 3,
            retentionTime: 12.1,
            height: 0.678,
            tubeId: 3,
            status: "completed",
        },
        {
            id: 4,
            retentionTime: 15.8,
            height: 0.245,
            tubeId: 4,
            status: "completed",
        },
        {
            id: 5,
            retentionTime: 18.3,
            height: 0.156,
            tubeId: 5,
            status: "collecting",
        },
    ])

    // 峰检测弹窗状态
    const showPeakDialog = ref(false)

    // 峰数量统计
    const peakCount = computed(() => detectedPeaks.value.length)

    // 活跃峰数量
    const activePeaks = computed(() =>
        detectedPeaks.value.filter(peak => peak.status === "collecting").length
    )

    // 已完成峰数量
    const completedPeaks = computed(() =>
        detectedPeaks.value.filter(peak => peak.status === "completed").length
    )

    // 峰状态类型映射
    const getPeakStatusType = (status) => {
        const statusMap = {
            collecting: "warning",
            completed: "success",
            failed: "danger",
        }
        return statusMap[status] || "info"
    }

    // 峰状态文本映射
    const getPeakStatusText = (status) => {
        const statusMap = {
            collecting: "收集中",
            completed: "已完成",
            failed: "失败",
        }
        return statusMap[status] || status
    }

    // 打开峰检测详情弹窗
    const openPeakDialog = () => {
        showPeakDialog.value = true
    }

    // 关闭峰检测详情弹窗
    const closePeakDialog = () => {
        showPeakDialog.value = false
    }

    // 定位峰
    const locatePeak = (peak) => {
        console.log(
            `定位到峰 ${peak.id}，保留时间: ${peak.retentionTime}min`
        )
        // 在这里可以添加图表定位逻辑
        // 比如滚动到对应时间点，高亮显示等
    }

    // 导出单个峰
    const exportPeak = (peak) => {
        console.log(`导出峰 ${peak.id} 数据`)
        // 在这里可以添加单个峰导出逻辑
        const peakData = {
            id: peak.id,
            retentionTime: peak.retentionTime,
            height: peak.height,
            tubeId: peak.tubeId,
            status: peak.status,
            exportTime: new Date().toISOString()
        }
        // 实际导出逻辑
        return peakData
    }

    // 导出所有峰
    const exportAllPeaks = () => {
        console.log("导出所有峰数据")
        const allPeaksData = {
            peaks: detectedPeaks.value,
            totalCount: peakCount.value,
            exportTime: new Date().toISOString(),
            baseline: currentBaseline.value,
            noiseLevel: noiseLevel.value
        }
        // 实际导出逻辑
        return allPeaksData
    }

    // 添加新峰
    const addPeak = (peakData) => {
        const newPeak = {
            id: Math.max(...detectedPeaks.value.map(p => p.id), 0) + 1,
            retentionTime: peakData.retentionTime,
            height: peakData.height,
            tubeId: peakData.tubeId,
            status: peakData.status || "collecting",
        }
        detectedPeaks.value.push(newPeak)
        console.log(`添加新峰 ${newPeak.id}`)
        return newPeak
    }

    // 更新峰状态
    const updatePeakStatus = (peakId, status) => {
        const peak = detectedPeaks.value.find(p => p.id === peakId)
        if (peak) {
            peak.status = status
            console.log(`更新峰 ${peakId} 状态为 ${status}`)
        }
    }

    // 删除峰
    const removePeak = (peakId) => {
        const index = detectedPeaks.value.findIndex(p => p.id === peakId)
        if (index > -1) {
            detectedPeaks.value.splice(index, 1)
            console.log(`删除峰 ${peakId}`)
        }
    }

    // 清空所有峰
    const clearAllPeaks = () => {
        detectedPeaks.value = []
        console.log("清空所有峰数据")
    }

    // 更新基线和噪声水平
    const updateBaseline = (baseline) => {
        currentBaseline.value = baseline
    }

    const updateNoiseLevel = (noise) => {
        noiseLevel.value = noise
    }

    // 切换峰检测状态
    const togglePeakDetection = () => {
        peakDetectionStatus.value = peakDetectionStatus.value === "active" ? "inactive" : "active"
        console.log(`峰检测状态: ${peakDetectionStatus.value}`)
    }

    // 获取指定试管的峰
    const getPeaksByTube = (tubeId) => {
        return detectedPeaks.value.filter(peak => peak.tubeId === tubeId)
    }

    // 获取指定时间范围内的峰
    const getPeaksByTimeRange = (startTime, endTime) => {
        return detectedPeaks.value.filter(peak =>
            peak.retentionTime >= startTime && peak.retentionTime <= endTime
        )
    }

    return {
        // 响应式状态
        peakDetectionStatus,
        currentBaseline,
        noiseLevel,
        detectedPeaks,
        showPeakDialog,

        // 计算属性
        peakCount,
        activePeaks,
        completedPeaks,

        // 工具方法
        getPeakStatusType,
        getPeakStatusText,

        // 弹窗方法
        openPeakDialog,
        closePeakDialog,

        // 峰操作方法
        locatePeak,
        exportPeak,
        exportAllPeaks,
        addPeak,
        updatePeakStatus,
        removePeak,
        clearAllPeaks,

        // 检测参数更新
        updateBaseline,
        updateNoiseLevel,
        togglePeakDetection,

        // 查询方法
        getPeaksByTube,
        getPeaksByTimeRange
    }
}