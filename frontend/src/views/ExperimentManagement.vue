<template>
  <div class="experiment-management">
    <!-- 实验状态概览 -->
    <el-row :gutter="20" class="status-overview">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-icon class="status-icon running"><VideoPlay /></el-icon>
            <div class="status-info">
              <h3>当前实验</h3>
              <p>{{ currentExperiment ? currentExperiment.name : '无' }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-icon class="status-icon pending"><Clock /></el-icon>
            <div class="status-info">
              <h3>排队实验</h3>
              <p>{{ queuedExperiments.length }} 个</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-icon class="status-icon progress"><TrendCharts /></el-icon>
            <div class="status-info">
              <h3>进度</h3>
              <p>{{ currentProgress }}%</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-icon class="status-icon time"><Timer /></el-icon>
            <div class="status-info">
              <h3>剩余时间</h3>
              <p>{{ remainingTime }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 左侧：实验创建和队列 -->
      <el-col :span="12">
        <!-- 实验创建 -->
        <el-card class="mb-3">
          <template #header>
            <div class="card-header">
              <span>创建新实验</span>
              <el-button type="primary" @click="showCreateWizard = true">
                <el-icon><Plus /></el-icon>
                创建实验
              </el-button>
            </div>
          </template>

          <div class="quick-create">
            <h4>快速创建</h4>
            <div class="quick-methods">
              <el-button
                v-for="method in quickMethods"
                :key="method.id"
                class="quick-method-btn"
                @click="createQuickExperiment(method)"
              >
                {{ method.name }}
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 实验队列 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实验队列</span>
              <el-button @click="clearQueue" :disabled="queuedExperiments.length === 0">
                清空队列
              </el-button>
            </div>
          </template>

          <div class="experiment-queue">
            <div v-if="queuedExperiments.length === 0" class="empty-queue">
              <el-empty description="暂无排队实验" />
            </div>
            <div v-else>
              <div
                v-for="(experiment, index) in queuedExperiments"
                :key="experiment.id"
                class="queue-item"
                :class="{ 'queue-active': index === 0 }"
              >
                <div class="queue-info">
                  <h4>{{ experiment.name }}</h4>
                  <p>方法: {{ experiment.method }}</p>
                  <p>预计时间: {{ experiment.estimatedTime }}</p>
                </div>
                <div class="queue-actions">
                  <el-button size="small" @click="editQueuedExperiment(experiment)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" @click="moveUp(index)" :disabled="index === 0">
                    <el-icon><Top /></el-icon>
                  </el-button>
                  <el-button size="small" @click="moveDown(index)" :disabled="index === queuedExperiments.length - 1">
                    <el-icon><Bottom /></el-icon>
                  </el-button>
                  <el-button size="small" type="danger" @click="removeFromQueue(experiment)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：当前实验控制 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>实验控制</span>
          </template>

          <div v-if="currentExperiment" class="experiment-control">
            <!-- 实验信息 -->
            <div class="experiment-info">
              <h3>{{ currentExperiment.name }}</h3>
              <p>方法: {{ currentExperiment.method }}</p>
              <p>状态:
                <el-tag :type="getStatusType(currentExperiment.status)">
                  {{ getStatusText(currentExperiment.status) }}
                </el-tag>
              </p>
            </div>

            <!-- 进度显示 -->
            <div class="progress-section">
              <el-progress
                :percentage="currentProgress"
                :status="progressStatus"
                stroke-width="12"
              />
              <div class="time-info">
                <span>已运行: {{ elapsedTime }}</span>
                <span>剩余: {{ remainingTime }}</span>
              </div>
            </div>

            <!-- 当前状态 -->
            <div class="current-status">
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="status-item-small">
                    <label>当前试管:</label>
                    <span class="status-value">{{ currentExperiment.currentTube }}</span>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="status-item-small">
                    <label>收集模式:</label>
                    <span class="status-value">{{ currentExperiment.collectionMode }}</span>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="status-item-small">
                    <label>检测峰数:</label>
                    <span class="status-value">{{ currentExperiment.peakCount }}</span>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="status-item-small">
                    <label>当前压力:</label>
                    <span class="status-value pressure" :class="getPressureClass(currentExperiment.currentPressure)">
                      {{ currentExperiment.currentPressure }} bar
                    </span>
                  </div>
                </el-col>
              </el-row>
            </div>

            <!-- 控制按钮 -->
            <div class="control-buttons">
              <el-button
                v-if="currentExperiment.status === 'running'"
                type="warning"
                size="large"
                @click="pauseExperiment"
              >
                <el-icon><VideoPause /></el-icon>
                暂停实验
              </el-button>
              <el-button
                v-if="currentExperiment.status === 'paused'"
                type="success"
                size="large"
                @click="resumeExperiment"
              >
                <el-icon><VideoPlay /></el-icon>
                继续实验
              </el-button>
              <el-button
                type="danger"
                size="large"
                @click="stopExperiment"
                :disabled="currentExperiment.status === 'stopped'"
              >
                <el-icon><CircleClose /></el-icon>
                停止实验
              </el-button>
            </div>

            <!-- 实时控制面板 -->
            <el-divider content-position="left">实时控制</el-divider>
            <div class="realtime-controls">
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="control-group">
                    <label>手动切换试管:</label>
                    <el-select v-model="selectedTube" placeholder="选择试管">
                      <el-option
                        v-for="tube in availableTubes"
                        :key="tube"
                        :label="`试管 ${tube}`"
                        :value="tube"
                      />
                    </el-select>
                    <el-button @click="switchTube" :disabled="!selectedTube">切换</el-button>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="control-group">
                    <label>收集模式:</label>
                    <el-switch
                      v-model="isWasteMode"
                      active-text="废液"
                      inactive-text="收集"
                      @change="switchCollectionMode"
                    />
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>

          <div v-else class="no-experiment">
            <el-empty description="当前无运行实验">
              <el-button type="primary" @click="startNextExperiment" :disabled="queuedExperiments.length === 0">
                开始下一个实验
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实验创建向导对话框 -->
    <el-dialog
      v-model="showCreateWizard"
      title="创建新实验"
      width="80%"
      :before-close="handleCloseWizard"
    >
      <ExperimentCreateWizard
        @save="handleSaveExperiment"
        @cancel="showCreateWizard = false"
      />
    </el-dialog>

    <!-- 预处理对话框 -->
    <el-dialog
      v-model="showPretreatment"
      title="系统预处理"
      width="60%"
    >
      <PretreatmentPanel
        @start="handleStartPretreatment"
        @complete="handlePretreatmentComplete"
      />
    </el-dialog>

    <!-- 实验结束处理对话框 -->
    <el-dialog
      v-model="showEndProcessing"
      title="实验结束处理"
      width="70%"
    >
      <ExperimentEndProcessing
        :experiment="currentExperiment"
        @save="handleSaveExperimentData"
        @merge="handleMergeCollections"
        @clean="handleCleanTubes"
      />
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import ExperimentCreateWizard from '../components/experiment/ExperimentCreateWizard.vue'
import PretreatmentPanel from '../components/experiment/PretreatmentPanel.vue'
import ExperimentEndProcessing from '../components/experiment/ExperimentEndProcessing.vue'

export default {
  name: 'ExperimentManagement',
  components: {
    ExperimentCreateWizard,
    PretreatmentPanel,
    ExperimentEndProcessing
  },
  setup() {
    const showCreateWizard = ref(false)
    const showPretreatment = ref(false)
    const showEndProcessing = ref(false)
    const selectedTube = ref('')
    const isWasteMode = ref(false)

    // 当前实验
    const currentExperiment = ref({
      id: 1,
      name: '蛋白质分离实验-001',
      method: '标准分析方法-01',
      status: 'running',
      startTime: new Date(Date.now() - 15 * 60 * 1000), // 15分钟前开始
      estimatedDuration: 45, // 预计45分钟
      currentTube: 5,
      collectionMode: '峰驱动',
      peakCount: 3,
      currentPressure: 185
    })

    // 排队实验
    const queuedExperiments = ref([
      {
        id: 2,
        name: '快速筛选实验-002',
        method: '快速检测方法',
        estimatedTime: '15分钟'
      },
      {
        id: 3,
        name: '复杂样品分析-003',
        method: '高分辨分离方法',
        estimatedTime: '60分钟'
      }
    ])

    // 快速方法
    const quickMethods = ref([
      { id: 1, name: '标准分析' },
      { id: 2, name: '快速检测' },
      { id: 3, name: '高分辨分离' }
    ])

    // 可用试管
    const availableTubes = computed(() => {
      return Array.from({ length: 40 }, (_, i) => i + 1)
    })

    // 当前进度
    const currentProgress = computed(() => {
      if (!currentExperiment.value) return 0
      const elapsed = Date.now() - currentExperiment.value.startTime.getTime()
      const total = currentExperiment.value.estimatedDuration * 60 * 1000
      return Math.min(Math.round((elapsed / total) * 100), 100)
    })

    // 进度状态
    const progressStatus = computed(() => {
      if (currentExperiment.value?.status === 'paused') return 'warning'
      if (currentExperiment.value?.status === 'error') return 'exception'
      return 'success'
    })

    // 已运行时间
    const elapsedTime = computed(() => {
      if (!currentExperiment.value) return '0分钟'
      const elapsed = Date.now() - currentExperiment.value.startTime.getTime()
      const minutes = Math.floor(elapsed / (60 * 1000))
      return `${minutes}分钟`
    })

    // 剩余时间
    const remainingTime = computed(() => {
      if (!currentExperiment.value) return '0分钟'
      const elapsed = Date.now() - currentExperiment.value.startTime.getTime()
      const total = currentExperiment.value.estimatedDuration * 60 * 1000
      const remaining = Math.max(0, total - elapsed)
      const minutes = Math.floor(remaining / (60 * 1000))
      return `${minutes}分钟`
    })

    const getStatusType = (status) => {
      const statusMap = {
        running: 'success',
        paused: 'warning',
        stopped: 'info',
        error: 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        running: '运行中',
        paused: '已暂停',
        stopped: '已停止',
        error: '异常'
      }
      return statusMap[status] || status
    }

    const getPressureClass = (pressure) => {
      if (pressure > 350) return 'danger'
      if (pressure > 200) return 'warning'
      return 'normal'
    }

    const createQuickExperiment = (method) => {
      console.log('快速创建实验:', method.name)
    }

    const clearQueue = () => {
      queuedExperiments.value = []
    }

    const editQueuedExperiment = (experiment) => {
      console.log('编辑排队实验:', experiment.name)
    }

    const moveUp = (index) => {
      if (index > 0) {
        const item = queuedExperiments.value.splice(index, 1)[0]
        queuedExperiments.value.splice(index - 1, 0, item)
      }
    }

    const moveDown = (index) => {
      if (index < queuedExperiments.value.length - 1) {
        const item = queuedExperiments.value.splice(index, 1)[0]
        queuedExperiments.value.splice(index + 1, 0, item)
      }
    }

    const removeFromQueue = (experiment) => {
      const index = queuedExperiments.value.findIndex(exp => exp.id === experiment.id)
      if (index > -1) {
        queuedExperiments.value.splice(index, 1)
      }
    }

    const pauseExperiment = () => {
      currentExperiment.value.status = 'paused'
      console.log('暂停实验')
    }

    const resumeExperiment = () => {
      currentExperiment.value.status = 'running'
      console.log('继续实验')
    }

    const stopExperiment = () => {
      currentExperiment.value.status = 'stopped'
      showEndProcessing.value = true
      console.log('停止实验')
    }

    const switchTube = () => {
      currentExperiment.value.currentTube = selectedTube.value
      console.log('切换到试管:', selectedTube.value)
    }

    const switchCollectionMode = (value) => {
      currentExperiment.value.collectionMode = value ? '废液' : '收集'
      console.log('切换收集模式:', currentExperiment.value.collectionMode)
    }

    const startNextExperiment = () => {
      if (queuedExperiments.value.length > 0) {
        currentExperiment.value = {
          ...queuedExperiments.value[0],
          status: 'running',
          startTime: new Date(),
          currentTube: 1,
          collectionMode: '峰驱动',
          peakCount: 0,
          currentPressure: 120
        }
        queuedExperiments.value.shift()
        showPretreatment.value = true
      }
    }

    const handleSaveExperiment = (experimentData) => {
      queuedExperiments.value.push({
        id: Date.now(),
        name: experimentData.name,
        method: experimentData.method,
        estimatedTime: experimentData.estimatedTime
      })
      showCreateWizard.value = false
      console.log('保存实验到队列:', experimentData)
    }

    const handleCloseWizard = (done) => {
      done()
    }

    const handleStartPretreatment = () => {
      console.log('开始预处理')
    }

    const handlePretreatmentComplete = () => {
      showPretreatment.value = false
      console.log('预处理完成，开始实验')
    }

    const handleSaveExperimentData = (data) => {
      console.log('保存实验数据:', data)
      showEndProcessing.value = false
      currentExperiment.value = null
    }

    const handleMergeCollections = (mergeData) => {
      console.log('合并收集:', mergeData)
    }

    const handleCleanTubes = (cleanData) => {
      console.log('清洗试管:', cleanData)
    }

    return {
      showCreateWizard,
      showPretreatment,
      showEndProcessing,
      selectedTube,
      isWasteMode,
      currentExperiment,
      queuedExperiments,
      quickMethods,
      availableTubes,
      currentProgress,
      progressStatus,
      elapsedTime,
      remainingTime,
      getStatusType,
      getStatusText,
      getPressureClass,
      createQuickExperiment,
      clearQueue,
      editQueuedExperiment,
      moveUp,
      moveDown,
      removeFromQueue,
      pauseExperiment,
      resumeExperiment,
      stopExperiment,
      switchTube,
      switchCollectionMode,
      startNextExperiment,
      handleSaveExperiment,
      handleCloseWizard,
      handleStartPretreatment,
      handlePretreatmentComplete,
      handleSaveExperimentData,
      handleMergeCollections,
      handleCleanTubes
    }
  }
}
</script>

<style scoped>
.experiment-management {
  padding: 20px;
}

.status-overview {
  margin-bottom: 20px;
}

.status-card {
  height: 100px;
}

.status-item {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-icon {
  font-size: 32px;
  margin-right: 16px;
}

.status-icon.running {
  color: #67c23a;
}

.status-icon.pending {
  color: #e6a23c;
}

.status-icon.progress {
  color: #409eff;
}

.status-icon.time {
  color: #909399;
}

.status-info h3 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #666;
}

.status-info p {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.mb-3 {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-create {
  padding: 16px;
}

.quick-create h4 {
  margin: 0 0 12px 0;
  color: #666;
}

.quick-methods {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-method-btn {
  flex: 1;
  min-width: 120px;
}

.experiment-queue {
  min-height: 200px;
}

.empty-queue {
  padding: 40px 0;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.queue-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.queue-item.queue-active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.queue-info h4 {
  margin: 0 0 4px 0;
  color: #333;
}

.queue-info p {
  margin: 2px 0;
  font-size: 14px;
  color: #666;
}

.queue-actions {
  display: flex;
  gap: 4px;
}

.experiment-control {
  padding: 16px;
}

.experiment-info {
  margin-bottom: 20px;
}

.experiment-info h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.experiment-info p {
  margin: 4px 0;
  color: #666;
}

.progress-section {
  margin-bottom: 20px;
}

.time-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.current-status {
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.status-item-small {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.status-item-small label {
  font-size: 14px;
  color: #666;
}

.status-value {
  font-weight: bold;
  color: #333;
}

.status-value.pressure.normal {
  color: #67c23a;
}

.status-value.pressure.warning {
  color: #e6a23c;
}

.status-value.pressure.danger {
  color: #f56c6c;
}

.control-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.control-buttons .el-button {
  flex: 1;
}

.realtime-controls {
  margin-top: 16px;
}

.control-group {
  margin-bottom: 12px;
}

.control-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  color: #666;
}

.control-group .el-select {
  width: 120px;
  margin-right: 8px;
}

.no-experiment {
  padding: 40px 0;
  text-align: center;
}
</style>