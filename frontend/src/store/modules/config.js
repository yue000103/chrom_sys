import { defineStore } from 'pinia'

export const useConfigStore = defineStore('config', {
  state: () => ({
    // 系统配置
    system: {
      name: '液相色谱仪控制系统',
      version: '1.0.0',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      dateFormat: 'YYYY-MM-DD',
      timeFormat: '24h',
      theme: 'light', // light, dark, auto
      autoSave: true,
      autoSaveInterval: 300 // 秒
    },

    // 用户配置
    user: {
      currentUser: {
        id: 1,
        name: '系统管理员',
        username: 'admin',
        role: 'administrator', // administrator, operator, viewer
        permissions: ['read', 'write', 'delete', 'admin'],
        preferences: {
          defaultMethod: null,
          dashboardLayout: 'default',
          notifications: true,
          soundAlerts: true
        }
      },
      users: [
        {
          id: 1,
          name: '系统管理员',
          username: 'admin',
          role: 'administrator',
          active: true,
          lastLogin: new Date('2024-03-15 09:00:00'),
          permissions: ['read', 'write', 'delete', 'admin']
        },
        {
          id: 2,
          name: '张三',
          username: 'zhangsan',
          role: 'operator',
          active: true,
          lastLogin: new Date('2024-03-15 08:30:00'),
          permissions: ['read', 'write']
        },
        {
          id: 3,
          name: '李四',
          username: 'lisi',
          role: 'viewer',
          active: true,
          lastLogin: new Date('2024-03-14 16:45:00'),
          permissions: ['read']
        }
      ]
    },

    // 设备配置
    device: {
      pump: {
        type: 'quaternary',
        model: 'LC-2030C',
        serialNumber: 'LC2030C001',
        maxPressure: 400,
        maxFlowRate: 10.0,
        minFlowRate: 0.001,
        channels: ['A', 'B', 'C', 'D'],
        calibration: {
          lastCalibrated: new Date('2024-03-01'),
          calibrationDue: new Date('2024-06-01'),
          flowRateCorrection: {
            A: 1.0,
            B: 0.98,
            C: 1.02,
            D: 0.99
          }
        }
      },
      detector: {
        type: 'UV-VIS',
        model: 'SPD-20A',
        serialNumber: 'SPD20A001',
        wavelengthRange: [190, 800],
        lampType: 'deuterium',
        flowCellVolume: 10,
        calibration: {
          lastCalibrated: new Date('2024-02-15'),
          calibrationDue: new Date('2024-05-15'),
          wavelengthAccuracy: 0.5,
          linearityCorrection: 1.0
        }
      },
      collector: {
        type: 'fraction_collector',
        model: 'FRC-10A',
        serialNumber: 'FRC10A001',
        rackCapacity: 40,
        tubeVolume: 15,
        positionAccuracy: 0.1,
        calibration: {
          lastCalibrated: new Date('2024-03-10'),
          positionCorrection: 0
        }
      }
    },

    // 方法配置
    methods: {
      defaultParameters: {
        flowRate: 1.0,
        injectionVolume: 20,
        temperature: 25,
        wavelength: 254,
        runTime: 30,
        equilibrationTime: 5,
        gradientMode: 'auto'
      },
      validationRules: {
        flowRate: { min: 0.001, max: 10.0 },
        pressure: { min: 0, max: 400 },
        temperature: { min: 4, max: 60 },
        wavelength: { min: 190, max: 800 },
        runTime: { min: 1, max: 999 },
        injectionVolume: { min: 0.1, max: 100 }
      },
      autoSave: true,
      backupCount: 10
    },

    // 数据配置
    data: {
      acquisition: {
        samplingRate: 1, // Hz
        dataPoints: 3000,
        autoBaseline: true,
        noiseFiltering: true,
        peakDetection: {
          enabled: true,
          sensitivity: 'medium', // low, medium, high
          minPeakWidth: 5,
          maxPeakWidth: 300,
          thresholdMultiplier: 3
        }
      },
      storage: {
        autoSave: true,
        saveInterval: 60, // 秒
        compression: true,
        backupEnabled: true,
        retentionPeriod: 365, // 天
        archiveAfter: 90 // 天
      },
      export: {
        defaultFormat: 'csv',
        includeMetadata: true,
        decimalPlaces: 4,
        dateTimeFormat: 'iso'
      }
    },

    // 告警配置
    alarms: {
      pressure: {
        enabled: true,
        warningThreshold: 300,
        criticalThreshold: 350,
        autoStop: true
      },
      temperature: {
        enabled: true,
        minThreshold: 10,
        maxThreshold: 50,
        warningRange: [15, 45]
      },
      liquidLevel: {
        enabled: true,
        lowThreshold: 20,
        criticalThreshold: 10,
        wasteHighThreshold: 80,
        wasteFullThreshold: 95
      },
      communication: {
        enabled: true,
        timeout: 5000, // 毫秒
        retryAttempts: 3,
        heartbeatInterval: 30 // 秒
      },
      notifications: {
        sound: true,
        popup: true,
        email: false,
        logToFile: true
      }
    },

    // 网络配置
    network: {
      api: {
        baseUrl: 'http://localhost:8000',
        timeout: 10000,
        retryAttempts: 3
      },
      websocket: {
        url: 'ws://localhost:8000/ws',
        reconnectInterval: 5000,
        maxReconnectAttempts: 10,
        heartbeatInterval: 30000
      },
      serial: {
        baudRate: 9600,
        dataBits: 8,
        stopBits: 1,
        parity: 'none',
        autoDetect: true
      }
    },

    // 安全配置
    security: {
      sessionTimeout: 3600, // 秒
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: false
      },
      auditLog: {
        enabled: true,
        retentionPeriod: 90, // 天
        logLevel: 'info' // debug, info, warning, error
      },
      backup: {
        enabled: true,
        interval: 'daily', // hourly, daily, weekly
        retention: 30, // 天
        encryption: false
      }
    }
  }),

  getters: {
    // 获取当前用户权限
    currentUserPermissions: (state) => {
      return state.user.currentUser.permissions || []
    },

    // 检查用户是否有特定权限
    hasPermission: (state) => (permission) => {
      return state.user.currentUser.permissions?.includes(permission) || false
    },

    // 检查用户角色
    isAdministrator: (state) => {
      return state.user.currentUser.role === 'administrator'
    },

    isOperator: (state) => {
      return ['administrator', 'operator'].includes(state.user.currentUser.role)
    },

    // 获取活跃用户
    activeUsers: (state) => {
      return state.user.users.filter(user => user.active)
    },

    // 获取设备校准状态
    deviceCalibrationStatus: (state) => {
      const devices = state.device
      const status = {}

      Object.keys(devices).forEach(deviceType => {
        const device = devices[deviceType]
        if (device.calibration) {
          const dueDate = new Date(device.calibration.calibrationDue)
          const today = new Date()
          const daysUntilDue = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24))

          status[deviceType] = {
            lastCalibrated: device.calibration.lastCalibrated,
            calibrationDue: device.calibration.calibrationDue,
            daysUntilDue,
            status: daysUntilDue < 0 ? 'overdue' :
                   daysUntilDue < 7 ? 'due_soon' : 'ok'
          }
        }
      })

      return status
    },

    // 获取有效的参数范围
    getParameterRange: (state) => (parameter) => {
      return state.methods.validationRules[parameter] || null
    },

    // 检查参数是否在有效范围内
    isParameterValid: (state) => (parameter, value) => {
      const range = state.methods.validationRules[parameter]
      if (!range) return true

      return value >= range.min && value <= range.max
    },

    // 获取告警配置
    getAlarmConfig: (state) => (alarmType) => {
      return state.alarms[alarmType] || null
    },

    // 检查功能是否启用
    isFeatureEnabled: (state) => (feature) => {
      const featurePath = feature.split('.')
      let config = state

      for (const path of featurePath) {
        config = config[path]
        if (config === undefined) return false
      }

      return config?.enabled || false
    }
  },

  actions: {
    // 更新系统配置
    updateSystemConfig(config) {
      this.system = { ...this.system, ...config }
      this.saveConfigToStorage('system')
    },

    // 更新用户配置
    updateUserConfig(config) {
      this.user = { ...this.user, ...config }
      this.saveConfigToStorage('user')
    },

    // 切换当前用户
    switchUser(userId) {
      const user = this.user.users.find(u => u.id === userId)
      if (user && user.active) {
        this.user.currentUser = { ...user }
        user.lastLogin = new Date()
        this.saveConfigToStorage('user')
      }
    },

    // 添加新用户
    addUser(userData) {
      const newUser = {
        id: Math.max(...this.user.users.map(u => u.id)) + 1,
        ...userData,
        active: true,
        lastLogin: null
      }

      this.user.users.push(newUser)
      this.saveConfigToStorage('user')
    },

    // 更新用户信息
    updateUser(userId, updates) {
      const userIndex = this.user.users.findIndex(u => u.id === userId)
      if (userIndex !== -1) {
        this.user.users[userIndex] = { ...this.user.users[userIndex], ...updates }

        // 如果更新的是当前用户
        if (this.user.currentUser.id === userId) {
          this.user.currentUser = { ...this.user.users[userIndex] }
        }

        this.saveConfigToStorage('user')
      }
    },

    // 删除用户
    removeUser(userId) {
      if (userId === this.user.currentUser.id) {
        throw new Error('不能删除当前登录用户')
      }

      this.user.users = this.user.users.filter(u => u.id !== userId)
      this.saveConfigToStorage('user')
    },

    // 更新设备配置
    updateDeviceConfig(deviceType, config) {
      if (this.device[deviceType]) {
        this.device[deviceType] = { ...this.device[deviceType], ...config }
        this.saveConfigToStorage('device')
      }
    },

    // 更新设备校准信息
    updateDeviceCalibration(deviceType, calibrationData) {
      if (this.device[deviceType]?.calibration) {
        this.device[deviceType].calibration = {
          ...this.device[deviceType].calibration,
          ...calibrationData
        }
        this.saveConfigToStorage('device')
      }
    },

    // 更新方法配置
    updateMethodConfig(config) {
      this.methods = { ...this.methods, ...config }
      this.saveConfigToStorage('methods')
    },

    // 更新数据配置
    updateDataConfig(config) {
      this.data = { ...this.data, ...config }
      this.saveConfigToStorage('data')
    },

    // 更新告警配置
    updateAlarmConfig(alarmType, config) {
      if (this.alarms[alarmType]) {
        this.alarms[alarmType] = { ...this.alarms[alarmType], ...config }
        this.saveConfigToStorage('alarms')
      }
    },

    // 更新网络配置
    updateNetworkConfig(config) {
      this.network = { ...this.network, ...config }
      this.saveConfigToStorage('network')
    },

    // 更新安全配置
    updateSecurityConfig(config) {
      this.security = { ...this.security, ...config }
      this.saveConfigToStorage('security')
    },

    // 验证参数
    validateParameter(parameter, value) {
      const range = this.getParameterRange(parameter)
      if (!range) return { valid: true }

      const valid = value >= range.min && value <= range.max
      return {
        valid,
        message: valid ? '' : `参数 ${parameter} 必须在 ${range.min} - ${range.max} 范围内`
      }
    },

    // 重置配置为默认值
    resetToDefaults(configType = null) {
      if (configType) {
        // 重置特定配置类型
        this.loadDefaultConfig(configType)
      } else {
        // 重置所有配置
        Object.keys(this.$state).forEach(key => {
          this.loadDefaultConfig(key)
        })
      }
    },

    // 加载默认配置
    loadDefaultConfig(configType) {
      // 这里应该从默认配置文件加载
      console.log(`加载默认配置: ${configType}`)
    },

    // 保存配置到本地存储
    saveConfigToStorage(configType) {
      try {
        const config = this[configType]
        localStorage.setItem(`chromatography_config_${configType}`, JSON.stringify(config))
      } catch (error) {
        console.error('保存配置失败:', error)
      }
    },

    // 从本地存储加载配置
    loadConfigFromStorage(configType) {
      try {
        const stored = localStorage.getItem(`chromatography_config_${configType}`)
        if (stored) {
          const config = JSON.parse(stored)
          this[configType] = { ...this[configType], ...config }
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    },

    // 导出配置
    exportConfig() {
      const config = {
        system: this.system,
        user: this.user,
        device: this.device,
        methods: this.methods,
        data: this.data,
        alarms: this.alarms,
        network: this.network,
        security: this.security,
        exportedAt: new Date().toISOString(),
        version: this.system.version
      }

      return JSON.stringify(config, null, 2)
    },

    // 导入配置
    importConfig(configJson) {
      try {
        const config = JSON.parse(configJson)

        // 验证配置版本兼容性
        if (config.version && config.version !== this.system.version) {
          console.warn('配置版本不匹配，可能存在兼容性问题')
        }

        // 逐个更新配置
        Object.keys(config).forEach(key => {
          if (this.hasOwnProperty(key) && key !== 'exportedAt' && key !== 'version') {
            this[key] = { ...this[key], ...config[key] }
            this.saveConfigToStorage(key)
          }
        })

        return { success: true, message: '配置导入成功' }
      } catch (error) {
        return { success: false, message: `配置导入失败: ${error.message}` }
      }
    },

    // 初始化配置
    initializeConfig() {
      // 从本地存储加载所有配置
      Object.keys(this.$state).forEach(configType => {
        this.loadConfigFromStorage(configType)
      })

      // 检查设备校准状态
      this.checkCalibrationStatus()
    },

    // 检查校准状态
    checkCalibrationStatus() {
      const calibrationStatus = this.deviceCalibrationStatus

      Object.keys(calibrationStatus).forEach(deviceType => {
        const status = calibrationStatus[deviceType]
        if (status.status === 'overdue' || status.status === 'due_soon') {
          // 可以在这里触发告警或通知
          console.warn(`设备 ${deviceType} 需要校准`)
        }
      })
    }
  }
})