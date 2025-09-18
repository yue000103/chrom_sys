<template>
  <div class="experiment-end-processing">
    <div class="processing-header">
      <h3>实验结束处理</h3>
      <p>实验 "{{ experiment?.name }}" 已结束，请确认后续处理操作</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 数据保存 -->
      <el-tab-pane label="数据保存" name="save">
        <div class="save-panel">
          <el-form :model="saveData" label-width="120px">
            <el-form-item label="实验名称">
              <el-input v-model="saveData.name" placeholder="输入保存的实验名称" />
            </el-form-item>

            <el-form-item label="数据描述">
              <el-input
                v-model="saveData.description"
                type="textarea"
                :rows="3"
                placeholder="输入实验数据描述"
              />
            </el-form-item>

            <el-form-item label="数据类型">
              <el-checkbox-group v-model="saveData.dataTypes">
                <el-checkbox label="raw_data">原始数据</el-checkbox>
                <el-checkbox label="processed_data">处理后数据</el-checkbox>
                <el-checkbox label="peak_data">峰数据</el-checkbox>
                <el-checkbox label="method_data">方法参数</el-checkbox>
                <el-checkbox label="report">分析报告</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="保存路径">
              <el-input v-model="saveData.path" placeholder="选择保存路径">
                <template #append>
                  <el-button @click="selectPath">浏览</el-button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="文件格式">
              <el-radio-group v-model="saveData.format">
                <el-radio label="csv">CSV</el-radio>
                <el-radio label="excel">Excel</el-radio>
                <el-radio label="pdf">PDF报告</el-radio>
                <el-radio label="raw">原始格式</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveExperimentData" :loading="saving">
                <el-icon><Download /></el-icon>
                保存数据
              </el-button>
            </el-form-item>
          </el-form>

          <div class="save-summary">
            <h4>实验总结</h4>
            <div class="summary-grid">
              <div class="summary-item">
                <label>运行时间:</label>
                <span>{{ experimentSummary.duration }}</span>
              </div>
              <div class="summary-item">
                <label>检测峰数:</label>
                <span>{{ experimentSummary.peakCount }}</span>
              </div>
              <div class="summary-item">
                <label>收集试管:</label>
                <span>{{ experimentSummary.tubeCount }}</span>
              </div>
              <div class="summary-item">
                <label>最大压力:</label>
                <span>{{ experimentSummary.maxPressure }} bar</span>
              </div>
              <div class="summary-item">
                <label>数据大小:</label>
                <span>{{ experimentSummary.dataSize }}</span>
              </div>
              <div class="summary-item">
                <label>结束状态:</label>
                <el-tag :type="getStatusType(experimentSummary.status)">
                  {{ getStatusText(experimentSummary.status) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 合并收集 -->
      <el-tab-pane label="合并收集" name="merge">
        <div class="merge-panel">
          <div class="tube-selection">
            <h4>选择需要合并的试管</h4>
            <div class="tube-grid">
              <div
                v-for="tube in collectedTubes"
                :key="tube.id"
                class="tube-item"
                :class="{ 'selected': mergeData.selectedTubes.includes(tube.id) }"
                @click="toggleTubeSelection(tube.id)"
              >
                <div class="tube-visual">
                  <div class="tube-fill" :style="{ height: `${tube.fillLevel}%` }"></div>
                  <span class="tube-number">{{ tube.id }}</span>
                </div>
                <div class="tube-info">
                  <div class="tube-volume">{{ tube.volume }}mL</div>
                  <div class="tube-peak">峰{{ tube.peakId }}</div>
                  <div class="tube-time">{{ tube.collectionTime }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="merge-config">
            <h4>合并配置</h4>
            <el-form :model="mergeData" label-width="120px">
              <el-form-item label="目标试管">
                <el-select v-model="mergeData.targetTube" placeholder="选择目标试管">
                  <el-option
                    v-for="tube in availableTargetTubes"
                    :key="tube"
                    :label="`试管 ${tube}`"
                    :value="tube"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="合并顺序">
                <el-radio-group v-model="mergeData.mergeOrder">
                  <el-radio label="time">按收集时间</el-radio>
                  <el-radio label="peak">按峰序号</el-radio>
                  <el-radio label="volume">按体积大小</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="混合方式">
                <el-radio-group v-model="mergeData.mixingMethod">
                  <el-radio label="gentle">轻柔混合</el-radio>
                  <el-radio label="vigorous">强烈混合</el-radio>
                  <el-radio label="none">不混合</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="执行方式">
                <el-radio-group v-model="mergeData.executionMode">
                  <el-radio label="immediate">立即执行</el-radio>
                  <el-radio label="queue">加入队列</el-radio>
                  <el-radio label="schedule">定时执行</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="mergeData.executionMode === 'schedule'" label="执行时间">
                <el-date-picker
                  v-model="mergeData.scheduledTime"
                  type="datetime"
                  placeholder="选择执行时间"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  @click="createMergeTask"
                  :disabled="mergeData.selectedTubes.length < 2"
                >
                  <el-icon><Merge /></el-icon>
                  创建合并任务
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="merge-preview">
            <h4>合并预览</h4>
            <div v-if="mergeData.selectedTubes.length >= 2" class="preview-content">
              <div class="preview-summary">
                <div class="preview-item">
                  <label>选中试管:</label>
                  <span>{{ mergeData.selectedTubes.length }} 支</span>
                </div>
                <div class="preview-item">
                  <label>总体积:</label>
                  <span>{{ totalMergeVolume }} mL</span>
                </div>
                <div class="preview-item">
                  <label>预计时间:</label>
                  <span>{{ estimatedMergeTime }} 分钟</span>
                </div>
              </div>
            </div>
            <div v-else class="no-preview">
              请至少选择2支试管进行合并
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 清洗处理 -->
      <el-tab-pane label="清洗处理" name="clean">
        <div class="clean-panel">
          <div class="clean-selection">
            <h4>选择需要清洗的试管</h4>
            <div class="selection-controls">
              <el-button @click="selectAllTubes">全选</el-button>
              <el-button @click="selectEmptyTubes">选择空试管</el-button>
              <el-button @click="selectUsedTubes">选择已用试管</el-button>
              <el-button @click="clearSelection">清空选择</el-button>
            </div>

            <div class="tube-grid">
              <div
                v-for="tube in allTubes"
                :key="tube.id"
                class="tube-item"
                :class="{
                  'selected': cleanData.selectedTubes.includes(tube.id),
                  'empty': tube.status === 'empty',
                  'used': tube.status === 'used'
                }"
                @click="toggleCleanTubeSelection(tube.id)"
              >
                <div class="tube-visual">
                  <div class="tube-fill" :style="{ height: `${tube.fillLevel}%` }"></div>
                  <span class="tube-number">{{ tube.id }}</span>
                </div>
                <div class="tube-status">{{ getTubeStatusText(tube.status) }}</div>
              </div>
            </div>
          </div>

          <div class="clean-config">
            <h4>清洗配置</h4>
            <el-form :model="cleanData" label-width="120px">
              <el-form-item label="清洗模式">
                <el-radio-group v-model="cleanData.cleanMode">
                  <el-radio label="normal">标准清洗</el-radio>
                  <el-radio label="intensive">深度清洗</el-radio>
                  <el-radio label="quick">快速清洗</el-radio>
                  <el-radio label="custom">自定义</el-radio>
                </el-radio-group>
              </el-form-item>

              <div v-if="cleanData.cleanMode === 'custom'" class="custom-clean-params">
                <el-form-item label="清洗溶剂">
                  <el-select v-model="cleanData.solvent">
                    <el-option label="去离子水" value="water" />
                    <el-option label="甲醇" value="methanol" />
                    <el-option label="乙腈" value="acetonitrile" />
                    <el-option label="异丙醇" value="isopropanol" />
                  </el-select>
                </el-form-item>

                <el-form-item label="清洗体积 (mL)">
                  <el-input-number v-model="cleanData.volume" :min="1" :max="50" />
                </el-form-item>

                <el-form-item label="清洗次数">
                  <el-input-number v-model="cleanData.cycles" :min="1" :max="10" />
                </el-form-item>

                <el-form-item label="清洗温度 (°C)">
                  <el-input-number v-model="cleanData.temperature" :min="20" :max="80" />
                </el-form-item>
              </div>

              <el-form-item label="清洗后处理">
                <el-checkbox-group v-model="cleanData.postTreatment">
                  <el-checkbox label="air_dry">空气干燥</el-checkbox>
                  <el-checkbox label="nitrogen_dry">氮气干燥</el-checkbox>
                  <el-checkbox label="rinse">最终冲洗</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="执行方式">
                <el-radio-group v-model="cleanData.executionMode">
                  <el-radio label="immediate">立即执行</el-radio>
                  <el-radio label="queue">加入队列</el-radio>
                  <el-radio label="batch">批量处理</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  @click="createCleanTask"
                  :disabled="cleanData.selectedTubes.length === 0"
                >
                  <el-icon><Brush /></el-icon>
                  创建清洗任务
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="processing-footer">
      <el-button @click="$emit('cancel')">稍后处理</el-button>
      <el-button type="success" @click="completeProcessing">完成处理</el-button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ExperimentEndProcessing',
  props: {
    experiment: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['save', 'merge', 'clean', 'cancel'],
  setup(props, { emit }) {
    const activeTab = ref('save')
    const saving = ref(false)

    // 保存数据配置
    const saveData = ref({
      name: props.experiment?.name || '',
      description: '',
      dataTypes: ['raw_data', 'processed_data', 'peak_data'],
      path: '',
      format: 'csv'
    })

    // 合并数据配置
    const mergeData = ref({
      selectedTubes: [],
      targetTube: '',
      mergeOrder: 'time',
      mixingMethod: 'gentle',
      executionMode: 'immediate',
      scheduledTime: null
    })

    // 清洗数据配置
    const cleanData = ref({
      selectedTubes: [],
      cleanMode: 'normal',
      solvent: 'water',
      volume: 10,
      cycles: 2,
      temperature: 25,
      postTreatment: ['air_dry'],
      executionMode: 'immediate'
    })

    // 实验总结
    const experimentSummary = ref({
      duration: '45分钟',
      peakCount: 8,
      tubeCount: 12,
      maxPressure: 185,
      dataSize: '25.6MB',
      status: 'completed'
    })

    // 已收集的试管
    const collectedTubes = ref([
      { id: 1, volume: 5.2, fillLevel: 85, peakId: 1, collectionTime: '14:32', status: 'used' },
      { id: 2, volume: 4.8, fillLevel: 78, peakId: 2, collectionTime: '14:38', status: 'used' },
      { id: 3, volume: 6.1, fillLevel: 92, peakId: 3, collectionTime: '14:45', status: 'used' },
      { id: 4, volume: 3.9, fillLevel: 65, peakId: 4, collectionTime: '14:52', status: 'used' },
      { id: 5, volume: 5.5, fillLevel: 88, peakId: 5, collectionTime: '14:58', status: 'used' }
    ])

    // 所有试管（包括空试管）
    const allTubes = ref([
      ...collectedTubes.value,
      ...Array.from({ length: 35 }, (_, i) => ({
        id: i + 6,
        volume: 0,
        fillLevel: 0,
        status: 'empty'
      }))
    ])

    // 可用的目标试管
    const availableTargetTubes = computed(() => {
      return Array.from({ length: 40 }, (_, i) => i + 1)
        .filter(id => !mergeData.value.selectedTubes.includes(id))
    })

    // 合并总体积
    const totalMergeVolume = computed(() => {
      return mergeData.value.selectedTubes.reduce((total, tubeId) => {
        const tube = collectedTubes.value.find(t => t.id === tubeId)
        return total + (tube ? tube.volume : 0)
      }, 0).toFixed(1)
    })

    // 预计合并时间
    const estimatedMergeTime = computed(() => {
      return Math.ceil(mergeData.value.selectedTubes.length * 2)
    })

    const getStatusType = (status) => {
      const statusMap = {
        completed: 'success',
        failed: 'danger',
        stopped: 'warning'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        completed: '正常完成',
        failed: '异常终止',
        stopped: '手动停止'
      }
      return statusMap[status] || status
    }

    const getTubeStatusText = (status) => {
      const statusMap = {
        empty: '空',
        used: '已用'
      }
      return statusMap[status] || status
    }

    const selectPath = () => {
      console.log('选择保存路径')
    }

    const saveExperimentData = () => {
      saving.value = true
      setTimeout(() => {
        saving.value = false
        emit('save', saveData.value)
        console.log('保存实验数据:', saveData.value)
      }, 2000)
    }

    const toggleTubeSelection = (tubeId) => {
      const index = mergeData.value.selectedTubes.indexOf(tubeId)
      if (index > -1) {
        mergeData.value.selectedTubes.splice(index, 1)
      } else {
        mergeData.value.selectedTubes.push(tubeId)
      }
    }

    const createMergeTask = () => {
      emit('merge', mergeData.value)
      console.log('创建合并任务:', mergeData.value)
    }

    const toggleCleanTubeSelection = (tubeId) => {
      const index = cleanData.value.selectedTubes.indexOf(tubeId)
      if (index > -1) {
        cleanData.value.selectedTubes.splice(index, 1)
      } else {
        cleanData.value.selectedTubes.push(tubeId)
      }
    }

    const selectAllTubes = () => {
      cleanData.value.selectedTubes = allTubes.value.map(tube => tube.id)
    }

    const selectEmptyTubes = () => {
      cleanData.value.selectedTubes = allTubes.value
        .filter(tube => tube.status === 'empty')
        .map(tube => tube.id)
    }

    const selectUsedTubes = () => {
      cleanData.value.selectedTubes = allTubes.value
        .filter(tube => tube.status === 'used')
        .map(tube => tube.id)
    }

    const clearSelection = () => {
      cleanData.value.selectedTubes = []
    }

    const createCleanTask = () => {
      emit('clean', cleanData.value)
      console.log('创建清洗任务:', cleanData.value)
    }

    const completeProcessing = () => {
      console.log('完成所有处理')
    }

    return {
      activeTab,
      saving,
      saveData,
      mergeData,
      cleanData,
      experimentSummary,
      collectedTubes,
      allTubes,
      availableTargetTubes,
      totalMergeVolume,
      estimatedMergeTime,
      getStatusType,
      getStatusText,
      getTubeStatusText,
      selectPath,
      saveExperimentData,
      toggleTubeSelection,
      createMergeTask,
      toggleCleanTubeSelection,
      selectAllTubes,
      selectEmptyTubes,
      selectUsedTubes,
      clearSelection,
      createCleanTask,
      completeProcessing
    }
  }
}
</script>

<style scoped>
.experiment-end-processing {
  padding: 20px;
}

.processing-header {
  text-align: center;
  margin-bottom: 30px;
}

.processing-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.processing-header p {
  color: #666;
  margin: 0;
}

.save-panel,
.merge-panel,
.clean-panel {
  padding: 20px;
}

.save-summary {
  margin-top: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.save-summary h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

.tube-selection {
  margin-bottom: 30px;
}

.tube-selection h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.selection-controls {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.tube-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.tube-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border: 2px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tube-item:hover {
  border-color: #409eff;
}

.tube-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.tube-item.empty {
  opacity: 0.6;
}

.tube-item.used {
  border-color: #67c23a;
}

.tube-visual {
  position: relative;
  width: 40px;
  height: 60px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  margin-bottom: 8px;
}

.tube-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #409eff;
  border-radius: 0 0 4px 4px;
  transition: height 0.3s ease;
}

.tube-number {
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: bold;
  color: #666;
}

.tube-info {
  text-align: center;
  font-size: 10px;
  color: #666;
}

.tube-volume {
  font-weight: bold;
  color: #333;
}

.tube-status {
  font-size: 10px;
  color: #666;
  text-align: center;
}

.merge-config,
.clean-config {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.merge-config h4,
.clean-config h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.custom-clean-params {
  margin-left: 20px;
  padding-left: 20px;
  border-left: 2px solid #409eff;
}

.merge-preview {
  padding: 20px;
  background-color: #f0f9ff;
  border-radius: 6px;
}

.merge-preview h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-item label {
  color: #666;
  font-weight: 500;
}

.no-preview {
  text-align: center;
  color: #999;
  font-style: italic;
}

.processing-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>