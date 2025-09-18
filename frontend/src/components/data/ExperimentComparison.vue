<template>
  <div class="experiment-comparison">
    <div class="comparison-header">
      <h3>实验对比分析</h3>
      <p>对比 {{ experiments.length }} 个实验的数据</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 图表对比 -->
      <el-tab-pane label="图表对比" name="chart">
        <div class="chart-comparison">
          <div class="comparison-controls">
            <div class="control-group">
              <label>对比模式:</label>
              <el-radio-group v-model="comparisonMode">
                <el-radio label="overlay">叠加显示</el-radio>
                <el-radio label="separate">分屏显示</el-radio>
                <el-radio label="normalize">归一化对比</el-radio>
              </el-radio-group>
            </div>

            <div class="control-group">
              <label>显示数据:</label>
              <el-checkbox-group v-model="visibleData">
                <el-checkbox label="uv">UV吸收</el-checkbox>
                <el-checkbox label="gradient">梯度</el-checkbox>
                <el-checkbox label="peaks">峰标记</el-checkbox>
              </el-checkbox-group>
            </div>

            <div class="control-group">
              <label>时间对齐:</label>
              <el-switch v-model="timeAlignment" active-text="开启" inactive-text="关闭" />
            </div>
          </div>

          <!-- 实验图例 -->
          <div class="experiments-legend">
            <div
              v-for="(experiment, index) in experiments"
              :key="experiment.id"
              class="legend-experiment"
            >
              <div class="legend-color" :style="{ backgroundColor: getExperimentColor(index) }"></div>
              <span class="legend-name">{{ experiment.name }}</span>
              <el-switch
                v-model="experiment.visible"
                size="small"
                @change="updateChart"
              />
            </div>
          </div>

          <!-- 图表区域 -->
          <div class="charts-container">
            <div v-if="comparisonMode === 'overlay'" class="overlay-chart">
              <div class="chart-placeholder">
                <el-icon class="chart-icon"><TrendCharts /></el-icon>
                <p>叠加对比图表</p>
                <p class="chart-info">所有实验数据在同一图表中显示</p>
              </div>
            </div>

            <div v-if="comparisonMode === 'separate'" class="separate-charts">
              <div
                v-for="(experiment, index) in visibleExperiments"
                :key="experiment.id"
                class="separate-chart"
              >
                <h5>{{ experiment.name }}</h5>
                <div class="chart-placeholder small">
                  <el-icon class="chart-icon small"><TrendCharts /></el-icon>
                  <p>{{ experiment.name }}</p>
                </div>
              </div>
            </div>

            <div v-if="comparisonMode === 'normalize'" class="normalize-chart">
              <div class="chart-placeholder">
                <el-icon class="chart-icon"><TrendCharts /></el-icon>
                <p>归一化对比图表</p>
                <p class="chart-info">数据已归一化便于对比</p>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 峰对比 -->
      <el-tab-pane label="峰对比" name="peaks">
        <div class="peaks-comparison">
          <div class="comparison-summary">
            <h4>峰对比摘要</h4>
            <div class="summary-stats">
              <div class="stat-item">
                <label>实验数量:</label>
                <span>{{ experiments.length }}</span>
              </div>
              <div class="stat-item">
                <label>总峰数:</label>
                <span>{{ totalPeaks }}</span>
              </div>
              <div class="stat-item">
                <label>共同峰:</label>
                <span>{{ commonPeaks }}</span>
              </div>
              <div class="stat-item">
                <label>独特峰:</label>
                <span>{{ uniquePeaks }}</span>
              </div>
            </div>
          </div>

          <!-- 峰匹配表格 -->
          <div class="peaks-matching">
            <h4>峰匹配分析</h4>
            <el-table
              :data="peakMatchingData"
              stripe
              style="width: 100%"
              max-height="400"
            >
              <el-table-column prop="peakGroup" label="峰组" width="80" />
              <el-table-column prop="averageRT" label="平均保留时间(min)" width="150" />
              <el-table-column
                v-for="(experiment, index) in experiments"
                :key="experiment.id"
                :prop="`exp${experiment.id}`"
                :label="experiment.name"
                width="120"
              >
                <template #default="scope">
                  <span v-if="scope.row[`exp${experiment.id}`]">
                    {{ scope.row[`exp${experiment.id}`].retentionTime }}
                  </span>
                  <span v-else class="missing-peak">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="rtStd" label="保留时间RSD(%)" width="130" />
              <el-table-column prop="status" label="匹配状态" width="100">
                <template #default="scope">
                  <el-tag :type="getMatchStatusType(scope.row.status)" size="small">
                    {{ getMatchStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 峰差异分析 -->
          <div class="peaks-difference">
            <h4>峰差异分析</h4>
            <div class="difference-charts">
              <div class="difference-chart">
                <h5>保留时间差异</h5>
                <div class="chart-placeholder small">
                  <el-icon class="chart-icon small"><BarChart /></el-icon>
                  <p>保留时间变化图</p>
                </div>
              </div>
              <div class="difference-chart">
                <h5>峰面积差异</h5>
                <div class="chart-placeholder small">
                  <el-icon class="chart-icon small"><BarChart /></el-icon>
                  <p>峰面积对比图</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 参数对比 -->
      <el-tab-pane label="参数对比" name="parameters">
        <div class="parameters-comparison">
          <h4>实验参数对比</h4>

          <!-- 方法参数对比 -->
          <div class="params-section">
            <h5>方法参数</h5>
            <el-table
              :data="methodParamsComparison"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="parameter" label="参数" width="150" />
              <el-table-column
                v-for="experiment in experiments"
                :key="experiment.id"
                :prop="`exp${experiment.id}`"
                :label="experiment.name"
                min-width="120"
              />
              <el-table-column prop="variation" label="变异系数" width="120">
                <template #default="scope">
                  <span :class="getVariationClass(scope.row.variation)">
                    {{ scope.row.variation }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 结果参数对比 -->
          <div class="params-section">
            <h5>结果参数</h5>
            <el-table
              :data="resultParamsComparison"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="parameter" label="参数" width="150" />
              <el-table-column
                v-for="experiment in experiments"
                :key="experiment.id"
                :prop="`exp${experiment.id}`"
                :label="experiment.name"
                min-width="120"
              />
              <el-table-column prop="trend" label="趋势" width="100">
                <template #default="scope">
                  <el-icon
                    :class="getTrendClass(scope.row.trend)"
                    :style="{ color: getTrendColor(scope.row.trend) }"
                  >
                    <component :is="getTrendIcon(scope.row.trend)" />
                  </el-icon>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 统计分析 -->
          <div class="statistical-analysis">
            <h5>统计分析</h5>
            <div class="analysis-grid">
              <div class="analysis-item">
                <label>重现性:</label>
                <el-progress
                  :percentage="reproducibility"
                  :color="getReproducibilityColor(reproducibility)"
                />
                <span class="percentage-text">{{ reproducibility }}%</span>
              </div>
              <div class="analysis-item">
                <label>方法精密度:</label>
                <el-progress
                  :percentage="precision"
                  :color="getPrecisionColor(precision)"
                />
                <span class="percentage-text">{{ precision }}%</span>
              </div>
              <div class="analysis-item">
                <label>系统稳定性:</label>
                <el-progress
                  :percentage="stability"
                  :color="getStabilityColor(stability)"
                />
                <span class="percentage-text">{{ stability }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 报告生成 -->
      <el-tab-pane label="对比报告" name="report">
        <div class="report-generation">
          <div class="report-config">
            <h4>报告配置</h4>
            <el-form :model="reportConfig" label-width="120px">
              <el-form-item label="报告标题">
                <el-input v-model="reportConfig.title" placeholder="输入报告标题" />
              </el-form-item>

              <el-form-item label="包含内容">
                <el-checkbox-group v-model="reportConfig.sections">
                  <el-checkbox label="summary">对比摘要</el-checkbox>
                  <el-checkbox label="charts">对比图表</el-checkbox>
                  <el-checkbox label="peaks">峰分析</el-checkbox>
                  <el-checkbox label="parameters">参数对比</el-checkbox>
                  <el-checkbox label="statistics">统计分析</el-checkbox>
                  <el-checkbox label="conclusions">结论建议</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="图表分辨率">
                <el-radio-group v-model="reportConfig.resolution">
                  <el-radio label="standard">标准 (300 DPI)</el-radio>
                  <el-radio label="high">高清 (600 DPI)</el-radio>
                  <el-radio label="print">印刷 (1200 DPI)</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="输出格式">
                <el-checkbox-group v-model="reportConfig.formats">
                  <el-checkbox label="pdf">PDF</el-checkbox>
                  <el-checkbox label="word">Word</el-checkbox>
                  <el-checkbox label="excel">Excel</el-checkbox>
                  <el-checkbox label="html">HTML</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="generateReport" :loading="generatingReport">
                  <el-icon><Document /></el-icon>
                  生成对比报告
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 报告预览 -->
          <div class="report-preview">
            <h4>报告预览</h4>
            <div class="preview-content">
              <div class="preview-header">
                <h3>{{ reportConfig.title || '实验对比分析报告' }}</h3>
                <p>生成时间: {{ new Date().toLocaleString() }}</p>
              </div>

              <div class="preview-section">
                <h4>1. 对比摘要</h4>
                <ul>
                  <li>对比实验数量: {{ experiments.length }}</li>
                  <li>分析时间范围: {{ getTimeRange() }}</li>
                  <li>主要发现: 实验间重现性良好，峰形一致</li>
                  <li>建议: 可优化梯度程序以提高分离效果</li>
                </ul>
              </div>

              <div class="preview-section">
                <h4>2. 关键指标</h4>
                <div class="key-metrics">
                  <div class="metric-item">
                    <label>重现性:</label>
                    <span>{{ reproducibility }}%</span>
                  </div>
                  <div class="metric-item">
                    <label>精密度:</label>
                    <span>{{ precision }}%</span>
                  </div>
                  <div class="metric-item">
                    <label>稳定性:</label>
                    <span>{{ stability }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ExperimentComparison',
  props: {
    experiments: {
      type: Array,
      required: true
    }
  },
  emits: ['close'],
  setup(props) {
    const activeTab = ref('chart')
    const comparisonMode = ref('overlay')
    const visibleData = ref(['uv', 'peaks'])
    const timeAlignment = ref(true)
    const generatingReport = ref(false)

    // 报告配置
    const reportConfig = ref({
      title: '',
      sections: ['summary', 'charts', 'peaks', 'parameters'],
      resolution: 'standard',
      formats: ['pdf']
    })

    // 为每个实验添加可见性属性
    const experimentsWithVisibility = ref(
      props.experiments.map(exp => ({ ...exp, visible: true }))
    )

    const visibleExperiments = computed(() => {
      return experimentsWithVisibility.value.filter(exp => exp.visible)
    })

    // 统计数据
    const totalPeaks = computed(() => 25) // 模拟数据
    const commonPeaks = computed(() => 8)
    const uniquePeaks = computed(() => 17)
    const reproducibility = computed(() => 92)
    const precision = computed(() => 88)
    const stability = computed(() => 95)

    // 峰匹配数据
    const peakMatchingData = ref([
      {
        peakGroup: 1,
        averageRT: 5.2,
        exp1: { retentionTime: 5.2 },
        exp2: { retentionTime: 5.1 },
        exp3: { retentionTime: 5.3 },
        rtStd: 1.8,
        status: 'matched'
      },
      {
        peakGroup: 2,
        averageRT: 8.7,
        exp1: { retentionTime: 8.7 },
        exp2: { retentionTime: 8.8 },
        exp3: null,
        rtStd: 0.8,
        status: 'partial'
      },
      {
        peakGroup: 3,
        averageRT: 12.1,
        exp1: { retentionTime: 12.1 },
        exp2: { retentionTime: 12.0 },
        exp3: { retentionTime: 12.2 },
        rtStd: 0.9,
        status: 'matched'
      }
    ])

    // 方法参数对比
    const methodParamsComparison = ref([
      {
        parameter: '流速 (mL/min)',
        exp1: '1.0',
        exp2: '1.0',
        exp3: '1.0',
        variation: '0%'
      },
      {
        parameter: '检测波长 (nm)',
        exp1: '254',
        exp2: '254',
        exp3: '280',
        variation: '5.9%'
      },
      {
        parameter: '柱温 (°C)',
        exp1: '25',
        exp2: '25',
        exp3: '30',
        variation: '11.5%'
      }
    ])

    // 结果参数对比
    const resultParamsComparison = ref([
      {
        parameter: '总运行时间 (min)',
        exp1: '45',
        exp2: '43',
        exp3: '47',
        trend: 'stable'
      },
      {
        parameter: '检测峰数',
        exp1: '8',
        exp2: '7',
        exp3: '9',
        trend: 'increasing'
      },
      {
        parameter: '最大压力 (bar)',
        exp1: '185',
        exp2: '192',
        exp3: '178',
        trend: 'decreasing'
      }
    ])

    const getExperimentColor = (index) => {
      const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
      return colors[index % colors.length]
    }

    const getMatchStatusType = (status) => {
      const statusMap = {
        matched: 'success',
        partial: 'warning',
        unmatched: 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getMatchStatusText = (status) => {
      const statusMap = {
        matched: '完全匹配',
        partial: '部分匹配',
        unmatched: '未匹配'
      }
      return statusMap[status] || status
    }

    const getVariationClass = (variation) => {
      const value = parseFloat(variation)
      if (value <= 5) return 'low-variation'
      if (value <= 15) return 'medium-variation'
      return 'high-variation'
    }

    const getTrendIcon = (trend) => {
      const iconMap = {
        increasing: 'TrendCharts',
        decreasing: 'TrendCharts',
        stable: 'Minus'
      }
      return iconMap[trend] || 'Minus'
    }

    const getTrendClass = (trend) => {
      return `trend-${trend}`
    }

    const getTrendColor = (trend) => {
      const colorMap = {
        increasing: '#67c23a',
        decreasing: '#f56c6c',
        stable: '#909399'
      }
      return colorMap[trend] || '#909399'
    }

    const getReproducibilityColor = (value) => {
      if (value >= 90) return '#67c23a'
      if (value >= 80) return '#e6a23c'
      return '#f56c6c'
    }

    const getPrecisionColor = (value) => {
      if (value >= 85) return '#67c23a'
      if (value >= 75) return '#e6a23c'
      return '#f56c6c'
    }

    const getStabilityColor = (value) => {
      if (value >= 90) return '#67c23a'
      if (value >= 80) return '#e6a23c'
      return '#f56c6c'
    }

    const getTimeRange = () => {
      if (props.experiments.length > 0) {
        return `${props.experiments[0].startTime} - ${props.experiments[props.experiments.length - 1].startTime}`
      }
      return '未知'
    }

    const updateChart = () => {
      console.log('更新图表显示')
    }

    const generateReport = () => {
      generatingReport.value = true
      setTimeout(() => {
        generatingReport.value = false
        console.log('生成对比报告:', reportConfig.value)
      }, 3000)
    }

    return {
      activeTab,
      comparisonMode,
      visibleData,
      timeAlignment,
      generatingReport,
      reportConfig,
      experimentsWithVisibility,
      visibleExperiments,
      totalPeaks,
      commonPeaks,
      uniquePeaks,
      reproducibility,
      precision,
      stability,
      peakMatchingData,
      methodParamsComparison,
      resultParamsComparison,
      getExperimentColor,
      getMatchStatusType,
      getMatchStatusText,
      getVariationClass,
      getTrendIcon,
      getTrendClass,
      getTrendColor,
      getReproducibilityColor,
      getPrecisionColor,
      getStabilityColor,
      getTimeRange,
      updateChart,
      generateReport
    }
  }
}
</script>

<style scoped>
.experiment-comparison {
  padding: 20px;
}

.comparison-header {
  text-align: center;
  margin-bottom: 20px;
}

.comparison-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.comparison-header p {
  color: #666;
  margin: 0;
}

.chart-comparison,
.peaks-comparison,
.parameters-comparison,
.report-generation {
  padding: 20px;
}

.comparison-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.experiments-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f0f9ff;
  border-radius: 6px;
}

.legend-experiment {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.legend-name {
  font-size: 14px;
  color: #333;
}

.charts-container {
  margin-bottom: 20px;
}

.overlay-chart,
.normalize-chart {
  height: 400px;
}

.separate-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.separate-chart {
  height: 250px;
}

.separate-chart h5 {
  margin: 0 0 8px 0;
  color: #333;
  text-align: center;
}

.chart-placeholder {
  height: 100%;
  background-color: #f8f9fa;
  border: 1px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.chart-placeholder.small {
  height: 200px;
}

.chart-placeholder {
  text-align: center;
  color: #909399;
}

.chart-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.chart-icon.small {
  font-size: 32px;
  margin-bottom: 8px;
}

.chart-info {
  font-size: 12px;
  margin-top: 8px;
}

.comparison-summary {
  margin-bottom: 30px;
}

.comparison-summary h4 {
  margin: 0 0 16px 0;
  color: #333;
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

.stat-item label {
  font-size: 14px;
  color: #666;
}

.stat-item span {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.peaks-matching,
.peaks-difference {
  margin-bottom: 30px;
}

.peaks-matching h4,
.peaks-difference h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.missing-peak {
  color: #999;
  font-style: italic;
}

.difference-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.difference-chart h5 {
  margin: 0 0 12px 0;
  color: #666;
  text-align: center;
}

.params-section {
  margin-bottom: 30px;
}

.params-section h5 {
  margin: 0 0 16px 0;
  color: #333;
}

.low-variation {
  color: #67c23a;
  font-weight: bold;
}

.medium-variation {
  color: #e6a23c;
  font-weight: bold;
}

.high-variation {
  color: #f56c6c;
  font-weight: bold;
}

.statistical-analysis {
  margin-top: 30px;
}

.statistical-analysis h5 {
  margin: 0 0 16px 0;
  color: #333;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.analysis-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analysis-item label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.percentage-text {
  text-align: center;
  font-weight: bold;
  color: #333;
}

.report-config {
  margin-bottom: 30px;
}

.report-config h4 {
  margin: 0 0 20px 0;
  color: #333;
}

.report-preview {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.report-preview h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.preview-content {
  background-color: white;
  padding: 20px;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.preview-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 16px;
  border-bottom: 2px solid #409eff;
}

.preview-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.preview-header p {
  color: #666;
  margin: 0;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.preview-section ul {
  margin: 0;
  padding-left: 20px;
}

.preview-section li {
  margin-bottom: 4px;
  color: #666;
}

.key-metrics {
  display: flex;
  gap: 24px;
}

.metric-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.metric-item label {
  font-size: 14px;
  color: #666;
}

.metric-item span {
  font-weight: bold;
  color: #333;
}
</style>