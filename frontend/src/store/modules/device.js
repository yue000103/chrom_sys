import { defineStore } from 'pinia'

export const useDeviceStore = defineStore('device', {
  state: () => ({
    // 设备连接状态
    devices: {
      pump: {
        id: 'pump_001',
        name: '四元梯度泵',
        status: 'online', // online, offline, error, maintenance
        lastUpdate: new Date(),
        parameters: {
          flowRate: 1.0,
          pressure: 185,
          maxPressure: 400,
          temperature: 25
        },
        alarms: []
      },
      detector: {
        id: 'detector_001',
        name: 'UV检测器',
        status: 'online',
        lastUpdate: new Date(),
        parameters: {
          wavelength: 254,
          signal: 0.156,
          lamp: 'on',
          temperature: 35
        },
        alarms: []
      },
      valve: {
        id: 'valve_001',
        name: '进样阀',
        status: 'online',
        lastUpdate: new Date(),
        parameters: {
          position: 'load',
          injectionVolume: 20,
          lastInjection: null
        },
        alarms: []
      },
      collector: {
        id: 'collector_001',
        name: '自动收集器',
        status: 'online',
        lastUpdate: new Date(),
        parameters: {
          currentPosition: 5,
          mode: 'collect', // collect, waste, bypass
          rackCapacity: 40,
          usedPositions: [1, 2, 3, 4]
        },
        alarms: []
      }
    },

    // 系统总体状态
    systemStatus: 'normal', // normal, warning, error, maintenance

    // 液位状态
    liquidLevels: {
      solutionA: 75,
      solutionB: 68,
      solutionC: 45,
      solutionD: 92,
      waste: 25,
      thresholds: {
        low: 20,
        critical: 10,
        wasteHigh: 80,
        wasteFull: 95
      }
    },

    // 通信状态
    communication: {
      websocket: {
        connected: true,
        lastHeartbeat: new Date(),
        reconnectAttempts: 0
      },
      serial: {
        ports: ['COM1', 'COM2', 'COM3'],
        activePort: 'COM1',
        baudRate: 9600
      }
    },

    // 维护信息
    maintenance: {
      lastMaintenance: new Date('2024-03-01'),
      nextMaintenance: new Date('2024-04-01'),
      maintenanceItems: [
        {
          item: '泵头清洗',
          lastDone: new Date('2024-03-01'),
          interval: 30, // 天
          status: 'due'
        },
        {
          item: '检测器灯泡更换',
          lastDone: new Date('2024-01-15'),
          interval: 90,
          status: 'ok'
        }
      ]
    }
  }),

  getters: {
    // 在线设备数量
    onlineDevicesCount: (state) => {
      return Object.values(state.devices).filter(device => device.status === 'online').length
    },

    // 总设备数量
    totalDevicesCount: (state) => {
      return Object.keys(state.devices).length
    },

    // 有告警的设备
    devicesWithAlarms: (state) => {
      return Object.values(state.devices).filter(device => device.alarms.length > 0)
    },

    // 系统是否正常
    isSystemHealthy: (state) => {
      return state.systemStatus === 'normal' &&
             Object.values(state.devices).every(device => device.status === 'online')
    },

    // 压力状态
    pressureStatus: (state) => {
      const pressure = state.devices.pump.parameters.pressure
      const maxPressure = state.devices.pump.parameters.maxPressure

      if (pressure > maxPressure * 0.9) return 'critical'
      if (pressure > maxPressure * 0.7) return 'warning'
      return 'normal'
    },

    // 液位警告
    liquidLevelWarnings: (state) => {
      const warnings = []
      const { liquidLevels } = state

      Object.keys(liquidLevels).forEach(solution => {
        if (solution === 'waste') {
          if (liquidLevels[solution] >= liquidLevels.thresholds.wasteFull) {
            warnings.push({ solution, level: 'critical', message: '废液容器已满' })
          } else if (liquidLevels[solution] >= liquidLevels.thresholds.wasteHigh) {
            warnings.push({ solution, level: 'warning', message: '废液容器接近满载' })
          }
        } else if (typeof liquidLevels[solution] === 'number') {
          if (liquidLevels[solution] <= liquidLevels.thresholds.critical) {
            warnings.push({ solution, level: 'critical', message: `${solution}液位严重不足` })
          } else if (liquidLevels[solution] <= liquidLevels.thresholds.low) {
            warnings.push({ solution, level: 'warning', message: `${solution}液位偏低` })
          }
        }
      })

      return warnings
    },

    // 需要维护的项目
    maintenanceNeeded: (state) => {
      return state.maintenance.maintenanceItems.filter(item => item.status === 'due' || item.status === 'overdue')
    },

    // 连接状态概览
    connectionStatus: (state) => {
      const { websocket, serial } = state.communication
      return {
        websocket: websocket.connected ? 'connected' : 'disconnected',
        serial: serial.activePort ? 'connected' : 'disconnected',
        overall: websocket.connected && serial.activePort ? 'stable' : 'unstable'
      }
    }
  },

  actions: {
    // 更新设备状态
    updateDeviceStatus(deviceId, status) {
      if (this.devices[deviceId]) {
        this.devices[deviceId].status = status
        this.devices[deviceId].lastUpdate = new Date()
        this.updateSystemStatus()
      }
    },

    // 更新设备参数
    updateDeviceParameters(deviceId, parameters) {
      if (this.devices[deviceId]) {
        this.devices[deviceId].parameters = {
          ...this.devices[deviceId].parameters,
          ...parameters
        }
        this.devices[deviceId].lastUpdate = new Date()
      }
    },

    // 添加设备告警
    addDeviceAlarm(deviceId, alarm) {
      if (this.devices[deviceId]) {
        this.devices[deviceId].alarms.push({
          id: Date.now(),
          level: alarm.level, // info, warning, critical
          message: alarm.message,
          timestamp: new Date(),
          acknowledged: false
        })
        this.updateSystemStatus()
      }
    },

    // 确认告警
    acknowledgeAlarm(deviceId, alarmId) {
      const device = this.devices[deviceId]
      if (device) {
        const alarm = device.alarms.find(a => a.id === alarmId)
        if (alarm) {
          alarm.acknowledged = true
          alarm.acknowledgedAt = new Date()
        }
      }
    },

    // 清除告警
    clearAlarm(deviceId, alarmId) {
      const device = this.devices[deviceId]
      if (device) {
        device.alarms = device.alarms.filter(a => a.id !== alarmId)
        this.updateSystemStatus()
      }
    },

    // 更新系统状态
    updateSystemStatus() {
      const devices = Object.values(this.devices)
      const hasError = devices.some(device => device.status === 'error')
      const hasWarning = devices.some(device =>
        device.status === 'warning' || device.alarms.some(alarm => alarm.level === 'warning')
      )
      const hasCritical = devices.some(device =>
        device.alarms.some(alarm => alarm.level === 'critical')
      )

      if (hasError || hasCritical) {
        this.systemStatus = 'error'
      } else if (hasWarning) {
        this.systemStatus = 'warning'
      } else {
        this.systemStatus = 'normal'
      }
    },

    // 更新液位
    updateLiquidLevels(levels) {
      this.liquidLevels = { ...this.liquidLevels, ...levels }
      this.checkLiquidLevelAlarms()
    },

    // 检查液位告警
    checkLiquidLevelAlarms() {
      const warnings = this.liquidLevelWarnings

      warnings.forEach(warning => {
        // 检查是否已存在相同告警
        const existingAlarm = this.devices.pump.alarms.find(
          alarm => alarm.message.includes(warning.solution)
        )

        if (!existingAlarm) {
          this.addDeviceAlarm('pump', {
            level: warning.level,
            message: warning.message
          })
        }
      })
    },

    // 连接WebSocket
    connectWebSocket() {
      this.communication.websocket.connected = true
      this.communication.websocket.lastHeartbeat = new Date()
      this.communication.websocket.reconnectAttempts = 0
    },

    // 断开WebSocket
    disconnectWebSocket() {
      this.communication.websocket.connected = false
    },

    // 更新心跳
    updateHeartbeat() {
      this.communication.websocket.lastHeartbeat = new Date()
    },

    // 重连尝试
    attemptReconnect() {
      this.communication.websocket.reconnectAttempts += 1
    },

    // 设置串口
    setSerialPort(port, baudRate = 9600) {
      this.communication.serial.activePort = port
      this.communication.serial.baudRate = baudRate
    },

    // 执行设备命令
    sendDeviceCommand(deviceId, command, parameters = {}) {
      return new Promise((resolve, reject) => {
        // 模拟发送命令
        setTimeout(() => {
          if (this.devices[deviceId] && this.devices[deviceId].status === 'online') {
            console.log(`发送命令到 ${deviceId}:`, command, parameters)
            resolve({ success: true, message: '命令执行成功' })
          } else {
            reject(new Error('设备离线或不存在'))
          }
        }, 500)
      })
    },

    // 校准设备
    calibrateDevice(deviceId, calibrationData) {
      return this.sendDeviceCommand(deviceId, 'calibrate', calibrationData)
    },

    // 重启设备
    restartDevice(deviceId) {
      this.updateDeviceStatus(deviceId, 'offline')

      setTimeout(() => {
        this.updateDeviceStatus(deviceId, 'online')
      }, 5000)

      return Promise.resolve({ success: true, message: '设备重启中' })
    },

    // 更新维护记录
    updateMaintenanceRecord(item, completedDate) {
      const maintenanceItem = this.maintenance.maintenanceItems.find(m => m.item === item)
      if (maintenanceItem) {
        maintenanceItem.lastDone = completedDate
        maintenanceItem.status = 'ok'

        // 计算下次维护时间
        const nextDate = new Date(completedDate)
        nextDate.setDate(nextDate.getDate() + maintenanceItem.interval)

        if (maintenanceItem.item === '泵头清洗') {
          this.maintenance.lastMaintenance = completedDate
          this.maintenance.nextMaintenance = nextDate
        }
      }
    },

    // 检查维护状态
    checkMaintenanceStatus() {
      const today = new Date()

      this.maintenance.maintenanceItems.forEach(item => {
        const nextDate = new Date(item.lastDone)
        nextDate.setDate(nextDate.getDate() + item.interval)

        if (today >= nextDate) {
          item.status = 'due'
        } else if (today > nextDate) {
          item.status = 'overdue'
        } else {
          item.status = 'ok'
        }
      })
    },

    // 获取设备诊断信息
    getDeviceDiagnostics(deviceId) {
      const device = this.devices[deviceId]
      if (!device) return null

      return {
        device: device.name,
        status: device.status,
        uptime: Date.now() - device.lastUpdate.getTime(),
        parameters: device.parameters,
        alarms: device.alarms,
        lastCommunication: device.lastUpdate,
        health: device.status === 'online' ? 'good' : 'poor'
      }
    }
  }
})