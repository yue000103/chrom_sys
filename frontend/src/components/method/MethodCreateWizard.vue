<template>
  <div class="method-create-wizard">
    <el-steps :active="currentStep" align-center>
      <el-step title="基本信息" />
      <el-step title="色谱参数" />
      <el-step title="梯度设置" />
      <el-step title="预处理配置" />
      <el-step title="确认创建" />
    </el-steps>

    <div class="wizard-content">
      <!-- 步骤1: 基本信息 -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>基本信息</h3>
        <el-form :model="methodData" label-width="120px">
          <el-form-item label="方法名称" required>
            <el-input v-model="methodData.name" placeholder="请输入方法名称" />
          </el-form-item>
          <el-form-item label="方法描述">
            <el-input
              v-model="methodData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入方法描述"
            />
          </el-form-item>
          <el-form-item label="方法类型">
            <el-radio-group v-model="methodData.type">
              <el-radio label="user">用户方法</el-radio>
              <el-radio label="template">模板方法</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2: 色谱参数 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>色谱参数</h3>
        <el-form :model="methodData" label-width="120px">
          <el-form-item label="柱子选择" required>
            <el-select v-model="methodData.column" placeholder="选择柱子">
              <el-option label="C18-150mm" value="C18-150mm" />
              <el-option label="C18-250mm" value="C18-250mm" />
              <el-option label="C8-100mm" value="C8-100mm" />
            </el-select>
          </el-form-item>
          <el-form-item label="流速 (mL/min)" required>
            <el-input-number
              v-model="methodData.flowRate"
              :min="0.01"
              :max="10"
              :step="0.01"
              :precision="2"
            />
          </el-form-item>
          <el-form-item label="运行时间 (min)" required>
            <el-input-number
              v-model="methodData.runTime"
              :min="1"
              :max="999"
            />
          </el-form-item>
          <el-form-item label="检测波长 (nm)" required>
            <el-input-number
              v-model="methodData.wavelength"
              :min="190"
              :max="800"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤3: 梯度设置 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>梯度设置</h3>
        <el-form :model="methodData" label-width="120px">
          <el-form-item label="梯度模式" required>
            <el-radio-group v-model="methodData.gradientMode">
              <el-radio label="auto">自动梯度</el-radio>
              <el-radio label="manual">手动梯度</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 自动梯度参数 -->
          <div v-if="methodData.gradientMode === 'auto'">
            <el-form-item label="起始比例 (%)">
              <el-input-number v-model="methodData.autoGradient.startRatio" :min="0" :max="100" />
            </el-form-item>
            <el-form-item label="结束比例 (%)">
              <el-input-number v-model="methodData.autoGradient.endRatio" :min="0" :max="100" />
            </el-form-item>
            <el-form-item label="柱体积 (mL)">
              <el-input-number v-model="methodData.autoGradient.columnVolume" :min="1" :max="200" />
            </el-form-item>
          </div>

          <!-- 手动梯度参数 -->
          <div v-if="methodData.gradientMode === 'manual'">
            <el-form-item label="梯度时间表">
              <el-table :data="methodData.manualGradient" style="width: 100%">
                <el-table-column prop="time" label="时间(min)" width="100">
                  <template #default="scope">
                    <el-input-number v-model="scope.row.time" :min="0" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="solutionA" label="原液A(%)" width="100">
                  <template #default="scope">
                    <el-input-number v-model="scope.row.solutionA" :min="0" :max="100" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="solutionB" label="原液B(%)" width="100">
                  <template #default="scope">
                    <el-input-number v-model="scope.row.solutionB" :min="0" :max="100" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="flowRate" label="流速" width="100">
                  <template #default="scope">
                    <el-input-number v-model="scope.row.flowRate" :min="0.01" :max="10" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="scope">
                    <el-button size="small" type="danger" @click="removeGradientStep(scope.$index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button @click="addGradientStep" style="margin-top: 10px;">添加步骤</el-button>
            </el-form-item>
          </div>
        </el-form>
      </div>

      <!-- 步骤4: 预处理配置 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>预处理配置</h3>
        <el-form :model="methodData" label-width="120px">
          <el-form-item label="吹扫系统">
            <el-switch v-model="methodData.pretreatment.purgeSystem" />
          </el-form-item>
          <el-form-item label="吹扫柱子">
            <el-switch v-model="methodData.pretreatment.purgeColumn" />
          </el-form-item>
          <el-form-item v-if="methodData.pretreatment.purgeColumn" label="吹扫时长 (min)">
            <el-input-number v-model="methodData.pretreatment.purgeTime" :min="1" :max="60" />
          </el-form-item>
          <el-form-item label="柱平衡">
            <el-switch v-model="methodData.pretreatment.columnBalance" />
          </el-form-item>
          <el-form-item v-if="methodData.pretreatment.columnBalance" label="平衡时长 (min)">
            <el-input-number v-model="methodData.pretreatment.balanceTime" :min="1" :max="60" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤5: 确认创建 -->
      <div v-if="currentStep === 4" class="step-content">
        <h3>确认方法信息</h3>
        <div class="method-summary">
          <el-card>
            <h4>{{ methodData.name }}</h4>
            <p>{{ methodData.description }}</p>
            <el-divider />
            <div class="summary-grid">
              <div class="summary-item">
                <label>柱子:</label>
                <span>{{ methodData.column }}</span>
              </div>
              <div class="summary-item">
                <label>流速:</label>
                <span>{{ methodData.flowRate }} mL/min</span>
              </div>
              <div class="summary-item">
                <label>运行时间:</label>
                <span>{{ methodData.runTime }} min</span>
              </div>
              <div class="summary-item">
                <label>检测波长:</label>
                <span>{{ methodData.wavelength }} nm</span>
              </div>
              <div class="summary-item">
                <label>梯度模式:</label>
                <span>{{ methodData.gradientMode === 'auto' ? '自动梯度' : '手动梯度' }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <div class="wizard-footer">
      <el-button @click="previousStep" :disabled="currentStep === 0">上一步</el-button>
      <el-button v-if="currentStep < 4" type="primary" @click="nextStep">下一步</el-button>
      <el-button v-if="currentStep === 4" type="success" @click="saveMethod">保存方法</el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'MethodCreateWizard',
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    const currentStep = ref(0)
    const methodData = ref({
      name: '',
      description: '',
      type: 'user',
      column: '',
      flowRate: 1.0,
      runTime: 30,
      wavelength: 254,
      gradientMode: 'auto',
      autoGradient: {
        startRatio: 80,
        endRatio: 20,
        columnVolume: 57
      },
      manualGradient: [
        { time: 0, solutionA: 80, solutionB: 20, flowRate: 1.0 },
        { time: 30, solutionA: 20, solutionB: 80, flowRate: 1.0 }
      ],
      pretreatment: {
        purgeSystem: false,
        purgeColumn: true,
        purgeTime: 5,
        columnBalance: true,
        balanceTime: 5
      }
    })

    const nextStep = () => {
      if (currentStep.value < 4) {
        currentStep.value++
      }
    }

    const previousStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }

    const addGradientStep = () => {
      const lastStep = methodData.value.manualGradient[methodData.value.manualGradient.length - 1]
      methodData.value.manualGradient.push({
        time: lastStep.time + 10,
        solutionA: 50,
        solutionB: 50,
        flowRate: 1.0
      })
    }

    const removeGradientStep = (index) => {
      if (methodData.value.manualGradient.length > 1) {
        methodData.value.manualGradient.splice(index, 1)
      }
    }

    const saveMethod = () => {
      emit('save', methodData.value)
    }

    return {
      currentStep,
      methodData,
      nextStep,
      previousStep,
      addGradientStep,
      removeGradientStep,
      saveMethod
    }
  }
}
</script>

<style scoped>
.method-create-wizard {
  padding: 20px;
}

.wizard-content {
  margin: 30px 0;
  min-height: 400px;
}

.step-content {
  padding: 20px;
}

.step-content h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
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