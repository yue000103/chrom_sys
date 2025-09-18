<template>
  <el-card class="system-status">
    <template #header>
      <span>系统状态</span>
    </template>
    <div class="status-grid">
      <div class="status-item">
        <span class="label">CPU使用率:</span>
        <el-progress :percentage="cpuUsage" />
      </div>
      <div class="status-item">
        <span class="label">内存使用率:</span>
        <el-progress :percentage="memoryUsage" />
      </div>
    </div>
  </el-card>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'SystemStatus',
  setup() {
    const cpuUsage = ref(0)
    const memoryUsage = ref(0)
    let timer = null

    const updateStatus = () => {
      cpuUsage.value = Math.random() * 100
      memoryUsage.value = Math.random() * 100
    }

    onMounted(() => {
      timer = setInterval(updateStatus, 2000)
    })

    onUnmounted(() => {
      if (timer) clearInterval(timer)
    })

    return {
      cpuUsage,
      memoryUsage
    }
  }
}
</script>

<style scoped>
.status-item {
  margin-bottom: 15px;
}
.label {
  display: inline-block;
  width: 100px;
  margin-bottom: 5px;
}
</style>