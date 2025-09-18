import { defineStore } from 'pinia'

export const useExperimentStore = defineStore('experiment', {
  state: () => ({
    // 当前实验
    currentExperiment: null,

    // 实验队列
    experimentQueue: [],

    // 实验历史
    experimentHistory: [],

    // 实验状态
    experimentStatus: 'idle', // idle, preparing, running, paused, completed, failed

    // 实验进度
    progress: {
      percentage: 0,
      elapsedTime: 0,
      remainingTime: 0,
      currentStep: ''
    },

    // 预处理状态
    pretreatment: {
      isRunning: false,
      currentStep: null,
      steps: [],
      completed: false
    },

    // 收集设置
    collection: {
      strategy: 'peak', // peak, volume, manual
      currentTube: 1,
      mode: 'collect', // collect, waste
      collectedTubes: [],
      parameters: {
        collectionVolume: 5.0,
        washVolume: 5.0,
        washCycles: 1
      }
    },

    // 实验统计
    statistics: {
      totalExperiments: 0,
      todayExperiments: 0,
      successRate: 0,
      averageDuration: 0
    }
  }),

  getters: {
    // 是否有运行中的实验
    hasRunningExperiment: (state) => {
      return ['preparing', 'running', 'paused'].includes(state.experimentStatus)
    },

    // 队列中的实验数量
    queueLength: (state) => state.experimentQueue.length,

    // 下一个实验
    nextExperiment: (state) => {
      return state.experimentQueue.length > 0 ? state.experimentQueue[0] : null
    },

    // 运行时间（分钟）
    runningTimeMinutes: (state) => {
      return Math.floor(state.progress.elapsedTime / 60)
    },

    // 剩余时间（分钟）
    remainingTimeMinutes: (state) => {
      return Math.floor(state.progress.remainingTime / 60)
    },

    // 已收集试管数量
    collectedTubeCount: (state) => {
      return state.collection.collectedTubes.length
    },

    // 可用试管列表
    availableTubes: (state) => {
      const usedTubes = state.collection.collectedTubes.map(tube => tube.id)
      return Array.from({ length: 40 }, (_, i) => i + 1)
        .filter(id => !usedTubes.includes(id))
    }
  },

  actions: {
    // 创建新实验
    createExperiment(experimentData) {
      const experiment = {
        id: Date.now(),
        name: experimentData.name,
        method: experimentData.method,
        operator: experimentData.operator,
        parameters: experimentData.parameters,
        status: 'queued',
        createdAt: new Date(),
        estimatedDuration: experimentData.estimatedDuration || 30
      }

      this.experimentQueue.push(experiment)
      this.updateStatistics()
    },

    // 开始实验
    startExperiment(experimentId) {
      const experiment = this.experimentQueue.find(exp => exp.id === experimentId)
      if (experiment) {
        this.currentExperiment = { ...experiment, status: 'running', startTime: new Date() }
        this.experimentStatus = 'running'
        this.experimentQueue = this.experimentQueue.filter(exp => exp.id !== experimentId)

        // 开始进度跟踪
        this.startProgressTracking()
      }
    },

    // 暂停实验
    pauseExperiment() {
      if (this.experimentStatus === 'running') {
        this.experimentStatus = 'paused'
        this.currentExperiment.pausedAt = new Date()
      }
    },

    // 继续实验
    resumeExperiment() {
      if (this.experimentStatus === 'paused') {
        this.experimentStatus = 'running'
        this.currentExperiment.resumedAt = new Date()
      }
    },

    // 停止实验
    stopExperiment() {
      if (this.hasRunningExperiment) {
        this.experimentStatus = 'completed'
        this.currentExperiment.endTime = new Date()
        this.currentExperiment.duration = Date.now() - this.currentExperiment.startTime.getTime()

        // 移动到历史记录
        this.experimentHistory.unshift(this.currentExperiment)
        this.currentExperiment = null

        // 重置进度
        this.resetProgress()
        this.updateStatistics()
      }
    },

    // 开始预处理
    startPretreatment(steps) {
      this.pretreatment.isRunning = true
      this.pretreatment.steps = steps
      this.pretreatment.currentStep = steps[0]
      this.experimentStatus = 'preparing'
    },

    // 完成预处理
    completePretreatment() {
      this.pretreatment.isRunning = false
      this.pretreatment.completed = true
      this.pretreatment.currentStep = null
    },

    // 切换试管
    switchTube(tubeId) {
      this.collection.currentTube = tubeId
    },

    // 切换收集模式
    switchCollectionMode(mode) {
      this.collection.mode = mode
    },

    // 添加收集的试管
    addCollectedTube(tubeData) {
      this.collection.collectedTubes.push({
        id: tubeData.tubeId,
        volume: tubeData.volume,
        collectionTime: new Date(),
        peakId: tubeData.peakId,
        retentionTime: tubeData.retentionTime
      })
    },

    // 更新实验进度
    updateProgress(progressData) {
      this.progress = { ...this.progress, ...progressData }
    },

    // 开始进度跟踪
    startProgressTracking() {
      this.progressInterval = setInterval(() => {
        if (this.experimentStatus === 'running' && this.currentExperiment) {
          const elapsed = Date.now() - this.currentExperiment.startTime.getTime()
          const estimated = this.currentExperiment.estimatedDuration * 60 * 1000

          this.progress.elapsedTime = elapsed / 1000
          this.progress.remainingTime = Math.max(0, (estimated - elapsed) / 1000)
          this.progress.percentage = Math.min(100, (elapsed / estimated) * 100)
        }
      }, 1000)
    },

    // 重置进度
    resetProgress() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
        this.progressInterval = null
      }

      this.progress = {
        percentage: 0,
        elapsedTime: 0,
        remainingTime: 0,
        currentStep: ''
      }
    },

    // 更新统计信息
    updateStatistics() {
      this.statistics.totalExperiments = this.experimentHistory.length

      // 今日实验数量
      const today = new Date().toDateString()
      this.statistics.todayExperiments = this.experimentHistory.filter(
        exp => new Date(exp.createdAt).toDateString() === today
      ).length

      // 成功率
      const completedExperiments = this.experimentHistory.filter(
        exp => exp.status === 'completed'
      ).length
      this.statistics.successRate = this.experimentHistory.length > 0
        ? Math.round((completedExperiments / this.experimentHistory.length) * 100)
        : 0

      // 平均持续时间
      const totalDuration = this.experimentHistory.reduce(
        (total, exp) => total + (exp.duration || 0), 0
      )
      this.statistics.averageDuration = this.experimentHistory.length > 0
        ? Math.round(totalDuration / this.experimentHistory.length / 60000) // 转换为分钟
        : 0
    },

    // 从队列中移除实验
    removeFromQueue(experimentId) {
      this.experimentQueue = this.experimentQueue.filter(exp => exp.id !== experimentId)
    },

    // 调整队列顺序
    reorderQueue(oldIndex, newIndex) {
      const experiment = this.experimentQueue.splice(oldIndex, 1)[0]
      this.experimentQueue.splice(newIndex, 0, experiment)
    },

    // 清空队列
    clearQueue() {
      this.experimentQueue = []
    },

    // 获取实验历史
    getExperimentHistory(filters = {}) {
      let history = [...this.experimentHistory]

      // 按日期过滤
      if (filters.dateRange && filters.dateRange.length === 2) {
        const [startDate, endDate] = filters.dateRange
        history = history.filter(exp => {
          const expDate = new Date(exp.createdAt)
          return expDate >= new Date(startDate) && expDate <= new Date(endDate)
        })
      }

      // 按状态过滤
      if (filters.status && filters.status !== 'all') {
        history = history.filter(exp => exp.status === filters.status)
      }

      // 按关键词搜索
      if (filters.keyword) {
        const keyword = filters.keyword.toLowerCase()
        history = history.filter(exp =>
          exp.name.toLowerCase().includes(keyword) ||
          exp.method.toLowerCase().includes(keyword) ||
          exp.operator.toLowerCase().includes(keyword)
        )
      }

      return history
    }
  }
})