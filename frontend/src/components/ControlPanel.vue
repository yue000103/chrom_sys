<template>
  <el-card class="control-panel">
    <template #header>
      <span>控制面板</span>
    </template>
    <div class="button-group">
      <el-button
        type="success"
        @click="startData"
        :disabled="isRunning"
        icon="VideoPlay"
      >
        开始
      </el-button>
      <el-button
        type="warning"
        @click="pauseData"
        :disabled="!isRunning || isPaused"
        icon="VideoPause"
      >
        暂停
      </el-button>
      <el-button
        type="primary"
        @click="resumeData"
        :disabled="!isPaused"
        icon="VideoPlay"
      >
        继续
      </el-button>
      <el-button
        type="danger"
        @click="stopData"
        :disabled="!isRunning"
        icon="VideoStop"
      >
        终止
      </el-button>
    </div>
    <div class="status-info">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="运行状态">
          <el-tag :type="statusType">{{ statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="MQTT连接">
          <el-tag :type="mqttConnected.value ? 'success' : 'danger'">
            {{ mqttConnected.value ? '已连接' : '未连接' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据接收数量">
          {{ dataCount }}
        </el-descriptions-item>
        <el-descriptions-item label="最后更新时间">
          {{ lastUpdateTime }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </el-card>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRealtimeDataStore } from '../store/modules/realtime-data'
import mqttService from '../services/mqtt-service'

export default {
  name: 'ControlPanel',
  setup() {
    const store = useRealtimeDataStore()

    const isRunning = ref(false)
    const isPaused = ref(false)
    const mqttConnected = ref(false)
    const dataCount = ref(0)
    const lastUpdateTime = ref('')

    const statusType = computed(() => {
      if (!isRunning.value) return 'info'
      if (isPaused.value) return 'warning'
      return 'success'
    })

    const statusText = computed(() => {
      if (!isRunning.value) return '已停止'
      if (isPaused.value) return '已暂停'
      return '运行中'
    })

    const startData = async () => {
      try {
        store.clearData()
        dataCount.value = 0
        lastUpdateTime.value = ''

        if (!mqttConnected.value) {
          await mqttService.connect()
          await mqttService.subscribe('data/random', (data) => {
            if (isRunning.value && !isPaused.value) {
              store.addDataPoint(data)
              dataCount.value++
              lastUpdateTime.value = new Date().toLocaleTimeString()
            }
          })
          mqttConnected.value = true
        }
        isRunning.value = true
        isPaused.value = false
      } catch (error) {
        console.error('启动失败:', error)
      }
    }

    const pauseData = () => {
      isPaused.value = true
    }

    const resumeData = () => {
      isPaused.value = false
    }

    const stopData = async () => {
      await mqttService.disconnect()
      isRunning.value = false
      isPaused.value = false
      mqttConnected.value = false
    }

    onMounted(() => {
      // 监听MQTT连接状态
      mqttService.onStatusChange((status) => {
        mqttConnected.value = status.connected
      })
    })

    onUnmounted(() => {
      mqttService.disconnect()
    })

    return {
      isRunning,
      isPaused,
      mqttConnected,
      dataCount,
      lastUpdateTime,
      statusType,
      statusText,
      startData,
      pauseData,
      resumeData,
      stopData
    }
  }
}
</script>

<style scoped>
.control-panel {
  margin-top: 20px;
}

.button-group {
  margin-bottom: 20px;
}

.button-group .el-button {
  margin-right: 10px;
}

.status-info {
  margin-top: 20px;
}
</style>