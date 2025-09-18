<template>
  <div class="history-data">
    <el-row :gutter="20">
      <!-- 实验列表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>历史实验</span>
              <div class="header-actions">
                <el-button @click="refreshData">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button type="primary" @click="exportSelected">
                  <el-icon><Download /></el-icon>
                  导出选中
                </el-button>
              </div>
            </div>
          </template>

          <!-- 搜索和筛选 -->
          <el-row :gutter="20" class="mb-3">
            <el-col :span="8">
              <el-input
                v-model="searchText"
                placeholder="搜索实验名称..."
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY/MM/DD"
                value-format="YYYY-MM-DD"
              />
            </el-col>
            <el-col :span="4">
              <el-select v-model="statusFilter" placeholder="状态筛选">
                <el-option label="全部" value="all" />
                <el-option label="已完成" value="completed" />
                <el-option label="异常终止" value="failed" />
                <el-option label="手动停止" value="stopped" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-button @click="resetFilters">重置筛选</el-button>
            </el-col>
          </el-row>

          <!-- 实验数据表格 -->
          <el-table
            :data="filteredExperiments"
            @selection-change="handleSelectionChange"
            @row-click="selectExperiment"
            stripe
            style="width: 100%"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="实验名称" min-width="120" />
            <el-table-column prop="method" label="使用方法" min-width="100" />
            <el-table-column prop="operator" label="操作员" width="80" />
            <el-table-column prop="startTime" label="开始时间" width="150" />
            <el-table-column prop="duration" label="持续时间" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag
                  :type="getStatusType(scope.row.status)"
                  size="small"
                >
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="peakCount" label="检测峰数" width="80" />
            <el-table-column prop="tubeCount" label="收集试管" width="80" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewExperiment(scope.row)">
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
                <el-button size="small" @click="downloadData(scope.row)">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
                <el-button size="small" @click="compareExperiment(scope.row)">
                  <el-icon><TrendCharts /></el-icon>
                  对比
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalExperiments"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 实验详情 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>{{ selectedExperiment ? '实验详情' : '选择实验查看详情' }}</span>
          </template>

          <div v-if="selectedExperiment" class="experiment-details">
            <h3>{{ selectedExperiment.name }}</h3>

            <!-- 基本信息 -->
            <el-divider content-position="left">基本信息</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>实验名称:</label>
                <span>{{ selectedExperiment.name }}</span>
              </div>
              <div class="detail-item">
                <label>使用方法:</label>
                <span>{{ selectedExperiment.method }}</span>
              </div>
              <div class="detail-item">
                <label>操作员:</label>
                <span>{{ selectedExperiment.operator }}</span>
              </div>
              <div class="detail-item">
                <label>开始时间:</label>
                <span>{{ selectedExperiment.startTime }}</span>
              </div>
              <div class="detail-item">
                <label>结束时间:</label>
                <span>{{ selectedExperiment.endTime }}</span>
              </div>
              <div class="detail-item">
                <label>持续时间:</label>
                <span>{{ selectedExperiment.duration }}</span>
              </div>
              <div class="detail-item">
                <label>状态:</label>
                <el-tag :type="getStatusType(selectedExperiment.status)" size="small">
                  {{ getStatusText(selectedExperiment.status) }}
                </el-tag>
              </div>
            </div>

            <!-- 实验参数 -->
            <el-divider content-position="left">实验参数</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>流速:</label>
                <span>{{ selectedExperiment.flowRate }} mL/min</span>
              </div>
              <div class="detail-item">
                <label>检测波长:</label>
                <span>{{ selectedExperiment.wavelength }} nm</span>
              </div>
              <div class="detail-item">
                <label>柱温:</label>
                <span>{{ selectedExperiment.temperature }} °C</span>
              </div>
            </div>

            <!-- 结果统计 -->
            <el-divider content-position="left">结果统计</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>检测峰数:</label>
                <span>{{ selectedExperiment.peakCount }}</span>
              </div>
              <div class="detail-item">
                <label>收集试管:</label>
                <span>{{ selectedExperiment.tubeCount }}</span>
              </div>
              <div class="detail-item">
                <label>最大压力:</label>
                <span>{{ selectedExperiment.maxPressure }} bar</span>
              </div>
              <div class="detail-item">
                <label>数据大小:</label>
                <span>{{ selectedExperiment.dataSize }}</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <el-divider />
            <div class="detail-actions">
              <el-button type="primary" @click="viewFullData">
                <el-icon><View /></el-icon>
                查看完整数据
              </el-button>
              <el-button @click="downloadExperiment">
                <el-icon><Download /></el-icon>
                下载实验数据
              </el-button>
              <el-button @click="addToComparison">
                <el-icon><Plus /></el-icon>
                添加到对比
              </el-button>
            </div>
          </div>

          <el-empty v-else description="请选择实验查看详情" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 实验对比面板 -->
    <el-card v-if="comparisonList.length > 0" class="comparison-panel">
      <template #header>
        <div class="card-header">
          <span>实验对比 ({{ comparisonList.length }}/4)</span>
          <div class="header-actions">
            <el-button @click="clearComparison">清空</el-button>
            <el-button type="primary" @click="startComparison" :disabled="comparisonList.length < 2">
              开始对比分析
            </el-button>
          </div>
        </div>
      </template>

      <div class="comparison-items">
        <el-tag
          v-for="experiment in comparisonList"
          :key="experiment.id"
          closable
          @close="removeFromComparison(experiment)"
          class="comparison-tag"
        >
          {{ experiment.name }}
        </el-tag>
      </div>
    </el-card>

    <!-- 数据查看对话框 -->
    <el-dialog
      v-model="showDataDialog"
      title="实验数据详情"
      width="90%"
      :before-close="handleCloseDataDialog"
    >
      <ExperimentDataViewer
        v-if="showDataDialog"
        :experiment="selectedExperiment"
        @close="showDataDialog = false"
      />
    </el-dialog>

    <!-- 对比分析对话框 -->
    <el-dialog
      v-model="showComparisonDialog"
      title="实验对比分析"
      width="95%"
      :before-close="handleCloseComparisonDialog"
    >
      <ExperimentComparison
        v-if="showComparisonDialog"
        :experiments="comparisonList"
        @close="showComparisonDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import ExperimentDataViewer from '../components/data/ExperimentDataViewer.vue'
