import { defineStore } from 'pinia'

export const useDataStore = defineStore('data', {
  state: () => ({
    // 实时数据
    realtimeData: {
      uv: [],
      pressure: [],
      flowRate: [],
      temperature: [],
      gradient: {
        solutionA: [],
        solutionB: [],
        solutionC: [],
        solutionD: []
      },
      maxDataPoints: 3000, // 最大数据点数
      samplingRate: 1 // 采样率（秒）
    },

    // 当前实时数值
    currentValues: {
      uv: 0.156,
      pressure: 185,
      flowRate: 1.0,
      temperature: 25.5,
      gradient: {
        solutionA: 80,
        solutionB: 20,
        solutionC: 0,
        solutionD: 0
      },
      timestamp: new Date()
    },

    // 峰检测数据
    peakDetection: {
      isActive: false,
      algorithm: 'auto', // auto, manual
      parameters: {
        threshold: 0.1,
        minPeakWidth: 5,
        maxPeakWidth: 300,
        baselineWindow: 180,
        smoothingWindow: 21
      },
      detectedPeaks: [],
      currentBaseline: 0.025,
      noiseLevel: 0.008
    },

    // 数据处理设置
    processing: {
      autoSave: true,
      saveInterval: 60, // 秒
      compression: true,
      smoothing: {
        enabled: true,
        algorithm: 'savitzky-golay',
        windowSize: 11,
        polynomialOrder: 3
      },
      filtering: {
        enabled: false,
        type: 'lowpass',
        cutoffFrequency: 10
      }
    },

    // 数据导出设置
    export: {
      format: 'csv', // csv, excel, json, txt
      includeMetadata: true,
      timeFormat: 'iso', // iso, relative, timestamp
      decimalPlaces: 4,
      separator: ','
    },

    // 数据缓存
    cache: {
      enabled: true,
      maxSize: 100, // MB
      currentSize: 0,
      compressionRatio: 0.3
    },

    // 历史数据查询
    query: {
      loading: false,
      filters: {
        dateRange: null,
        experimentId: null,
        dataType: 'all',
        operator: null
      },
      results: [],
      pagination: {
        currentPage: 1,
        pageSize: 100,
        total: 0
      }
    }
  }),

  getters: {
    // 获取指定时间范围的数据
    getDataInTimeRange: (state) => (startTime, endTime, dataType = 'uv') => {
      const data = state.realtimeData[dataType] || []
      return data.filter(point => {
        const pointTime = new Date(point.timestamp)
        return pointTime >= startTime && pointTime <= endTime
      })
    },

    // 获取最新的N个数据点
    getLatestData: (state) => (count = 100, dataType = 'uv') => {
      const data = state.realtimeData[dataType] || []
      return data.slice(-count)
    },

    // 数据统计信息
    dataStatistics: (state) => {
      const uvData = state.realtimeData.uv
      if (uvData.length === 0) return null

      const values = uvData.map(point => point.value)
      return {
        count: values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        mean: values.reduce((sum, val) => sum + val, 0) / values.length,
        latest: values[values.length - 1],
        timeRange: {
          start: uvData[0]?.timestamp,
          end: uvData[uvData.length - 1]?.timestamp
        }
      }
    },

    // 峰检测统计
    peakStatistics: (state) => {
      const peaks = state.peakDetection.detectedPeaks
      if (peaks.length === 0) return null

      const retentionTimes = peaks.map(peak => peak.retentionTime)
      const heights = peaks.map(peak => peak.height)
      const areas = peaks.map(peak => peak.area)

      return {
        count: peaks.length,
        averageRetentionTime: retentionTimes.reduce((sum, rt) => sum + rt, 0) / peaks.length,
        averageHeight: heights.reduce((sum, h) => sum + h, 0) / peaks.length,
        totalArea: areas.reduce((sum, area) => sum + area, 0),
        retentionTimeRange: {
          min: Math.min(...retentionTimes),
          max: Math.max(...retentionTimes)
        }
      }
    },

    // 数据质量评估
    dataQuality: (state) => {
      const uvData = state.realtimeData.uv
      if (uvData.length < 100) return null

      // 简单的数据质量评估
      const recent = uvData.slice(-100)
      const values = recent.map(point => point.value)
      const timestamps = recent.map(point => new Date(point.timestamp).getTime())

      // 检查数据连续性
      const timeGaps = []
      for (let i = 1; i < timestamps.length; i++) {
        timeGaps.push(timestamps[i] - timestamps[i - 1])
      }
      const avgTimeGap = timeGaps.reduce((sum, gap) => sum + gap, 0) / timeGaps.length
      const timeGapVariance = timeGaps.reduce((sum, gap) => sum + Math.pow(gap - avgTimeGap, 2), 0) / timeGaps.length

      // 检查信号稳定性
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
      const standardDeviation = Math.sqrt(variance)

      return {
        continuity: timeGapVariance < 1000 ? 'good' : 'poor', // 时间连续性
        stability: standardDeviation < 0.01 ? 'good' : 'fair', // 信号稳定性
        noiseLevel: state.peakDetection.noiseLevel,
        baseline: state.peakDetection.currentBaseline,
        overall: timeGapVariance < 1000 && standardDeviation < 0.01 ? 'excellent' : 'good'
      }
    },

    // 数据压缩率
    compressionInfo: (state) => {
      const totalPoints = Object.values(state.realtimeData).reduce((total, data) => {
        if (Array.isArray(data)) return total + data.length
        return total
      }, 0)

      const estimatedRawSize = totalPoints * 24 // 每个数据点大约24字节
      const compressedSize = estimatedRawSize * state.cache.compressionRatio

      return {
        totalPoints,
        estimatedRawSize: Math.round(estimatedRawSize / 1024 / 1024 * 100) / 100, // MB
        compressedSize: Math.round(compressedSize / 1024 / 1024 * 100) / 100, // MB
        compressionRatio: state.cache.compressionRatio,
        savingsPercent: Math.round((1 - state.cache.compressionRatio) * 100)
      }
    }
  },

  actions: {
    // 添加实时数据点
    addRealtimeData(dataType, value, timestamp = new Date()) {
      const dataArray = this.realtimeData[dataType]
      if (!Array.isArray(dataArray)) return

      const dataPoint = {
        value: Number(value),
        timestamp: timestamp,
        quality: this.assessDataQuality(value)
      }

      dataArray.push(dataPoint)

      // 限制数据点数量
      if (dataArray.length > this.realtimeData.maxDataPoints) {
        dataArray.shift()
      }

      // 更新当前值
      if (this.currentValues.hasOwnProperty(dataType)) {
        this.currentValues[dataType] = value
        this.currentValues.timestamp = timestamp
      }
    },

    // 批量添加数据
    addBatchData(dataType, dataPoints) {
      dataPoints.forEach(point => {
        this.addRealtimeData(dataType, point.value, point.timestamp)
      })
    },

    // 更新梯度数据
    updateGradientData(gradientValues, timestamp = new Date()) {
      Object.keys(gradientValues).forEach(solution => {
        if (this.realtimeData.gradient[solution]) {
          this.addRealtimeData(`gradient.${solution}`, gradientValues[solution], timestamp)
        }
      })

      // 更新当前梯度值
      this.currentValues.gradient = { ...this.currentValues.gradient, ...gradientValues }
    },

    // 评估数据质量
    assessDataQuality(value) {
      // 简单的数据质量评估
      if (typeof value !== 'number' || isNaN(value)) return 'invalid'
      if (value < 0) return 'questionable'
      if (value > 10) return 'questionable' // 假设UV值不应超过10
      return 'good'
    },

    // 启动峰检测
    startPeakDetection(parameters = {}) {
      this.peakDetection.isActive = true
      this.peakDetection.parameters = { ...this.peakDetection.parameters, ...parameters }
      this.peakDetection.detectedPeaks = []

      // 模拟峰检测过程
      this.simulatePeakDetection()
    },

    // 停止峰检测
    stopPeakDetection() {
      this.peakDetection.isActive = false
    },

    // 模拟峰检测
    simulatePeakDetection() {
      if (!this.peakDetection.isActive) return

      // 模拟检测到峰
      const uvData = this.realtimeData.uv
      if (uvData.length > 50) {
        const recent = uvData.slice(-50)
        const values = recent.map(point => point.value)
        const maxValue = Math.max(...values)

        if (maxValue > this.peakDetection.parameters.threshold) {
          const maxIndex = values.indexOf(maxValue)
          const peakTime = recent[maxIndex].timestamp

          // 检查是否已存在相近的峰
          const existingPeak = this.peakDetection.detectedPeaks.find(peak => {
            const timeDiff = Math.abs(new Date(peakTime) - new Date(peak.timestamp))
            return timeDiff < 30000 // 30秒内
          })

          if (!existingPeak) {
            this.addDetectedPeak({
              retentionTime: (Date.now() - recent[0].timestamp.getTime()) / 60000, // 分钟
              height: maxValue,
              area: maxValue * 20, // 简化计算
              timestamp: peakTime,
              width: 15,
              symmetry: 1.05,
              purity: 95 + Math.random() * 5
            })
          }
        }
      }

      // 继续检测
      setTimeout(() => this.simulatePeakDetection(), 5000)
    },

    // 添加检测到的峰
    addDetectedPeak(peakData) {
      const peak = {
        id: this.peakDetection.detectedPeaks.length + 1,
        ...peakData,
        status: 'detected',
        detectedAt: new Date()
      }

      this.peakDetection.detectedPeaks.push(peak)
    },

    // 手动添加峰
    addManualPeak(peakData) {
      const peak = {
        id: this.peakDetection.detectedPeaks.length + 1,
        ...peakData,
        status: 'manual',
        addedAt: new Date()
      }

      this.peakDetection.detectedPeaks.push(peak)
    },

    // 删除峰
    removePeak(peakId) {
      this.peakDetection.detectedPeaks = this.peakDetection.detectedPeaks.filter(
        peak => peak.id !== peakId
      )
    },

    // 更新峰信息
    updatePeak(peakId, updates) {
      const peak = this.peakDetection.detectedPeaks.find(p => p.id === peakId)
      if (peak) {
        Object.assign(peak, updates)
        peak.updatedAt = new Date()
      }
    },

    // 清空实时数据
    clearRealtimeData(dataType = null) {
      if (dataType) {
        if (this.realtimeData[dataType]) {
          this.realtimeData[dataType] = []
        }
      } else {
        // 清空所有数据
        this.realtimeData.uv = []
        this.realtimeData.pressure = []
        this.realtimeData.flowRate = []
        this.realtimeData.temperature = []
        Object.keys(this.realtimeData.gradient).forEach(solution => {
          this.realtimeData.gradient[solution] = []
        })
      }
    },

    // 导出数据
    exportData(options = {}) {
      const exportOptions = { ...this.export, ...options }
      const data = this.prepareDataForExport(exportOptions)

      return new Promise((resolve) => {
        // 模拟导出过程
        setTimeout(() => {
          resolve({
            data,
            filename: `experiment_data_${new Date().toISOString().slice(0, 19)}.${exportOptions.format}`,
            size: JSON.stringify(data).length
          })
        }, 1000)
      })
    },

    // 准备导出数据
    prepareDataForExport(options) {
      const exportData = {
        metadata: options.includeMetadata ? {
          exportTime: new Date().toISOString(),
          dataRange: this.dataStatistics?.timeRange,
          peakCount: this.peakDetection.detectedPeaks.length,
          dataPoints: this.realtimeData.uv.length
        } : null,
        uv: this.formatDataForExport(this.realtimeData.uv, options),
        pressure: this.formatDataForExport(this.realtimeData.pressure, options),
        gradient: {
          solutionA: this.formatDataForExport(this.realtimeData.gradient.solutionA, options),
          solutionB: this.formatDataForExport(this.realtimeData.gradient.solutionB, options),
          solutionC: this.formatDataForExport(this.realtimeData.gradient.solutionC, options),
          solutionD: this.formatDataForExport(this.realtimeData.gradient.solutionD, options)
        },
        peaks: this.peakDetection.detectedPeaks
      }

      return exportData
    },

    // 格式化导出数据
    formatDataForExport(dataArray, options) {
      return dataArray.map(point => ({
        time: this.formatTimeForExport(point.timestamp, options.timeFormat),
        value: Number(point.value.toFixed(options.decimalPlaces)),
        quality: point.quality
      }))
    },

    // 格式化时间
    formatTimeForExport(timestamp, format) {
      const date = new Date(timestamp)
      switch (format) {
        case 'iso':
          return date.toISOString()
        case 'relative':
          return Math.round((date.getTime() - this.realtimeData.uv[0]?.timestamp.getTime()) / 1000)
        case 'timestamp':
          return date.getTime()
        default:
          return date.toISOString()
      }
    },

    // 查询历史数据
    async queryHistoricalData(filters = {}) {
      this.query.loading = true
      this.query.filters = { ...this.query.filters, ...filters }

      // 模拟API查询
      return new Promise((resolve) => {
        setTimeout(() => {
          // 模拟查询结果
          const mockResults = Array.from({ length: 50 }, (_, i) => ({
            id: i + 1,
            experimentId: `exp_${Math.floor(Math.random() * 100)}`,
            timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
            dataType: ['uv', 'pressure', 'temperature'][Math.floor(Math.random() * 3)],
            value: Math.random() * 2,
            operator: ['张三', '李四', '王五'][Math.floor(Math.random() * 3)]
          }))

          this.query.results = mockResults
          this.query.pagination.total = mockResults.length
          this.query.loading = false

          resolve(mockResults)
        }, 1500)
      })
    },

    // 更新数据处理设置
    updateProcessingSettings(settings) {
      this.processing = { ...this.processing, ...settings }
    },

    // 应用数据平滑
    applySmoothingToData(dataType) {
      const data = this.realtimeData[dataType]
      if (!data || !this.processing.smoothing.enabled) return

      const windowSize = this.processing.smoothing.windowSize
      const halfWindow = Math.floor(windowSize / 2)

      for (let i = halfWindow; i < data.length - halfWindow; i++) {
        const window = data.slice(i - halfWindow, i + halfWindow + 1)
        const smoothedValue = window.reduce((sum, point) => sum + point.value, 0) / window.length
        data[i].value = smoothedValue
        data[i].smoothed = true
      }
    },

    // 计算基线
    calculateBaseline() {
      const uvData = this.realtimeData.uv
      if (uvData.length < 100) return

      const recentData = uvData.slice(-100)
      const values = recentData.map(point => point.value)
      values.sort((a, b) => a - b)

      // 使用最小值的10%作为基线
      const percentile10 = Math.floor(values.length * 0.1)
      this.peakDetection.currentBaseline = values.slice(0, percentile10)
        .reduce((sum, val) => sum + val, 0) / percentile10
    },

    // 计算噪声水平
    calculateNoiseLevel() {
      const uvData = this.realtimeData.uv
      if (uvData.length < 50) return

      const recentData = uvData.slice(-50)
      const values = recentData.map(point => point.value)
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length

      this.peakDetection.noiseLevel = Math.sqrt(variance)
    }
  }
})