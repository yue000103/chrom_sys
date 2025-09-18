<template>
  <div class="pretreatment-panel">
    <div class="pretreatment-header">
      <h3>系统预处理</h3>
      <p>在开始实验前，需要进行系统预处理以确保实验结果的准确性</p>
    </div>

    <div class="pretreatment-steps">
      <div
        v-for="(step, index) in pretreatmentSteps"
        :key="step.id"
        class="step-item"
        :class="getStepClass(step.status)"
      >
        <div class="step-icon">
          <el-icon v-if="step.status === 'pending'"><Clock /></el-icon>
          <el-icon v-if="step.status === 'running'"><Loading /></el-icon>
          <el-icon v-if="step.status === 'completed'"><CircleCheckFilled /></el-icon>
          <el-icon v-if="step.status === 'skipped'"><RemoveFilled /></el-icon>
        </div>

        <div class="step-content">
          <div class="step-header">
            <h4>{{ step.name }}</h4>
            <div class="step-controls">
              <el-switch
                v-model="step.enabled"
                :disabled="step.status === 'running' || step.status === 'completed'"
                @change="updateStepConfig"
              />
              <span class="switch-label">{{ step.enabled ? '启用' : '跳过' }}</span>
            </div>
          </div>

          <p class="step-description">{{ step.description }}</p>

          <div v-if="step.enabled && step.parameters" class="step-parameters">
            <div
              v-for="param in step.parameters"
              :key="param.key"
              class="parameter-item"
            >
              <label>{{ param.label }}:</label>
              <el-input-number
                v-if="param.type === 'number'"
                v-model="param.value"
                :min="param.min"
                :max="param.max"
                :step="param.step"
                :disabled="step.status === 'running' || step.status === 'completed'"
              />
              <span class="parameter-unit">{{ param.unit }}</span>
            </div>
          </div>

          <div v-if="step.status === 'running'" class="step-progress">
            <el-progress
              :percentage="step.progress"
              :status="step.progress === 100 ? 'success' : 'active'"
            />
            <div class="progress-info">
              <span>{{ step.currentAction }}</span>
              <span>{{ step.remainingTime }}</span>
            </div>
          </div>

          <div v-if="step.status === 'completed'" class="step-result">
            <el-tag type="success" size="small">
              <el-icon><CircleCheckFilled /></el-icon>
              完成时间: {{ step.completedTime }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="pretreatment-summary">
      <el-card>
        <template #header>
          <span>预处理总览</span>
        </template>

        <div class="summary-content">
          <div class="summary-stats">
            <div class="stat-item">
              <span class="stat-label">总步骤:</span>
              <span class="stat-value">{{ totalSteps }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已启用:</span>
              <span class="stat-value">{{ enabledSteps }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">预计时间:</span>
              <span class="stat-value">{{ estimatedTime }} 分钟</span>
            </div>
          </div>

          <div class="summary-actions">
            <el-button
              v-if="!isRunning && !isCompleted"
              type="primary"
              size="large"
              @click="startPretreatment"
              :disabled="enabledSteps === 0"
            >
              <el-icon><VideoPlay /></el-icon>
              开始预处理
            </el-button>

            <el-button
              v-if="isRunning"
              type="warning"
              size="large"
              @click="pausePretreatment"
            >
              <el-icon><VideoPause /></el-icon>
              暂停预处理
            </el-button>

            <el-button
              v-if="isRunning"
              type="danger"
              size="large"
              @click="stopPretreatment"
            >
              <el-icon><VideoStop /></el-icon>
              停止预处理
            </el-button>

            <el-button
              v-if="isCompleted"
              type="success"
              size="large"
              @click="completePretreatment"
            >
              <el-icon><CircleCheckFilled /></el-icon>
              完成预处理
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'PretreatmentPanel',
  emits: ['start', 'complete'],
  setup(props, { emit }) {
    const pretreatmentSteps = ref([
      {
        id: 1,
        name: '系统吹扫',
        description: '清除管路中的空气和杂质，确保系统密闭性',
        enabled: true,
        status: 'pending',
        progress: 0,
        currentAction: '',
        remainingTime: '',
        completedTime: '',
        parameters: [
          {
            key: 'pressure',
            label: '吹扫压力',
            type: 'number',
            value: 50,
            min: 10,
            max: 100,
            step: 5,
            unit: 'bar'
          },
          {
            key: 'duration',
            label: '吹扫时间',
            type: 'number',
            value: 3,
            min: 1,
            max: 10,
            step: 1,
            unit: '分钟'
          }
        ]
      },
      {
        id: 2,
        name: '柱子吹扫',
        description: '清除色谱柱中的残留物质，准备新的分离环境',
        enabled: true,
        status: 'pending',
        progress: 0,
        currentAction: '',
        remainingTime: '',
        completedTime: '',
        parameters: [
          {
            key: 'flowRate',
            label: '吹扫流速',
            type: 'number',
            value: 2.0,
            min: 0.5,
            max: 5.0,
            step: 0.1,
            unit: 'mL/min'
          },
          {
            key: 'duration',
            label: '吹扫时间',
            type: 'number',
            value: 5,
            min: 1,
            max: 15,
            step: 1,
            unit: '分钟'
          }
        ]
      },
      {
        id: 3,
        name: '柱平衡',
        description: '使用起始流动相平衡色谱柱，建立稳定的基线',
        enabled: true,
        status: 'pending',
        progress: 0,
        currentAction: '',
        remainingTime: '',
        completedTime: '',
        parameters: [
          {
            key: 'solutionA',
            label: '原液A比例',
            type: 'number',
            value: 80,
            min: 0,
            max: 100,
            step: 5,
            unit: '%'
          },
          {
            key: 'solutionB',
            label: '原液B比例',
            type: 'number',
            value: 20,
            min: 0,
            max: 100,
            step: 5,
            unit: '%'
          },
          {
            key: 'flowRate',
            label: '平衡流速',
            type: 'number',
            value: 1.0,
            min: 0.1,
            max: 3.0,
            step: 0.1,
            unit: 'mL/min'
          },
          {
            key: 'duration',
            label: '平衡时间',
            type: 'number',
            value: 5,
            min: 2,
            max: 20,
            step: 1,
            unit: '分钟'
          }
        ]
      },
      {
        id: 4,
        name: '基线稳定',
        description: '等待检测器基线稳定，确保检测精度',
        enabled: true,
        status: 'pending',
        progress: 0,
        currentAction: '',
        remainingTime: '',
        completedTime: '',
        parameters: [
          {
            key: 'stabilityThreshold',
            label: '稳定阈值',
            type: 'number',
            value: 0.005,
            min: 0.001,
            max: 0.01,
            step: 0.001,
            unit: 'AU'
          },
          {
            key: 'checkInterval',
            label: '检查间隔',
            type: 'number',
            value: 30,
            min: 10,
            max: 60,
            step: 10,
            unit: '秒'
          }
        ]
      }
    ])

    const totalSteps = computed(() => pretreatmentSteps.value.length)

    const enabledSteps = computed(() =>
      pretreatmentSteps.value.filter(step => step.enabled).length
    )

    const estimatedTime = computed(() => {
      return pretreatmentSteps.value
        .filter(step => step.enabled)
        .reduce((total, step) => {
          const durationParam = step.parameters?.find(p => p.key === 'duration')
          return total + (durationParam ? durationParam.value : 2)
        }, 0)
    })

    const isRunning = computed(() =>
      pretreatmentSteps.value.some(step => step.status === 'running')
    )

    const isCompleted = computed(() =>
      pretreatmentSteps.value.filter(step => step.enabled)
        .every(step => step.status === 'completed')
    )

    const getStepClass = (status) => {
      return `step-${status}`
    }

    const updateStepConfig = () => {
      // 更新步骤配置
      console.log('更新预处理配置')
    }

    const startPretreatment = () => {
      console.log('开始预处理')
      emit('start')

      // 模拟预处理过程
      const enabledStepsList = pretreatmentSteps.value.filter(step => step.enabled)
      executeStepsSequentially(enabledStepsList, 0)
    }

    const executeStepsSequentially = (steps, currentIndex) => {
      if (currentIndex >= steps.length) {
        // 所有步骤完成
        return
      }

      const step = steps[currentIndex]
      step.status = 'running'
      step.progress = 0
      step.currentAction = `正在执行${step.name}...`

      const durationParam = step.parameters?.find(p => p.key === 'duration')
      const duration = durationParam ? durationParam.value * 60 * 1000 : 120000 // 默认2分钟

      const progressInterval = setInterval(() => {
        step.progress += 2
        step.remainingTime = `剩余 ${Math.ceil((100 - step.progress) * duration / 100 / 1000)} 秒`

        if (step.progress >= 100) {
          clearInterval(progressInterval)
          step.status = 'completed'
          step.completedTime = new Date().toLocaleTimeString()
          step.currentAction = ''
          step.remainingTime = ''

          // 执行下一步
          setTimeout(() => {
            executeStepsSequentially(steps, currentIndex + 1)
          }, 1000)
        }
      }, duration / 50) // 50步完成
    }

    const pausePretreatment = () => {
      console.log('暂停预处理')
    }

    const stopPretreatment = () => {
      console.log('停止预处理')
      pretreatmentSteps.value.forEach(step => {
        if (step.status === 'running') {
          step.status = 'pending'
          step.progress = 0
          step.currentAction = ''
          step.remainingTime = ''
        }
      })
    }

    const completePretreatment = () => {
      console.log('预处理完成')
      emit('complete')
    }

    return {
      pretreatmentSteps,
      totalSteps,
      enabledSteps,
      estimatedTime,
      isRunning,
      isCompleted,
      getStepClass,
      updateStepConfig,
      startPretreatment,
      pausePretreatment,
      stopPretreatment,
      completePretreatment
    }
  }
}
</script>

<style scoped>
.pretreatment-panel {
  padding: 20px;
}

.pretreatment-header {
  margin-bottom: 30px;
  text-align: center;
}

.pretreatment-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.pretreatment-header p {
  color: #666;
  margin: 0;
}

.pretreatment-steps {
  margin-bottom: 30px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.step-item.step-pending {
  background-color: #fafafa;
}

.step-item.step-running {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.step-item.step-completed {
  border-color: #67c23a;
  background-color: #f6ffed;
}

.step-item.step-skipped {
  border-color: #909399;
  background-color: #f4f4f5;
  opacity: 0.7;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}

.step-pending .step-icon {
  background-color: #909399;
}

.step-running .step-icon {
  background-color: #409eff;
}

.step-completed .step-icon {
  background-color: #67c23a;
}

.step-skipped .step-icon {
  background-color: #c0c4cc;
}

.step-content {
  flex: 1;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-header h4 {
  margin: 0;
  color: #333;
}

.step-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch-label {
  font-size: 14px;
  color: #666;
}

.step-description {
  color: #666;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.step-parameters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.parameter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.parameter-item label {
  min-width: 80px;
  font-size: 14px;
  color: #666;
}

.parameter-unit {
  font-size: 14px;
  color: #666;
}

.step-progress {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.step-result {
  margin-top: 8px;
}

.pretreatment-summary {
  margin-top: 30px;
}

.summary-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.summary-actions {
  display: flex;
  gap: 12px;
}
</style>