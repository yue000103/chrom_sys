<template>
  <div class="hardware-mode-control">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>硬件模式控制</span>
          <el-tag :type="globalMockMode ? 'warning' : 'success'">
            {{ globalMockMode ? '模拟模式' : '联机模式' }}
          </el-tag>
        </div>
      </template>

      <!-- 全局模式控制 -->
      <div class="mode-section">
        <h4>全局联机控制</h4>
        <el-row :gutter="20" align="middle">
          <el-col :span="12">
            <el-switch
              v-model="globalMockMode"
              active-text="模拟模式"
              inactive-text="联机模式"
              active-color="#E6A23C"
              inactive-color="#67C23A"
              @change="handleGlobalModeChange"
              style="--el-switch-on-color: #E6A23C; --el-switch-off-color: #67C23A;"
            />
          </el-col>
          <el-col :span="12">
            <el-button
              :type="globalMockMode ? 'warning' : 'primary'"
              @click="toggleGlobalMode"
              :icon="globalMockMode ? 'Connection' : 'Disconnection'"
            >
              {{ globalMockMode ? '切换到联机' : '切换到模拟' }}
            </el-button>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 特定设备控制 -->
      <div class="mode-section">
        <h4>特定设备控制</h4>
        <el-form :model="deviceForm" label-width="100px">
          <el-form-item label="设备选择">
            <el-select
              v-model="deviceForm.device_id"
              placeholder="请选择设备"
              clearable
              style="width: 100%"
            >
              <el-option-group label="主机模块设备">
                <el-option label="继电器控制器" value="relay_controller" />
                <el-option label="压力传感器 (ttyAMA0)" value="pressure_sensor_ttyAMA0" />
                <el-option label="检测器 (ttyAMA3)" value="detector_ttyAMA3" />
                <el-option label="高压泵控制器 (ttyAMA2)" value="pump_controller_ttyAMA2" />
                <el-option label="气泡传感器 (主机)" value="bubble_sensor_host" />
              </el-option-group>
              <el-option-group label="收集模块设备">
                <el-option label="LED控制器" value="led_controller" />
                <el-option label="阀门控制器" value="valve_controller" />
                <el-option label="气泡传感器 (收集)" value="bubble_sensor_collect" />
                <el-option label="多向阀控制器" value="multi_valve_controller" />
                <el-option label="隔膜泵控制器" value="spray_pump_controller" />
              </el-option-group>
            </el-select>
          </el-form-item>

          <el-form-item label="设备模式">
            <el-radio-group v-model="deviceForm.mock">
              <el-radio :label="false">联机模式</el-radio>
              <el-radio :label="true">模拟模式</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              @click="setDeviceMode"
              :disabled="!deviceForm.device_id"
            >
              设置设备模式
            </el-button>
            <el-button @click="resetDeviceForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-divider />

      <!-- 设备状态列表 -->
      <div class="mode-section">
        <h4>设备状态</h4>
        <el-button @click="fetchDevicesStatus" :icon="'Refresh'">
          刷新状态
        </el-button>
        <el-button @click="resetAllToOnline" type="danger" :icon="'RefreshRight'">
          全部重置为联机
        </el-button>

        <el-table
          :data="devicesStatus"
          style="margin-top: 10px"
          v-if="devicesStatus.length > 0"
        >
          <el-table-column prop="device_id" label="设备ID" />
          <el-table-column prop="name" label="设备名称" />
          <el-table-column label="当前模式">
            <template #default="scope">
              <el-tag :type="scope.row.mock ? 'warning' : 'success'">
                {{ scope.row.mock ? '模拟模式' : '联机模式' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hardwareAPI } from '../services/hardware-api'

// 全局模式状态
const globalMockMode = ref(false)

// 设备表单
const deviceForm = ref({
  device_id: '',
  mock: false
})

// 设备状态列表
const devicesStatus = ref([])

// 设备名称映射
const deviceNames = {
  'relay_controller': '继电器控制器',
  'pressure_sensor_ttyAMA0': '压力传感器',
  'detector_ttyAMA3': '检测器',
  'pump_controller_ttyAMA2': '高压泵控制器',
  'bubble_sensor_host': '气泡传感器(主机)',
  'led_controller': 'LED控制器',
  'valve_controller': '阀门控制器',
  'bubble_sensor_collect': '气泡传感器(收集)',
  'multi_valve_controller': '多向阀控制器',
  'spray_pump_controller': '隔膜泵控制器'
}

// 获取全局模式状态
const fetchGlobalMode = async () => {
  try {
    const response = await hardwareAPI.getMockMode()
    globalMockMode.value = response.mock
  } catch (error) {
    console.error('获取全局模式失败:', error)
    ElMessage.error('获取全局模式失败')
  }
}

// 处理全局模式切换
const handleGlobalModeChange = async (value) => {
  try {
    const mode = value ? '模拟' : '联机'
    await ElMessageBox.confirm(
      `确定要将全局模式切换到${mode}模式吗？`,
      '模式切换确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await hardwareAPI.setMockMode({ mock: value })
    if (response.success) {
      ElMessage.success(response.message)
      fetchDevicesStatus()
    }
  } catch (error) {
    if (error !== 'cancel') {
      globalMockMode.value = !value // 恢复原状态
      ElMessage.error('切换失败: ' + (error.message || error))
    } else {
      globalMockMode.value = !value // 用户取消，恢复原状态
    }
  }
}

// 切换全局模式按钮
const toggleGlobalMode = () => {
  handleGlobalModeChange(!globalMockMode.value)
}

// 设置设备模式
const setDeviceMode = async () => {
  try {
    const { device_id, mock } = deviceForm.value
    if (!device_id) {
      ElMessage.warning('请选择设备')
      return
    }

    const response = await hardwareAPI.setMockMode({ mock, device_id })
    if (response.success) {
      ElMessage.success(response.message)
      fetchDevicesStatus()
      resetDeviceForm()
    }
  } catch (error) {
    ElMessage.error('设置失败: ' + (error.message || error))
  }
}

// 重置设备表单
const resetDeviceForm = () => {
  deviceForm.value = {
    device_id: '',
    mock: false
  }
}

// 获取所有设备状态
const fetchDevicesStatus = async () => {
  try {
    const response = await hardwareAPI.getDevicesStatus()
    globalMockMode.value = response.global_mock

    // 转换设备状态为表格数据
    const devices = []
    for (const [device_id, status] of Object.entries(response.devices || {})) {
      devices.push({
        device_id,
        name: deviceNames[device_id] || device_id,
        mock: status.mock,
        mode: status.mode
      })
    }
    devicesStatus.value = devices
  } catch (error) {
    console.error('获取设备状态失败:', error)
    ElMessage.error('获取设备状态失败')
  }
}

// 重置所有设备为联机模式
const resetAllToOnline = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要将所有设备重置为联机模式吗？',
      '重置确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await hardwareAPI.resetMockMode()
    if (response.success) {
      ElMessage.success(response.message)
      globalMockMode.value = false
      fetchDevicesStatus()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败: ' + (error.message || error))
    }
  }
}

// 组件挂载时获取初始状态
onMounted(() => {
  fetchGlobalMode()
  fetchDevicesStatus()
})
</script>

<style scoped>
.hardware-mode-control {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mode-section {
  margin-bottom: 20px;
}

.mode-section h4 {
  margin-bottom: 15px;
  color: #303133;
}

.el-divider {
  margin: 20px 0;
}
</style>