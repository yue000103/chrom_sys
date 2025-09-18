import { defineStore } from 'pinia'

export const useAlarmStore = defineStore('alarm', {
  state: () => ({
    // 活跃告警
    activeAlarms: [],

    // 告警历史
    alarmHistory: [],

    // 告警统计
    statistics: {
      total: 0,
      critical: 0,
      warning: 0,
      info: 0,
      resolved: 0,
      acknowledged: 0
    },

    // 告警设置
    settings: {
      soundEnabled: true,
      popupEnabled: true,
      emailEnabled: false,
      logEnabled: true,
      autoAcknowledge: false,
      autoAcknowledgeDelay: 300, // 秒
      suppressDuplicates: true,
      duplicateThreshold: 60 // 秒
    },

    // 告警规则
    rules: {
      pressure: {
        enabled: true,
        warning: { threshold: 300, message: '系统压力偏高' },
        critical: { threshold: 350, message: '系统压力过高，存在安全风险' },
        actions: {
          warning: ['log', 'popup'],
          critical: ['log', 'popup', 'sound', 'emergency_stop']
        }
      },
      temperature: {
        enabled: true,
        warning: { min: 15, max: 45, message: '温度超出正常范围' },
        critical: { min: 10, max: 50, message: '温度严重超出安全范围' },
        actions: {
          warning: ['log', 'popup'],
          critical: ['log', 'popup', 'sound']
        }
      },
      liquidLevel: {
        enabled: true,
        warning: { threshold: 20, message: '液位偏低' },
        critical: { threshold: 10, message: '液位严重不足' },
        waste: {
          warning: { threshold: 80, message: '废液容器接近满载' },
          critical: { threshold: 95, message: '废液容器已满' }
        },
        actions: {
          warning: ['log', 'popup'],
          critical: ['log', 'popup', 'sound']
        }
      },
      communication: {
        enabled: true,
        timeout: 5000,
        message: '设备通信异常',
        actions: ['log', 'popup', 'sound']
      },
      peakDetection: {
        enabled: true,
        noiseThreshold: 0.05,
        baselineDrift: 0.1,
        message: '峰检测质量异常',
        actions: ['log', 'popup']
      },
      systemHealth: {
        enabled: true,
        cpuThreshold: 80,
        memoryThreshold: 85,
        diskThreshold: 90,
        message: '系统资源不足',
        actions: ['log', 'popup']
      }
    },

    // 告警过滤器
    filters: {
      level: 'all', // all, critical, warning, info
      status: 'all', // all, active, acknowledged, resolved
      source: 'all', // all, device specific
      timeRange: null // [startDate, endDate]
    },

    // 通知状态
    notifications: {
      unreadCount: 0,
      lastNotification: null,
      soundPlaying: false
    }
  }),

  getters: {
    // 活跃告警数量
    activeAlarmCount: (state) => state.activeAlarms.length,

    // 按级别分组的活跃告警
    activeAlarmsByLevel: (state) => {
      return state.activeAlarms.reduce((groups, alarm) => {
        const level = alarm.level
        if (!groups[level]) groups[level] = []
        groups[level].push(alarm)
        return groups
      }, {})
    },

    // 严重告警
    criticalAlarms: (state) => {
      return state.activeAlarms.filter(alarm => alarm.level === 'critical')
    },

    // 未确认告警
    unacknowledgedAlarms: (state) => {
      return state.activeAlarms.filter(alarm => !alarm.acknowledged)
    },

    // 过滤后的告警历史
    filteredAlarmHistory: (state) => {
      let filtered = [...state.alarmHistory]

      // 按级别过滤
      if (state.filters.level !== 'all') {
        filtered = filtered.filter(alarm => alarm.level === state.filters.level)
      }

      // 按状态过滤
      if (state.filters.status !== 'all') {
        filtered = filtered.filter(alarm => alarm.status === state.filters.status)
      }

      // 按来源过滤
      if (state.filters.source !== 'all') {
        filtered = filtered.filter(alarm => alarm.source === state.filters.source)
      }

      // 按时间范围过滤
      if (state.filters.timeRange && state.filters.timeRange.length === 2) {
        const [startDate, endDate] = state.filters.timeRange
        filtered = filtered.filter(alarm => {
          const alarmDate = new Date(alarm.createdAt)
          return alarmDate >= new Date(startDate) && alarmDate <= new Date(endDate)
        })
      }

      return filtered.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    },

    // 最近的告警
    recentAlarms: (state) => {
      return state.alarmHistory
        .slice(0, 10)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    },

    // 告警趋势
    alarmTrend: (state) => {
      const now = new Date()
      const dayMs = 24 * 60 * 60 * 1000
      const trends = {}

      // 计算过去7天的告警趋势
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now.getTime() - i * dayMs)
        const dateStr = date.toISOString().split('T')[0]

        const dayAlarms = state.alarmHistory.filter(alarm => {
          const alarmDate = new Date(alarm.createdAt).toISOString().split('T')[0]
          return alarmDate === dateStr
        })

        trends[dateStr] = {
          total: dayAlarms.length,
          critical: dayAlarms.filter(a => a.level === 'critical').length,
          warning: dayAlarms.filter(a => a.level === 'warning').length,
          info: dayAlarms.filter(a => a.level === 'info').length
        }
      }

      return trends
    },

    // 系统健康状态
    systemHealthStatus: (state) => {
      const criticalCount = state.activeAlarms.filter(a => a.level === 'critical').length
      const warningCount = state.activeAlarms.filter(a => a.level === 'warning').length

      if (criticalCount > 0) return 'critical'
      if (warningCount > 0) return 'warning'
      return 'healthy'
    }
  },

  actions: {
    // 创建新告警
    createAlarm(alarmData) {
      // 检查重复告警
      if (this.settings.suppressDuplicates) {
        const existingAlarm = this.activeAlarms.find(alarm =>
          alarm.source === alarmData.source &&
          alarm.message === alarmData.message &&
          (Date.now() - new Date(alarm.createdAt).getTime()) < this.settings.duplicateThreshold * 1000
        )

        if (existingAlarm) {
          existingAlarm.count = (existingAlarm.count || 1) + 1
          existingAlarm.lastOccurred = new Date()
          return existingAlarm
        }
      }

      const alarm = {
        id: Date.now(),
        level: alarmData.level || 'info',
        title: alarmData.title || '系统告警',
        message: alarmData.message,
        source: alarmData.source || 'system',
        status: 'active',
        acknowledged: false,
        createdAt: new Date(),
        acknowledgedAt: null,
        resolvedAt: null,
        count: 1,
        lastOccurred: new Date(),
        metadata: alarmData.metadata || {},
        actions: alarmData.actions || []
      }

      // 添加到活跃告警
      this.activeAlarms.push(alarm)

      // 添加到历史记录
      this.alarmHistory.unshift({ ...alarm })

      // 更新统计
      this.updateStatistics()

      // 执行告警动作
      this.executeAlarmActions(alarm)

      // 更新通知状态
      this.notifications.unreadCount++
      this.notifications.lastNotification = alarm

      return alarm
    },

    // 确认告警
    acknowledgeAlarm(alarmId, acknowledgedBy = '当前用户') {
      const alarm = this.activeAlarms.find(a => a.id === alarmId)
      if (alarm && !alarm.acknowledged) {
        alarm.acknowledged = true
        alarm.acknowledgedAt = new Date()
        alarm.acknowledgedBy = acknowledgedBy

        // 更新历史记录
        const historyAlarm = this.alarmHistory.find(a => a.id === alarmId)
        if (historyAlarm) {
          historyAlarm.acknowledged = true
          historyAlarm.acknowledgedAt = alarm.acknowledgedAt
          historyAlarm.acknowledgedBy = acknowledgedBy
        }

        this.updateStatistics()
      }
    },

    // 解决告警
    resolveAlarm(alarmId, resolvedBy = '当前用户', resolution = '') {
      const alarmIndex = this.activeAlarms.findIndex(a => a.id === alarmId)
      if (alarmIndex !== -1) {
        const alarm = this.activeAlarms[alarmIndex]
        alarm.status = 'resolved'
        alarm.resolvedAt = new Date()
        alarm.resolvedBy = resolvedBy
        alarm.resolution = resolution

        // 更新历史记录
        const historyAlarm = this.alarmHistory.find(a => a.id === alarmId)
        if (historyAlarm) {
          historyAlarm.status = 'resolved'
          historyAlarm.resolvedAt = alarm.resolvedAt
          historyAlarm.resolvedBy = resolvedBy
          historyAlarm.resolution = resolution
        }

        // 从活跃告警中移除
        this.activeAlarms.splice(alarmIndex, 1)

        this.updateStatistics()
      }
    },

    // 批量确认告警
    acknowledgeMultipleAlarms(alarmIds, acknowledgedBy = '当前用户') {
      alarmIds.forEach(id => {
        this.acknowledgeAlarm(id, acknowledgedBy)
      })
    },

    // 清除所有已确认的告警
    clearAcknowledgedAlarms() {
      const acknowledgedAlarms = this.activeAlarms.filter(alarm => alarm.acknowledged)
      acknowledgedAlarms.forEach(alarm => {
        this.resolveAlarm(alarm.id, '系统', '批量清除')
      })
    },

    // 执行告警动作
    executeAlarmActions(alarm) {
      const actions = alarm.actions || []

      actions.forEach(action => {
        switch (action) {
          case 'log':
            this.logAlarm(alarm)
            break
          case 'popup':
            if (this.settings.popupEnabled) {
              this.showPopupNotification(alarm)
            }
            break
          case 'sound':
            if (this.settings.soundEnabled) {
              this.playAlarmSound(alarm)
            }
            break
          case 'email':
            if (this.settings.emailEnabled) {
              this.sendEmailNotification(alarm)
            }
            break
          case 'emergency_stop':
            this.triggerEmergencyStop(alarm)
            break
        }
      })
    },

    // 记录告警日志
    logAlarm(alarm) {
      console.log(`[ALARM ${alarm.level.toUpperCase()}] ${alarm.source}: ${alarm.message}`)
    },

    // 显示弹窗通知
    showPopupNotification(alarm) {
      // 这里应该触发UI组件显示弹窗
      console.log('显示告警弹窗:', alarm.title)
    },

    // 播放告警声音
    playAlarmSound(alarm) {
      if (!this.notifications.soundPlaying) {
        this.notifications.soundPlaying = true

        // 模拟播放声音
        setTimeout(() => {
          this.notifications.soundPlaying = false
        }, 3000)

        console.log('播放告警声音:', alarm.level)
      }
    },

    // 发送邮件通知
    sendEmailNotification(alarm) {
      console.log('发送邮件通知:', alarm.message)
    },

    // 触发紧急停机
    triggerEmergencyStop(alarm) {
      console.log('触发紧急停机:', alarm.message)
      // 这里应该调用实验停止的相关方法
    },

    // 检查压力告警
    checkPressureAlarm(pressure) {
      const rule = this.rules.pressure
      if (!rule.enabled) return

      if (pressure >= rule.critical.threshold) {
        this.createAlarm({
          level: 'critical',
          title: '压力严重超限',
          message: `${rule.critical.message}，当前压力: ${pressure} bar`,
          source: 'pressure_sensor',
          actions: rule.actions.critical
        })
      } else if (pressure >= rule.warning.threshold) {
        this.createAlarm({
          level: 'warning',
          title: '压力超限警告',
          message: `${rule.warning.message}，当前压力: ${pressure} bar`,
          source: 'pressure_sensor',
          actions: rule.actions.warning
        })
      }
    },

    // 检查温度告警
    checkTemperatureAlarm(temperature) {
      const rule = this.rules.temperature
      if (!rule.enabled) return

      if (temperature <= rule.critical.min || temperature >= rule.critical.max) {
        this.createAlarm({
          level: 'critical',
          title: '温度严重异常',
          message: `${rule.critical.message}，当前温度: ${temperature}°C`,
          source: 'temperature_sensor',
          actions: rule.actions.critical
        })
      } else if (temperature <= rule.warning.min || temperature >= rule.warning.max) {
        this.createAlarm({
          level: 'warning',
          title: '温度异常警告',
          message: `${rule.warning.message}，当前温度: ${temperature}°C`,
          source: 'temperature_sensor',
          actions: rule.actions.warning
        })
      }
    },

    // 检查液位告警
    checkLiquidLevelAlarm(solution, level) {
      const rule = this.rules.liquidLevel
      if (!rule.enabled) return

      if (solution === 'waste') {
        if (level >= rule.waste.critical.threshold) {
          this.createAlarm({
            level: 'critical',
            title: '废液容器已满',
            message: `${rule.waste.critical.message}，当前液位: ${level}%`,
            source: 'waste_sensor',
            actions: rule.actions.critical
          })
        } else if (level >= rule.waste.warning.threshold) {
          this.createAlarm({
            level: 'warning',
            title: '废液容器警告',
            message: `${rule.waste.warning.message}，当前液位: ${level}%`,
            source: 'waste_sensor',
            actions: rule.actions.warning
          })
        }
      } else {
        if (level <= rule.critical.threshold) {
          this.createAlarm({
            level: 'critical',
            title: `${solution}液位严重不足`,
            message: `${rule.critical.message}，当前液位: ${level}%`,
            source: `${solution}_sensor`,
            actions: rule.actions.critical
          })
        } else if (level <= rule.warning.threshold) {
          this.createAlarm({
            level: 'warning',
            title: `${solution}液位偏低`,
            message: `${rule.warning.message}，当前液位: ${level}%`,
            source: `${solution}_sensor`,
            actions: rule.actions.warning
          })
        }
      }
    },

    // 检查通信告警
    checkCommunicationAlarm(deviceId, isConnected) {
      const rule = this.rules.communication
      if (!rule.enabled) return

      if (!isConnected) {
        this.createAlarm({
          level: 'warning',
          title: '设备通信异常',
          message: `${rule.message}: ${deviceId}`,
          source: deviceId,
          actions: rule.actions
        })
      }
    },

    // 更新告警统计
    updateStatistics() {
      this.statistics.total = this.alarmHistory.length
      this.statistics.critical = this.alarmHistory.filter(a => a.level === 'critical').length
      this.statistics.warning = this.alarmHistory.filter(a => a.level === 'warning').length
      this.statistics.info = this.alarmHistory.filter(a => a.level === 'info').length
      this.statistics.resolved = this.alarmHistory.filter(a => a.status === 'resolved').length
      this.statistics.acknowledged = this.alarmHistory.filter(a => a.acknowledged).length
    },

    // 更新告警设置
    updateAlarmSettings(settings) {
      this.settings = { ...this.settings, ...settings }
    },

    // 更新告警规则
    updateAlarmRule(ruleType, rule) {
      if (this.rules[ruleType]) {
        this.rules[ruleType] = { ...this.rules[ruleType], ...rule }
      }
    },

    // 设置告警过滤器
    setAlarmFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    // 清除告警历史
    clearAlarmHistory(days = null) {
      if (days) {
        const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
        this.alarmHistory = this.alarmHistory.filter(alarm =>
          new Date(alarm.createdAt) > cutoffDate
        )
      } else {
        this.alarmHistory = []
      }
      this.updateStatistics()
    },

    // 导出告警数据
    exportAlarmData(format = 'json') {
      const data = {
        activeAlarms: this.activeAlarms,
        alarmHistory: this.alarmHistory,
        statistics: this.statistics,
        exportedAt: new Date().toISOString()
      }

      switch (format) {
        case 'json':
          return JSON.stringify(data, null, 2)
        case 'csv':
          return this.convertToCSV(this.alarmHistory)
        default:
          return data
      }
    },

    // 转换为CSV格式
    convertToCSV(alarms) {
      const headers = ['ID', '级别', '标题', '消息', '来源', '状态', '创建时间', '确认时间', '解决时间']
      const rows = alarms.map(alarm => [
        alarm.id,
        alarm.level,
        alarm.title,
        alarm.message,
        alarm.source,
        alarm.status,
        alarm.createdAt,
        alarm.acknowledgedAt || '',
        alarm.resolvedAt || ''
      ])

      return [headers, ...rows].map(row => row.join(',')).join('\n')
    },

    // 标记通知为已读
    markNotificationsAsRead() {
      this.notifications.unreadCount = 0
    },

    // 测试告警系统
    testAlarmSystem() {
      this.createAlarm({
        level: 'info',
        title: '告警系统测试',
        message: '这是一个测试告警，系统功能正常',
        source: 'test_system',
        actions: ['log', 'popup']
      })
    }
  }
})