import ExperimentComparison from '../components/data/ExperimentComparison.vue'

export default {
  name: 'HistoryData',
  components: {
    ExperimentDataViewer,
    ExperimentComparison
  },
  setup() {
    const searchText = ref('')
    const dateRange = ref([])
    const statusFilter = ref('all')
    const selectedExperiment = ref(null)
    const selectedExperiments = ref([])
    const comparisonList = ref([])
    const showDataDialog = ref(false)
    const showComparisonDialog = ref(false)

    // 分页相关
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalExperiments = ref(0)

    // 模拟历史实验数据
    const experiments = ref([
      {
        id: 1,
        name: '蛋白质分离实验-001',
        method: '标准分析方法-01',
        operator: '张三',
        startTime: '2024-03-15 09:30:00',
        endTime: '2024-03-15 10:15:00',
        duration: '45分钟',
        status: 'completed',
        peakCount: 8,
        tubeCount: 12,
        flowRate: 1.0,
        wavelength: 254,
        temperature: 25,
        maxPressure: 180,
        dataSize: '25.6MB'
      },
      {
        id: 2,
        name: '快速筛选实验-002',
        method: '快速检测方法',
        operator: '李四',
        startTime: '2024-03-14 14:20:00',
        endTime: '2024-03-14 14:35:00',
        duration: '15分钟',
        status: 'completed',
        peakCount: 5,
        tubeCount: 6,
        flowRate: 1.5,
        wavelength: 280,
        temperature: 30,
        maxPressure: 220,
        dataSize: '12.3MB'
      },
      {
        id: 3,
        name: '复杂样品分析-003',
        method: '高分辨分离方法',
        operator: '王五',
        startTime: '2024-03-13 10:00:00',
        endTime: '2024-03-13 11:05:00',
        duration: '65分钟',
        status: 'failed',
        peakCount: 12,
        tubeCount: 18,
        flowRate: 0.8,
        wavelength: 254,
        temperature: 25,
        maxPressure: 350,
        dataSize: '45.2MB'
      }
    ])

    const filteredExperiments = computed(() => {
      let filtered = experiments.value

      // 搜索过滤
      if (searchText.value) {
        filtered = filtered.filter(exp =>
          exp.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
          exp.method.toLowerCase().includes(searchText.value.toLowerCase())
        )
      }

      // 日期范围过滤
      if (dateRange.value && dateRange.value.length === 2) {
        filtered = filtered.filter(exp => {
          const expDate = new Date(exp.startTime).toISOString().split('T')[0]
          return expDate >= dateRange.value[0] && expDate <= dateRange.value[1]
        })
      }

      // 状态过滤
      if (statusFilter.value !== 'all') {
        filtered = filtered.filter(exp => exp.status === statusFilter.value)
      }

      totalExperiments.value = filtered.length
      return filtered
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
        completed: '已完成',
        failed: '异常终止',
        stopped: '手动停止'
      }
      return statusMap[status] || status
    }

    const selectExperiment = (experiment) => {
      selectedExperiment.value = experiment
    }

    const handleSelectionChange = (selection) => {
      selectedExperiments.value = selection
    }

    const viewExperiment = (experiment) => {
      selectedExperiment.value = experiment
      showDataDialog.value = true
    }

    const downloadData = (experiment) => {
      console.log('下载实验数据:', experiment.name)
    }

    const compareExperiment = (experiment) => {
      if (comparisonList.value.length < 4 && !comparisonList.value.find(exp => exp.id === experiment.id)) {
        comparisonList.value.push(experiment)
      }
    }

    const addToComparison = () => {
      if (selectedExperiment.value && comparisonList.value.length < 4) {
        if (!comparisonList.value.find(exp => exp.id === selectedExperiment.value.id)) {
          comparisonList.value.push(selectedExperiment.value)
        }
      }
    }

    const removeFromComparison = (experiment) => {
      const index = comparisonList.value.findIndex(exp => exp.id === experiment.id)
      if (index > -1) {
        comparisonList.value.splice(index, 1)
      }
    }

    const clearComparison = () => {
      comparisonList.value = []
    }

    const startComparison = () => {
      showComparisonDialog.value = true
    }

    const exportSelected = () => {
      console.log('导出选中的实验:', selectedExperiments.value)
    }

    const refreshData = () => {
      console.log('刷新数据')
    }

    const resetFilters = () => {
      searchText.value = ''
      dateRange.value = []
      statusFilter.value = 'all'
    }

    const viewFullData = () => {
      showDataDialog.value = true
    }

    const downloadExperiment = () => {
      console.log('下载实验:', selectedExperiment.value.name)
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
    }

    const handleCloseDataDialog = (done) => {
      done()
    }

    const handleCloseComparisonDialog = (done) => {
      done()
    }

    onMounted(() => {
      totalExperiments.value = experiments.value.length
      if (experiments.value.length > 0) {
        selectedExperiment.value = experiments.value[0]
      }
    })

    return {
      searchText,
      dateRange,
      statusFilter,
      selectedExperiment,
      selectedExperiments,
      comparisonList,
      showDataDialog,
      showComparisonDialog,
      currentPage,
      pageSize,
      totalExperiments,
      experiments,
      filteredExperiments,
      getStatusType,
      getStatusText,
      selectExperiment,
      handleSelectionChange,
      viewExperiment,
      downloadData,
      compareExperiment,
      addToComparison,
      removeFromComparison,
      clearComparison,
      startComparison,
      exportSelected,
      refreshData,
      resetFilters,
      viewFullData,
      downloadExperiment,
      handleSizeChange,
      handleCurrentChange,
      handleCloseDataDialog,
      handleCloseComparisonDialog
    }
  }
}
</script>

<style scoped>
.history-data {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.mb-3 {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}

.experiment-details {
  padding: 16px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 4px 0;
}

.detail-item label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.detail-item span {
  color: #333;
}

.detail-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comparison-panel {
  margin-top: 20px;
}

.comparison-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.comparison-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}
</style>