import { defineStore } from 'pinia'

export const useRealtimeDataStore = defineStore('realtimeData', {
  state: () => ({
    dataPoints: [],
    maxDataPoints: 300, // 保持最近5分钟数据 (300秒)
    isReceiving: false,
    startTime: null,
    totalReceived: 0
  }),

  getters: {
    // 获取图表数据格式
    getChartData: (state) => () => {
      return {
        labels: state.dataPoints.map(point => new Date(point.timestamp)),
        values: state.dataPoints.map(point => point.value)
      }
    },

    // 获取最新数据点
    getLatestDataPoint: (state) => () => {
      return state.dataPoints.length > 0
        ? state.dataPoints[state.dataPoints.length - 1]
        : null
    },

    // 获取数据统计信息
    getStatistics: (state) => () => {
      if (state.dataPoints.length === 0) {
        return {
          count: 0,
          average: 0,
          min: 0,
          max: 0,
          latest: 0
        }
      }

      const values = state.dataPoints.map(point => point.value)
      return {
        count: state.dataPoints.length,
        average: values.reduce((sum, val) => sum + val, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        latest: values[values.length - 1]
      }
    },

    // 获取数据接收速率
    getReceiveRate: (state) => () => {
      if (!state.startTime || state.dataPoints.length === 0) return 0

      const elapsedSeconds = (Date.now() - state.startTime) / 1000
      return state.totalReceived / elapsedSeconds
    }
  },

  actions: {
    // 添加数据点 - 实现开发文档要求的数据格式
    addDataPoint(data) {
      // 验证数据格式
      if (!data || typeof data !== 'object') {
        console.warn('无效的数据格式:', data)
        return
      }

      if (!data.timestamp || data.value === undefined) {
        console.warn('数据缺少必要字段:', data)
        return
      }

      const dataPoint = {
        timestamp: data.timestamp,
        value: Number(data.value),
        receivedAt: new Date().toISOString()
      }

      // 添加数据点
      this.dataPoints.push(dataPoint)
      this.totalReceived++

      // 设置开始时间
      if (!this.startTime) {
        this.startTime = Date.now()
      }

      // 保持最大数据点数量 (最近5分钟)
      if (this.dataPoints.length > this.maxDataPoints) {
        this.dataPoints.shift()
      }

      console.log(`接收数据: ${dataPoint.value} (总计: ${this.totalReceived})`)
    },

    // 清空数据
    clearData() {
      this.dataPoints = []
      this.totalReceived = 0
      this.startTime = null
      console.log('数据已清空')
    },

    // 设置接收状态
    setReceivingStatus(status) {
      this.isReceiving = status

      if (status) {
        console.log('开始接收数据')
      } else {
        console.log('停止接收数据')
      }
    },

    // 获取指定时间范围内的数据
    getDataInTimeRange(startTime, endTime) {
      return this.dataPoints.filter(point => {
        const timestamp = new Date(point.timestamp).getTime()
        return timestamp >= startTime && timestamp <= endTime
      })
    },

    // 导出数据
    exportData(format = 'json') {
      const data = {
        metadata: {
          totalPoints: this.dataPoints.length,
          startTime: this.startTime,
          exportTime: new Date().toISOString(),
          statistics: this.getStatistics()
        },
        dataPoints: this.dataPoints
      }

      if (format === 'json') {
        return JSON.stringify(data, null, 2)
      } else if (format === 'csv') {
        let csv = 'timestamp,value,receivedAt\\n'
        this.dataPoints.forEach(point => {
          csv += `${point.timestamp},${point.value},${point.receivedAt}\\n`
        })
        return csv
      }

      return data
    },

    // 数据质量检查
    validateDataQuality() {
      if (this.dataPoints.length < 2) return { valid: true, issues: [] }

      const issues = []
      let previousTime = null

      this.dataPoints.forEach((point, index) => {
        // 检查时间戳顺序
        const currentTime = new Date(point.timestamp).getTime()
        if (previousTime && currentTime < previousTime) {
          issues.push(`数据点 ${index}: 时间戳乱序`)
        }
        previousTime = currentTime

        // 检查数值范围 (根据开发文档，应该是0-100)
        if (point.value < 0 || point.value > 100) {
          issues.push(`数据点 ${index}: 数值超出范围 (${point.value})`)
        }
      })

      return {
        valid: issues.length === 0,
        issues
      }
    }
  }
})