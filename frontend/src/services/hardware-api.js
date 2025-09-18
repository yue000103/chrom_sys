/**
 * 硬件控制API服务
 */
import axios from 'axios'
// API基础URL - 注意后端运行在8008端口
const API_BASE_URL = 'http://localhost:8008/api/hardware'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 可以在这里添加token等认证信息
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    if (error.response) {
      // 服务器返回错误状态码
      const message = error.response.data?.detail || error.response.statusText
      return Promise.reject(new Error(message))
    } else if (error.request) {
      // 请求已发送但没有收到响应
      return Promise.reject(new Error('网络连接失败，请检查服务器是否运行'))
    } else {
      // 其他错误
      return Promise.reject(error)
    }
  }
)

/**
 * 硬件API接口
 */
export const hardwareAPI = {
  /**
   * 设置Mock模式
   * @param {Object} data - { mock: boolean, device_id?: string }
   * @returns {Promise}
   */
  setMockMode(data) {
    return apiClient.post('/mock-mode', data)
  },

  /**
   * 获取Mock模式状态
   * @param {string} deviceId - 可选，设备ID
   * @returns {Promise}
   */
  getMockMode(deviceId = null) {
    const params = deviceId ? { device_id: deviceId } : {}
    return apiClient.get('/mock-mode', { params })
  },

  /**
   * 获取所有设备状态
   * @returns {Promise}
   */
  getDevicesStatus() {
    return apiClient.get('/devices-status')
  },

  /**
   * 重置所有设备为联机模式
   * @returns {Promise}
   */
  resetMockMode() {
    return apiClient.post('/reset-mock-mode')
  }
}

// 设备列表常量
export const DEVICES = {
  // 主机模块设备
  HOST_DEVICES: [
    { id: 'relay_controller', name: '继电器控制器', type: 'host' },
    { id: 'pressure_sensor_ttyAMA0', name: '压力传感器 (ttyAMA0)', type: 'host' },
    { id: 'detector_ttyAMA3', name: '检测器 (ttyAMA3)', type: 'host' },
    { id: 'pump_controller_ttyAMA2', name: '高压泵控制器 (ttyAMA2)', type: 'host' },
    { id: 'bubble_sensor_host', name: '气泡传感器 (主机)', type: 'host' }
  ],
  // 收集模块设备
  COLLECT_DEVICES: [
    { id: 'led_controller', name: 'LED控制器', type: 'collect' },
    { id: 'valve_controller', name: '阀门控制器', type: 'collect' },
    { id: 'bubble_sensor_collect', name: '气泡传感器 (收集)', type: 'collect' },
    { id: 'multi_valve_controller', name: '多向阀控制器', type: 'collect' },
    { id: 'spray_pump_controller', name: '隔膜泵控制器', type: 'collect' }
  ]
}

// 获取所有设备列表
export const getAllDevices = () => {
  return [...DEVICES.HOST_DEVICES, ...DEVICES.COLLECT_DEVICES]
}

// 根据ID获取设备信息
export const getDeviceById = (deviceId) => {
  return getAllDevices().find(device => device.id === deviceId)
}

export default hardwareAPI