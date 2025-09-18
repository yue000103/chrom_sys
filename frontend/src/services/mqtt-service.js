
class MQTTService {
  constructor() {

     if (!window.mqtt) {
            throw new Error('MQTT库未加载，请确保CDN脚本已正确加载')
        }
    this.client = null
    this.isConnected = false
    this.subscriptions = new Map()
    this.statusCallbacks = []
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  async connect(options = {}) {
    const defaultOptions = {
      host: 'broker.emqx.io',
      port: 8084,
      protocol: 'wss',
      keepalive: 60,
      reconnectPeriod: 5000,
      connectTimeout: 30 * 1000,
      clean: true,
      rejectUnauthorized: false,
      brokerUrl : 'wss://broker.emqx.io:8084/mqtt',
    }

    const config = { ...defaultOptions, ...options }

    return new Promise((resolve, reject) => {
      try {
        this.client = window.mqtt.connect(defaultOptions.brokerUrl,{
                    clientId: 'vue_client_',
                    clean: true,
                    connectTimeout: 4000,
                    reconnectPeriod: 1000,
                })

        this.client.on('connect', () => {
          console.log('MQTT连接成功')
          this.isConnected = true
          this.reconnectAttempts = 0
          this.notifyStatusChange({ connected: true })
          resolve()
        })

        this.client.on('error', (error) => {
          console.error('MQTT连接错误:', error)
          this.isConnected = false
          this.notifyStatusChange({ connected: false, error })
          reject(error)
        })

        this.client.on('close', () => {
          console.log('MQTT连接关闭')
          this.isConnected = false
          this.notifyStatusChange({ connected: false })
        })

        this.client.on('reconnect', () => {
          this.reconnectAttempts++
          console.log(`MQTT重连中... (第${this.reconnectAttempts}次)`)

          if (this.reconnectAttempts > this.maxReconnectAttempts) {
            console.error('MQTT重连失败，超过最大重试次数')
            this.client.end()
          }
        })

        this.client.on('offline', () => {
          console.log('MQTT客户端离线')
          this.isConnected = false
          this.notifyStatusChange({ connected: false })
        })

        this.client.on('message', (topic, message) => {
          this.handleMessage(topic, message)
        })

      } catch (error) {
        console.error('创建MQTT客户端失败:', error)
        reject(error)
      }
    })
  }

  async subscribe(topic, callback) {
    if (!this.client || !this.isConnected) {
      throw new Error('MQTT客户端未连接')
    }

    return new Promise((resolve, reject) => {
      this.client.subscribe(topic, (error) => {
        if (error) {
          console.error(`订阅主题 ${topic} 失败:`, error)
          reject(error)
        } else {
          console.log(`成功订阅主题: ${topic}`)
          this.subscriptions.set(topic, callback)
          resolve()
        }
      })
    })
  }

  async unsubscribe(topic) {
    if (!this.client) {
      return
    }

    return new Promise((resolve, reject) => {
      this.client.unsubscribe(topic, (error) => {
        if (error) {
          console.error(`取消订阅主题 ${topic} 失败:`, error)
          reject(error)
        } else {
          console.log(`成功取消订阅主题: ${topic}`)
          this.subscriptions.delete(topic)
          resolve()
        }
      })
    })
  }

  async publish(topic, message, options = {}) {
    if (!this.client || !this.isConnected) {
      throw new Error('MQTT客户端未连接')
    }

    const defaultOptions = {
      qos: 0,
      retain: false
    }

    const publishOptions = { ...defaultOptions, ...options }

    return new Promise((resolve, reject) => {
      const payload = typeof message === 'string' ? message : JSON.stringify(message)

      this.client.publish(topic, payload, publishOptions, (error) => {
        if (error) {
          console.error(`发布消息到主题 ${topic} 失败:`, error)
          reject(error)
        } else {
          console.log(`成功发布消息到主题: ${topic}`)
          resolve()
        }
      })
    })
  }

  handleMessage(topic, message) {
    try {
      const callback = this.subscriptions.get(topic)
      if (callback) {
        let data
        try {
          data = JSON.parse(message.toString())
        } catch (e) {
          data = message.toString()
        }

        // 为开发文档中要求的数据格式进行特殊处理
        if (topic === 'data/random') {
          if (typeof data === 'object' && data.timestamp && data.value !== undefined) {
            callback({
              timestamp: data.timestamp,
              value: Number(data.value)
            })
          }
        } else {
          callback(data)
        }
      }
    } catch (error) {
      console.error('处理MQTT消息失败:', error)
    }
  }

  async disconnect() {
    if (this.client) {
      this.subscriptions.clear()
      this.client.end()
      this.client = null
      this.isConnected = false
      this.notifyStatusChange({ connected: false })
      console.log('MQTT客户端已断开')
    }
  }

  onStatusChange(callback) {
    this.statusCallbacks.push(callback)
  }

  notifyStatusChange(status) {
    this.statusCallbacks.forEach(callback => {
      try {
        callback(status)
      } catch (error) {
        console.error('状态回调执行失败:', error)
      }
    })
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts
    }
  }
}

// 创建单例实例
const mqttService = new MQTTService()

export default mqttService