<template>
  <div class="alarm-center">
    <el-row :gutter="20">
      <!-- 左侧：告警概览 -->
      <el-col :span="8">
        <!-- 告警统计 -->
        <el-card class="alarm-stats-card">
          <template #header>
            <span>告警统计</span>
          </template>

          <div class="alarm-stats">
            <div class="stat-item critical">
              <div class="stat-icon critical">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ alarmStats.critical }}</h3>
                <p>严重告警</p>
              </div>
            </div>

            <div class="stat-item warning">
              <div class="stat-icon warning">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ alarmStats.warning }}</h3>
                <p>警告</p>
              </div>
            </div>

            <div class="stat-item info">
              <div class="stat-icon info">
                <el-icon><InfoFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ alarmStats.info }}</h3>
                <p>提示</p>
              </div>
            </div>

            <div class="stat-item resolved">
              <div class="stat-icon resolved">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ alarmStats.resolved }}</h3>
                <p>已解决</p>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 当前活跃告警 -->
        <el-card class="active-alarms-card">
          <template #header>
            <div class="card-header">
              <span>当前活跃告警</span>
              <el-badge :value="activeAlarms.length" type="danger" :hidden="activeAlarms.length === 0">
                <el-icon><Bell /></el-icon>
              </el-badge>
            </div>
          </template>

          <div class="active-alarms">
            <div v-if="activeAlarms.length === 0" class="no-alarms">
              <el-icon class="no-alarm-icon"><CircleCheckFilled /></el-icon>
              <p>系统运行正常</p>
              <p class="sub-text">暂无活跃告警</p>
            </div>

            <div v-else class="alarm-list">
              <div
                v-for="alarm in activeAlarms"
                :key="alarm.id"
                class="alarm-item"
                :class="alarm.level"
                @click="selectAlarm(alarm)"
              >
                <div class="alarm-indicator" :class="alarm.level"></div>
                <div class="alarm-content">
                  <div class="alarm-title">{{ alarm.title }}</div>
                  <div class="alarm-time">{{ formatTime(alarm.createdAt) }}</div>
                </div>
                <div class="alarm-actions">
                  <el-button size="small" @click.stop="acknowledgeAlarm(alarm)">
                    <el-icon><Check /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 系统健康状态 -->
        <el-card class="system-health-card">
          <template #header>
            <span>系统健康状态</span>
          </template>

          <div class="health-status">
            <div class="health-item">
              <div class="health-label">系统压力</div>
              <div class="health-value">
                <span class="value" :class="getPressureStatus(systemHealth.pressure)">
                  {{ systemHealth.pressure }} bar
                </span>
                <div class="health-indicator" :class="getPressureStatus(systemHealth.pressure)"></div>
              </div>
            </div>

            <div class="health-item">
              <div class="health-label">液位状态</div>
              <div class="health-value">
                <span class="value" :class="getLiquidStatus(systemHealth.liquidLevel)">
                  {{ systemHealth.liquidLevel }}%
                </span>
                <div class="health-indicator" :class="getLiquidStatus(systemHealth.liquidLevel)"></div>
              </div>
            </div>

            <div class="health-item">
              <div class="health-label">设备通信</div>
              <div class="health-value">
                <span class="value" :class="systemHealth.communication">
                  {{ getCommStatus(systemHealth.communication) }}
                </span>
                <div class="health-indicator" :class="systemHealth.communication"></div>
              </div>
            </div>

            <div class="health-item">
              <div class="health-label">温度状态</div>
              <div class="health-value">
                <span class="value" :class="getTemperatureStatus(systemHealth.temperature)">
                  {{ systemHealth.temperature }}°C
                </span>
                <div class="health-indicator" :class="getTemperatureStatus(systemHealth.temperature)"></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：告警列表和处理 -->
      <el-col :span="16">
        <!-- 告警历史 -->
        <el-card class="alarm-history-card">
          <template #header>
            <div class="card-header">
              <span>告警历史</span>
              <div class="header-actions">
                <el-button @click="refreshAlarms">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button @click="exportAlarms">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
              </div>
            </div>
          </template>

          <!-- 筛选器 -->
          <el-row :gutter="16" class="filter-row">
            <el-col :span="6">
              <el-select v-model="filterLevel" placeholder="告警级别">
                <el-option label="全部" value="all" />
                <el-option label="严重" value="critical" />
                <el-option label="警告" value="warning" />
                <el-option label="提示" value="info" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="filterStatus" placeholder="处理状态">
                <el-option label="全部" value="all" />
                <el-option label="活跃" value="active" />
                <el-option label="已确认" value="acknowledged" />
                <el-option label="已解决" value="resolved" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-date-picker
                v-model="filterDateRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="MM/DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-col>
            <el-col :span="4">
              <el-button @click="resetFilters">重置</el-button>
            </el-col>
          </el-row>

          <!-- 告警表格 -->
          <el-table
            :data="filteredAlarms"
            @row-click="selectAlarm"
            stripe
            style="width: 100%"
            max-height="400"
          >
            <el-table-column width="60">
              <template #default="scope">
                <div class="alarm-level-indicator" :class="scope.row.level"></div>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="告警内容" min-width="200" />
            <el-table-column prop="source" label="来源" width="100" />
            <el-table-column prop="createdAt" label="发生时间" width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusTagType(scope.row.status)" size="small">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button
                  v-if="scope.row.status === 'active'"
                  size="small"
                  @click.stop="acknowledgeAlarm(scope.row)"
                >
                  确认
                </el-button>
                <el-button
                  v-if="scope.row.status === 'acknowledged'"
                  size="small"
                  type="success"
                  @click.stop="resolveAlarm(scope.row)"
                >
                  解决
                </el-button>
                <el-button size="small" @click.stop="viewAlarmDetail(scope.row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="totalAlarms"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>

        <!-- 选中告警详情 -->
        <el-card v-if="selectedAlarm" class="alarm-detail-card">
          <template #header>
            <div class="card-header">
              <span>告警详情</span>
              <el-tag :type="getAlarmLevelType(selectedAlarm.level)" size="small">
                {{ getAlarmLevelText(selectedAlarm.level) }}
              </el-tag>
            </div>
          </template>

          <div class="alarm-detail">
            <el-row :gutter="20">
              <el-col :span="16">
                <div class="detail-section">
                  <h4>{{ selectedAlarm.title }}</h4>
                  <p class="alarm-description">{{ selectedAlarm.description }}</p>

                  <el-divider content-position="left">基本信息</el-divider>
                  <div class="info-grid">
                    <div class="info-item">
                      <label>告警来源:</label>
                      <span>{{ selectedAlarm.source }}</span>
                    </div>
                    <div class="info-item">
                      <label>发生时间:</label>
                      <span>{{ selectedAlarm.createdAt }}</span>
                    </div>
                    <div class="info-item">
                      <label>当前状态:</label>
                      <el-tag :type="getStatusTagType(selectedAlarm.status)" size="small">
                        {{ getStatusText(selectedAlarm.status) }}
                      </el-tag>
                    </div>
                    <div class="info-item">
                      <label>告警级别:</label>
                      <el-tag :type="getAlarmLevelType(selectedAlarm.level)" size="small">
                        {{ getAlarmLevelText(selectedAlarm.level) }}
                      </el-tag>
                    </div>
                  </div>

                  <el-divider content-position="left">处理建议</el-divider>
                  <div class="suggestions">
                    <ul>
                      <li v-for="suggestion in selectedAlarm.suggestions" :key="suggestion">
                        {{ suggestion }}
                      </li>
                    </ul>
                  </div>
                </div>
              </el-col>

              <el-col :span="8">
                <div class="action-panel">
                  <h4>处理操作</h4>

                  <div class="action-buttons">
                    <el-button
                      v-if="selectedAlarm.status === 'active'"
                      type="warning"
                      @click="acknowledgeAlarm(selectedAlarm)"
                      block
                    >
                      <el-icon><Check /></el-icon>
                      确认告警
                    </el-button>

                    <el-button
                      v-if="selectedAlarm.status === 'acknowledged'"
                      type="success"
                      @click="resolveAlarm(selectedAlarm)"
                      block
                    >
                      <el-icon><CircleCheck /></el-icon>
                      标记已解决
                    </el-button>

                    <el-button @click="addComment" block>
                      <el-icon><ChatDotRound /></el-icon>
                      添加备注
                    </el-button>

                    <el-button v-if="selectedAlarm.level === 'critical'" type="danger" @click="emergencyStop" block>
                      <el-icon><Warning /></el-icon>
                      紧急停机
                    </el-button>
                  </div>

                  <!-- 处理历史 -->
                  <el-divider content-position="left">处理历史</el-divider>
                  <div class="action-history">
                    <div
                      v-for="action in selectedAlarm.actions || []"
                      :key="action.id"
                      class="history-item"
                    >
                      <div class="history-time">{{ action.time }}</div>
                      <div class="history-user">{{ action.user }}</div>
                      <div class="history-action">{{ action.action }}</div>
                    </div>
                    <div v-if="!selectedAlarm.actions || selectedAlarm.actions.length === 0" class="no-history">
                      暂无处理记录
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加备注对话框 -->
    <el-dialog v-model="showCommentDialog" title="添加备注" width="50%">
      <el-input
        v-model="commentText"
        type="textarea"
        :rows="4"
        placeholder="请输入备注内容..."
      />
      <template #footer>
        <el-button @click="showCommentDialog = false">取消</el-button>
        <el-button type="primary" @click="saveComment">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'AlarmCenter',
  setup() {
    const selectedAlarm = ref(null)
    const filterLevel = ref('all')
    const filterStatus = ref('all')
    const filterDateRange = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalAlarms = ref(0)
    const showCommentDialog = ref(false)
    const commentText = ref('')

    // 告警统计
    const alarmStats = ref({
      critical: 2,
      warning: 5,
      info: 8,
      resolved: 23
    })

    // 系统健康状态
    const systemHealth = ref({
      pressure: 185,
      liquidLevel: 75,
      communication: 'normal',
      temperature: 25.5
    })

    // 模拟告警数据
    const alarms = ref([
      {
        id: 1,
        title: '系统压力异常升高',
        description: '检测到系统压力超过安全阈值，当前压力为 380 bar，建议立即检查。',
        level: 'critical',
        status: 'active',
        source: '压力传感器',
        createdAt: '2024-03-15 14:30:00',
        suggestions: [
          '立即停止实验运行',
          '检查管路是否堵塞',
          '检查泵的工作状态',
          '联系技术支持'
        ]
      },
      {
        id: 2,
        title: '检测器信号异常',
        description: 'UV检测器信号出现异常波动，可能影响检测结果。',
        level: 'warning',
        status: 'acknowledged',
        source: 'UV检测器',
        createdAt: '2024-03-15 13:45:00',
        suggestions: [
          '检查检测器灯泡状态',
          '清洁流通池',
          '校准检测器'
        ],
        actions: [
          {
            id: 1,
            time: '2024-03-15 13:50:00',
            user: '张三',
            action: '确认告警'
          }
        ]
      },
      {
        id: 3,
        title: '原液A液位偏低',
        description: '原液A储液瓶液位低于20%，建议及时补充。',
        level: 'warning',
        status: 'active',
        source: '液位传感器',
        createdAt: '2024-03-15 12:20:00',
        suggestions: [
          '补充原液A',
          '检查是否有泄漏',
          '更换储液瓶'
        ]
      },
      {
        id: 4,
        title: '泵速度校准提醒',
        description: '系统提醒进行定期的泵速度校准，建议在空闲时进行。',
        level: 'info',
        status: 'active',
        source: '系统维护',
        createdAt: '2024-03-15 10:00:00',
        suggestions: [
          '安排合适时间进行校准',
          '准备校准用试剂',
          '按照标准操作程序执行'
        ]
      },
      {
        id: 5,
        title: '废液容器接近满载',
        description: '废液收集容器容量已达到85%，建议尽快清空。',
        level: 'warning',
        status: 'resolved',
        source: '废液传感器',
        createdAt: '2024-03-14 16:30:00',
        suggestions: [
          '清空废液容器',
          '检查废液管路',
          '记录废液处理'
        ],
        actions: [
          {
            id: 1,
            time: '2024-03-14 16:35:00',
            user: '李四',
            action: '确认告警'
          },
          {
            id: 2,
            time: '2024-03-14 17:00:00',
            user: '李四',
            action: '已清空废液容器，问题解决'
          }
        ]
      }
    ])

    // 活跃告警
    const activeAlarms = computed(() => {
      return alarms.value.filter(alarm => alarm.status === 'active')
    })

    // 过滤后的告警
    const filteredAlarms = computed(() => {
      let filtered = alarms.value

      if (filterLevel.value !== 'all') {
        filtered = filtered.filter(alarm => alarm.level === filterLevel.value)
      }

      if (filterStatus.value !== 'all') {
        filtered = filtered.filter(alarm => alarm.status === filterStatus.value)
      }

      if (filterDateRange.value && filterDateRange.value.length === 2) {
        filtered = filtered.filter(alarm => {
          const alarmTime = new Date(alarm.createdAt)
          const startTime = new Date(filterDateRange.value[0])
          const endTime = new Date(filterDateRange.value[1])
          return alarmTime >= startTime && alarmTime <= endTime
        })
      }

      totalAlarms.value = filtered.length
      return filtered
    })

    const formatTime = (time) => {
      return new Date(time).toLocaleString('zh-CN')
    }

    const getPressureStatus = (pressure) => {
      if (pressure > 350) return 'critical'
      if (pressure > 200) return 'warning'
      return 'normal'
    }

    const getLiquidStatus = (level) => {
      if (level < 20) return 'critical'
      if (level < 50) return 'warning'
      return 'normal'
    }

    const getTemperatureStatus = (temp) => {
      if (temp > 60 || temp < 4) return 'critical'
      if (temp > 50 || temp < 10) return 'warning'
      return 'normal'
    }

    const getCommStatus = (status) => {
      const statusMap = {
        normal: '正常',
        warning: '不稳定',
        critical: '断开'
      }
      return statusMap[status] || status
    }

    const getAlarmLevelType = (level) => {
      const levelMap = {
        critical: 'danger',
        warning: 'warning',
        info: 'info'
      }
      return levelMap[level] || 'info'
    }

    const getAlarmLevelText = (level) => {
      const levelMap = {
        critical: '严重',
        warning: '警告',
        info: '提示'
      }
      return levelMap[level] || level
    }

    const getStatusTagType = (status) => {
      const statusMap = {
        active: 'danger',
        acknowledged: 'warning',
        resolved: 'success'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        active: '活跃',
        acknowledged: '已确认',
        resolved: '已解决'
      }
      return statusMap[status] || status
    }

    const selectAlarm = (alarm) => {
      selectedAlarm.value = alarm
    }

    const acknowledgeAlarm = (alarm) => {
      alarm.status = 'acknowledged'
      if (!alarm.actions) {
        alarm.actions = []
      }
      alarm.actions.push({
        id: Date.now(),
        time: new Date().toLocaleString('zh-CN'),
        user: '当前用户',
        action: '确认告警'
      })
      console.log('确认告警:', alarm.title)
    }

    const resolveAlarm = (alarm) => {
      alarm.status = 'resolved'
      if (!alarm.actions) {
        alarm.actions = []
      }
      alarm.actions.push({
        id: Date.now(),
        time: new Date().toLocaleString('zh-CN'),
        user: '当前用户',
        action: '标记为已解决'
      })
      console.log('解决告警:', alarm.title)
    }

    const addComment = () => {
      showCommentDialog.value = true
    }

    const saveComment = () => {
      if (selectedAlarm.value && commentText.value.trim()) {
        if (!selectedAlarm.value.actions) {
          selectedAlarm.value.actions = []
        }
        selectedAlarm.value.actions.push({
          id: Date.now(),
          time: new Date().toLocaleString('zh-CN'),
          user: '当前用户',
          action: `添加备注: ${commentText.value}`
        })
        commentText.value = ''
        showCommentDialog.value = false
      }
    }

    const emergencyStop = () => {
      console.log('执行紧急停机')
    }

    const viewAlarmDetail = (alarm) => {
      selectedAlarm.value = alarm
    }

    const refreshAlarms = () => {
      console.log('刷新告警数据')
    }

    const exportAlarms = () => {
      console.log('导出告警数据')
    }

    const resetFilters = () => {
      filterLevel.value = 'all'
      filterStatus.value = 'all'
      filterDateRange.value = []
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
    }

    onMounted(() => {
      totalAlarms.value = alarms.value.length
      if (alarms.value.length > 0) {
        selectedAlarm.value = alarms.value[0]
      }
    })

    return {
      selectedAlarm,
      filterLevel,
      filterStatus,
      filterDateRange,
      currentPage,
      pageSize,
      totalAlarms,
      showCommentDialog,
      commentText,
      alarmStats,
      systemHealth,
      alarms,
      activeAlarms,
      filteredAlarms,
      formatTime,
      getPressureStatus,
      getLiquidStatus,
      getTemperatureStatus,
      getCommStatus,
      getAlarmLevelType,
      getAlarmLevelText,
      getStatusTagType,
      getStatusText,
      selectAlarm,
      acknowledgeAlarm,
      resolveAlarm,
      addComment,
      saveComment,
      emergencyStop,
      viewAlarmDetail,
      refreshAlarms,
      exportAlarms,
      resetFilters,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.alarm-center {
  padding: 20px;
}

.alarm-stats-card,
.active-alarms-card,
.system-health-card,
.alarm-history-card,
.alarm-detail-card {
  margin-bottom: 20px;
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

/* 告警统计 */
.alarm-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background-color: #f8f9fa;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.stat-icon.critical {
  background-color: #f56c6c;
}

.stat-icon.warning {
  background-color: #e6a23c;
}

.stat-icon.info {
  background-color: #409eff;
}

.stat-icon.resolved {
  background-color: #67c23a;
}

.stat-info h3 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-info p {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 14px;
}

/* 活跃告警 */
.no-alarms {
  text-align: center;
  padding: 40px 0;
  color: #67c23a;
}

.no-alarm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.no-alarms p {
  margin: 8px 0;
}

.sub-text {
  color: #999 !important;
  font-size: 14px !important;
}

.alarm-list {
  max-height: 300px;
  overflow-y: auto;
}

.alarm-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.alarm-item:hover {
  background-color: #f8f9fa;
  border-color: #409eff;
}

.alarm-item.critical {
  border-left: 4px solid #f56c6c;
}

.alarm-item.warning {
  border-left: 4px solid #e6a23c;
}

.alarm-item.info {
  border-left: 4px solid #409eff;
}

.alarm-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.alarm-indicator.critical {
  background-color: #f56c6c;
}

.alarm-indicator.warning {
  background-color: #e6a23c;
}

.alarm-indicator.info {
  background-color: #409eff;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.alarm-content {
  flex: 1;
}

.alarm-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.alarm-time {
  font-size: 12px;
  color: #999;
}

.alarm-actions {
  display: flex;
  gap: 4px;
}

/* 系统健康状态 */
.health-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.health-label {
  font-size: 14px;
  color: #666;
}

.health-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.health-value .value {
  font-weight: bold;
}

.health-value .value.normal {
  color: #67c23a;
}

.health-value .value.warning {
  color: #e6a23c;
}

.health-value .value.critical {
  color: #f56c6c;
}

.health-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.health-indicator.normal {
  background-color: #67c23a;
}

.health-indicator.warning {
  background-color: #e6a23c;
}

.health-indicator.critical {
  background-color: #f56c6c;
}

/* 过滤器 */
.filter-row {
  margin-bottom: 20px;
}

/* 告警级别指示器 */
.alarm-level-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.alarm-level-indicator.critical {
  background-color: #f56c6c;
}

.alarm-level-indicator.warning {
  background-color: #e6a23c;
}

.alarm-level-indicator.info {
  background-color: #409eff;
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  text-align: center;
}

/* 告警详情 */
.alarm-detail {
  padding: 16px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.alarm-description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item label {
  color: #666;
  font-weight: 500;
}

.suggestions ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions li {
  margin-bottom: 8px;
  color: #666;
  line-height: 1.5;
}

/* 操作面板 */
.action-panel h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.action-history {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
  background-color: #f8f9fa;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.history-user {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.history-action {
  font-size: 14px;
  color: #333;
  margin-top: 4px;
}

.no-history {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-style: italic;
}
</style>