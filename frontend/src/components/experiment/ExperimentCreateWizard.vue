<template>
  <div class="experiment-create-wizard">
    <el-steps :active="currentStep" align-center>
      <el-step title="基本信息" />
      <el-step title="方法选择" />
      <el-step title="参数配置" />
      <el-step title="确认创建" />
    </el-steps>

    <div class="wizard-content">
      <!-- 步骤1: 基本信息 -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>实验基本信息</h3>
        <el-form :model="experimentData" label-width="120px">
          <el-form-item label="实验名称" required>
            <el-input v-model="experimentData.name" placeholder="请输入实验名称" />
          </el-form-item>
          <el-form-item label="实验描述">
            <el-input
              v-model="experimentData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入实验描述"
            />
          </el-form-item>
          <el-form-item label="操作员">
            <el-input v-model="experimentData.operator" placeholder="操作员姓名" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2: 方法选择 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>选择分析方法</h3>
        <div class="method-selection">
          <el-radio-group v-model="experimentData.methodId" class="method-list">
            <el-radio
              v-for="method in availableMethods"
              :key="method.id"
              :label="method.id"
              class="method-radio"
            >
              <div class="method-card">
                <div class="method-header">
                  <h4>{{ method.name }}</h4>
                  <el-tag v-if="method.isFavorite" type="warning" size="small">常用</el-tag>
                </div>
                <p class="method-description">{{ method.description }}</p>
                <div class="method-params">
                  <span>流速: {{ method.flowRate }}mL/min</span>
                  <span>时间: {{ method.runTime }}min</span>
                  <span>波长: {{ method.wavelength }}nm</span>
                </div>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
      </div>

      <!-- 步骤3: 参数配置 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>实验参数配置</h3>
        <el-form :model="experimentData" label-width="140px">
          <el-form-item label="收集策略">
            <el-radio-group v-model="experimentData.collectionStrategy">
              <el-radio label="peak">峰驱动</el-radio>
              <el-radio label="volume">体积驱动</el-radio>
              <el-radio label="manual">手动收集</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="experimentData.collectionStrategy === 'volume'" label="收集体积 (mL)">
            <el-input-number v-model="experimentData.collectionVolume" :min="0.1" :max="50" :step="0.1" />
          </el-form-item>

          <el-form-item label="清洗体积 (mL)">
            <el-input-number v-model="experimentData.washVolume" :min="0" :max="20" :step="0.1" />
          </el-form-item>

          <el-form-item label="清洗次数">
            <el-input-number v-model="experimentData.washCycles" :min="0" :max="10" />
          </el-form-item>

          <el-form-item label="预计开始时间">
            <el-date-picker
              v-model="experimentData.scheduledTime"
              type="datetime"
              placeholder="选择开始时间"
              format="YYYY/MM/DD HH:mm"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>

          <el-form-item label="优先级">
            <el-radio-group v-model="experimentData.priority">
              <el-radio label="low">低</el-radio>
              <el-radio label="normal">正常</el-radio>
              <el-radio label="high">高</el-radio>
              <el-radio label="urgent">紧急</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤4: 确认创建 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>确认实验信息</h3>
        <div class="experiment-summary">
          <el-card>
            <h4>{{ experimentData.name }}</h4>
            <p>{{ experimentData.description }}</p>
            <el-divider />

            <div class="summary-section">
              <h5>基本信息</h5>
              <div class="summary-grid">
                <div class="summary-item">
                  <label>操作员:</label>
                  <span>{{ experimentData.operator }}</span>
                </div>
                <div class="summary-item">
                  <label>使用方法:</label>
                  <span>{{ getSelectedMethodName() }}</span>
                </div>
                <div class="summary-item">
                  <label>收集策略:</label>
                  <span>{{ getCollectionStrategyText() }}</span>
                </div>
                <div class="summary-item">
                  <label>优先级:</label>
                  <el-tag :type="getPriorityType()">{{ getPriorityText() }}</el-tag>
                </div>
              </div>
            </div>

            <div class="summary-section">
              <h5>参数设置</h5>
              <div class="summary-grid">
                <div class="summary-item" v-if="experimentData.collectionVolume">
                  <label>收集体积:</label>
                  <span>{{ experimentData.collectionVolume }} mL</span>
                </div>
                <div class="summary-item">
                  <label>清洗体积:</label>
                  <span>{{ experimentData.washVolume }} mL</span>
                </div>
                <div class="summary-item">
                  <label>清洗次数:</label>
                  <span>{{ experimentData.washCycles }} 次</span>
                </div>
                <div class="summary-item" v-if="experimentData.scheduledTime">
                  <label>预计开始:</label>
                  <span>{{ experimentData.scheduledTime }}</span>
                </div>
              </div>
            </div>

            <div class="summary-section">
              <h5>预计消耗</h5>
              <div class="summary-grid">
                <div class="summary-item">
                  <label>预计运行时间:</label>
                  <span>{{ estimatedRunTime }} 分钟</span>
                </div>
                <div class="summary-item">
                  <label>预计试管使用:</label>
                  <span>{{ estimatedTubes }} 支</span>
                </div>
                <div class="summary-item">
                  <label>预计溶剂消耗:</label>
                  <span>{{ estimatedSolvent }} mL</span>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <div class="wizard-footer">
      <el-button @click="previousStep" :disabled="currentStep === 0">上一步</el-button>
      <el-button v-if="currentStep < 3" type="primary" @click="nextStep">下一步</el-button>
      <el-button v-if="currentStep === 3" type="success" @click="saveExperiment">创建实验</el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ExperimentCreateWizard',
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    const currentStep = ref(0)
    const experimentData = ref({
      name: `实验-${new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '-')}`,
      description: '',
      operator: '当前用户',
      methodId: null,
      collectionStrategy: 'peak',
      collectionVolume: 5.0,
      washVolume: 5.0,
      washCycles: 1,
      scheduledTime: null,
      priority: 'normal'
    })

    // 可用方法列表
    const availableMethods = ref([
      {
        id: 1,
        name: '标准分析方法-01',
        description: '用于蛋白质分离的标准方法',
        isFavorite: true,
        flowRate: 1.0,
        runTime: 30,
        wavelength: 254
      },
      {
        id: 2,
        name: '快速检测方法',
        description: '用于快速样品筛选',
        isFavorite: false,
        flowRate: 1.5,
        runTime: 15,
        wavelength: 280
      },
      {
        id: 3,
        name: '高分辨分离方法',
        description: '用于复杂样品的高分辨分离',
        isFavorite: true,
        flowRate: 0.8,
        runTime: 60,
        wavelength: 254
      }
    ])

    const selectedMethod = computed(() => {
      return availableMethods.value.find(method => method.id === experimentData.value.methodId)
    })

    const estimatedRunTime = computed(() => {
      if (selectedMethod.value) {
        const baseTime = selectedMethod.value.runTime
        const washTime = experimentData.value.washCycles * 2 // 假设每次清洗2分钟
        return baseTime + washTime
      }
      return 0
    })

    const estimatedTubes = computed(() => {
      if (selectedMethod.value) {
        if (experimentData.value.collectionStrategy === 'volume') {
          const totalVolume = selectedMethod.value.flowRate * selectedMethod.value.runTime
          return Math.ceil(totalVolume / experimentData.value.collectionVolume)
        }
        return Math.ceil(selectedMethod.value.runTime / 5) // 假设平均每5分钟一个峰
      }
      return 0
    })

    const estimatedSolvent = computed(() => {
      if (selectedMethod.value) {
        const runVolume = selectedMethod.value.flowRate * selectedMethod.value.runTime
        const washVolume = experimentData.value.washVolume * experimentData.value.washCycles
        return Math.round((runVolume + washVolume) * 10) / 10
      }
      return 0
    })

    const nextStep = () => {
      if (currentStep.value < 3) {
        currentStep.value++
      }
    }

    const previousStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }

    const getSelectedMethodName = () => {
      return selectedMethod.value ? selectedMethod.value.name : '未选择'
    }

    const getCollectionStrategyText = () => {
      const strategyMap = {
        peak: '峰驱动',
        volume: '体积驱动',
        manual: '手动收集'
      }
      return strategyMap[experimentData.value.collectionStrategy]
    }

    const getPriorityType = () => {
      const typeMap = {
        low: 'info',
        normal: 'success',
        high: 'warning',
        urgent: 'danger'
      }
      return typeMap[experimentData.value.priority]
    }

    const getPriorityText = () => {
      const textMap = {
        low: '低',
        normal: '正常',
        high: '高',
        urgent: '紧急'
      }
      return textMap[experimentData.value.priority]
    }

    const saveExperiment = () => {
      const experimentToSave = {
        ...experimentData.value,
        method: selectedMethod.value?.name || '',
        estimatedTime: `${estimatedRunTime.value}分钟`
      }
      emit('save', experimentToSave)
    }

    return {
      currentStep,
      experimentData,
      availableMethods,
      selectedMethod,
      estimatedRunTime,
      estimatedTubes,
      estimatedSolvent,
      nextStep,
      previousStep,
      getSelectedMethodName,
      getCollectionStrategyText,
      getPriorityType,
      getPriorityText,
      saveExperiment
    }
  }
}
</script>

<style scoped>
.experiment-create-wizard {
  padding: 20px;
}

.wizard-content {
  margin: 30px 0;
  min-height: 500px;
}

.step-content {
  padding: 20px;
}

.step-content h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.method-selection {
  max-height: 400px;
  overflow-y: auto;
}

.method-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.method-radio {
  width: 100%;
  margin-right: 0;
}

.method-card {
  width: 100%;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.method-card:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.method-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.method-header h4 {
  margin: 0;
  color: #333;
}

.method-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.method-params {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #888;
}

.experiment-summary {
  max-height: 500px;
  overflow-y: auto;
}

.summary-section {
  margin-bottom: 20px;
}

.summary-section h5 {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 14px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 4px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-item label {
  color: #666;
  font-weight: 500;
}

.wizard-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>