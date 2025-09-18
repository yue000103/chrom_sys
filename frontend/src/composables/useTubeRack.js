import { ref, computed } from 'vue'

export function useTubeRack() {
    // 试管数据
    const tubes = ref(
        Array.from({ length: 40 }, (_, i) => ({
            id: i + 1,
            status:
                i < 4
                    ? "completed"
                    : i === 4
                    ? "collecting"
                    : i === 5
                    ? "ready"
                    : "empty",
            fillLevel: i < 4 ? 85 : i === 4 ? 45 : 0,
            peakId: i < 4 ? i + 1 : null,
        }))
    )

    // 当前试管
    const currentTube = ref(5)

    // 收集模式
    const collectionMode = ref("收集")

    // 选中的试管
    const selectedTubeForSwitch = ref("")

    // 选择的试管列表（用于合并操作）
    const selectedTubes = ref(new Set())

    // 合并任务列表
    const mergeTasks = ref([])

    // 任务弹窗显示状态
    const showMergeTaskDialog = ref(false)

    // 可用试管
    const availableTubes = computed(() => {
        return tubes.value
            .filter(
                (tube) => tube.status === "empty" || tube.status === "ready"
            )
            .map((tube) => tube.id)
    })

    // 已完成试管数量
    const completedTubes = computed(() => {
        return tubes.value.filter((tube) => tube.status === "completed")
            .length
    })

    // 选中的试管数组（用于模板显示）
    const selectedTubesArray = computed(() => {
        return Array.from(selectedTubes.value).sort((a, b) => a - b)
    })

    // 选中试管数量
    const selectedTubesCount = computed(() => {
        return selectedTubes.value.size
    })

    // 试管状态样式
    const getTubeClass = (tube) => {
        const classes = [tube.status]
        if (selectedTubes.value.has(tube.id)) {
            classes.push('selected')
        }
        return classes.join(' ')
    }

    // 试管提示信息
    const getTubeTooltip = (tube) => {
        const statusText = {
            empty: "空闲",
            ready: "准备中",
            collecting: "收集中",
            completed: "已完成",
        }
        return `试管 ${tube.id} - ${statusText[tube.status]}`
    }

    // 选择试管（用于多选）
    const selectTube = (tube) => {
        const tubeId = tube.id
        const newSelected = new Set(selectedTubes.value)

        if (newSelected.has(tubeId)) {
            newSelected.delete(tubeId)
        } else {
            newSelected.add(tubeId)
        }

        selectedTubes.value = newSelected
        console.log("选择试管:", Array.from(selectedTubes.value))
    }

    // 清空选择
    const clearSelection = () => {
        selectedTubes.value = new Set()
    }

    // 切换到指定试管
    const switchToTube = () => {
        if (!selectedTubeForSwitch.value) {
            console.log("请先选择试管")
            return
        }

        currentTube.value = selectedTubeForSwitch.value
        console.log("切换到试管:", selectedTubeForSwitch.value)

        // 更新试管状态
        tubes.value.forEach(tube => {
            if (tube.id === selectedTubeForSwitch.value) {
                tube.status = "collecting"
            } else if (tube.status === "collecting") {
                tube.status = "completed"
            }
        })
    }

    // 切换收集模式
    const changeCollectionMode = (mode) => {
        collectionMode.value = mode
        console.log("切换收集模式:", mode)
    }

    // 试管反转操作 - 反转选择状态
    const reverseTubes = () => {
        console.log("执行试管反转操作")

        const newSelected = new Set()

        if (selectedTubes.value.size === 0) {
            // 如果没有选择试管，则选中所有试管
            tubes.value.forEach(tube => {
                newSelected.add(tube.id)
            })
            console.log("没有选择试管，选中所有试管")
        } else {
            // 如果有选择试管，则选中未选择的试管
            tubes.value.forEach(tube => {
                if (!selectedTubes.value.has(tube.id)) {
                    newSelected.add(tube.id)
                }
            })
            console.log("反转选择：选中未选择的试管")
        }

        selectedTubes.value = newSelected
        console.log("反转完成，当前选中试管:", Array.from(selectedTubes.value))
    }

    // 试管合并操作 - 显示任务管理弹窗
    const mergeTubes = () => {
        if (selectedTubesCount.value === 0) {
            console.log("请先选择要合并的试管")
            return
        }

        const selectedTubesList = Array.from(selectedTubes.value).sort((a, b) => a - b)

        // 创建新的合并任务
        const newTask = {
            id: Date.now(),
            tubeIds: selectedTubesList,
            type: '合并',
            status: 'pending', // pending, running, paused, completed, terminated
            createdAt: new Date().toLocaleString(),
            progress: 0
        }

        mergeTasks.value.push(newTask)
        showMergeTaskDialog.value = true

        console.log("创建合并任务:", newTask)
    }

    // 任务控制方法
    const startTask = (taskId) => {
        const task = mergeTasks.value.find(t => t.id === taskId)
        if (task) {
            task.status = 'running'
            console.log("开始任务:", taskId)
        }
    }

    const pauseTask = (taskId) => {
        const task = mergeTasks.value.find(t => t.id === taskId)
        if (task) {
            task.status = 'paused'
            console.log("暂停任务:", taskId)
        }
    }

    const resumeTask = (taskId) => {
        const task = mergeTasks.value.find(t => t.id === taskId)
        if (task) {
            task.status = 'running'
            console.log("继续任务:", taskId)
        }
    }

    const terminateTask = (taskId) => {
        const task = mergeTasks.value.find(t => t.id === taskId)
        if (task) {
            task.status = 'terminated'
            console.log("终止任务:", taskId)
        }
    }

    // 批量任务控制
    const batchStartTasks = (taskIds) => {
        taskIds.forEach(id => startTask(id))
    }

    const batchPauseTasks = (taskIds) => {
        taskIds.forEach(id => pauseTask(id))
    }

    const batchResumeTasks = (taskIds) => {
        taskIds.forEach(id => resumeTask(id))
    }

    const batchTerminateTasks = (taskIds) => {
        taskIds.forEach(id => terminateTask(id))
    }

    // 删除任务
    const deleteTask = (taskId) => {
        const index = mergeTasks.value.findIndex(t => t.id === taskId)
        if (index > -1) {
            mergeTasks.value.splice(index, 1)
            console.log("删除任务:", taskId)
        }
    }

    // 关闭任务弹窗
    const closeMergeTaskDialog = () => {
        showMergeTaskDialog.value = false
        clearSelection()
    }

    // 试管清洗操作
    const cleanTubes = () => {
        console.log("执行试管清洗操作")
        // 模拟清洗操作 - 清洗所有已使用的试管
        tubes.value = tubes.value.map((tube) => {
            if (tube.status === "completed" || tube.status === "waste") {
                return {
                    ...tube,
                    status: "empty",
                    fillLevel: 0,
                    peakId: null,
                }
            }
            return tube
        })
        console.log("试管清洗完成，所有已使用试管已清空")
    }

    // 更新试管状态
    const updateTubeStatus = (tubeId, status, fillLevel = null) => {
        const tube = tubes.value.find(t => t.id === tubeId)
        if (tube) {
            tube.status = status
            if (fillLevel !== null) {
                tube.fillLevel = fillLevel
            }
        }
    }

    // 设置试管峰ID
    const setTubePeak = (tubeId, peakId) => {
        const tube = tubes.value.find(t => t.id === tubeId)
        if (tube) {
            tube.peakId = peakId
        }
    }

    // 获取下一个可用试管
    const getNextAvailableTube = () => {
        return tubes.value.find(tube => tube.status === "empty")
    }

    // 自动切换到下一个试管
    const autoSwitchToNext = () => {
        const nextTube = getNextAvailableTube()
        if (nextTube) {
            // 将当前试管标记为完成
            updateTubeStatus(currentTube.value, "completed")

            // 切换到下一个试管
            currentTube.value = nextTube.id
            updateTubeStatus(nextTube.id, "collecting")

            console.log(`自动切换到试管 ${nextTube.id}`)
        } else {
            console.log("没有可用的空试管")
        }
    }

    return {
        // 响应式状态
        tubes,
        currentTube,
        collectionMode,
        selectedTubeForSwitch,
        selectedTubes,
        mergeTasks,
        showMergeTaskDialog,

        // 计算属性
        availableTubes,
        completedTubes,
        selectedTubesArray,
        selectedTubesCount,

        // 工具方法
        getTubeClass,
        getTubeTooltip,

        // 试管操作方法
        selectTube,
        clearSelection,
        switchToTube,
        changeCollectionMode,
        reverseTubes,
        mergeTubes,
        cleanTubes,
        updateTubeStatus,
        setTubePeak,
        getNextAvailableTube,
        autoSwitchToNext,

        // 任务管理方法
        startTask,
        pauseTask,
        resumeTask,
        terminateTask,
        batchStartTasks,
        batchPauseTasks,
        batchResumeTasks,
        batchTerminateTasks,
        deleteTask,
        closeMergeTaskDialog
    }
}