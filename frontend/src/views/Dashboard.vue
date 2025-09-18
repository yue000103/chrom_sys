<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="12">
        <RealtimeChart />
      </el-col>
      <el-col :span="12">
        <SystemStatus />
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <HardwareModeControl />
      </el-col>
      <el-col :span="12">
        <ControlPanel />
      </el-col>
    </el-row>
  </div>
</template>

<script>
import RealtimeChart from '../components/charts/RealtimeChart.vue'
import SystemStatus from '../components/monitoring/SystemStatus.vue'
import ControlPanel from '../components/ControlPanel.vue'
import HardwareModeControl from '../components/HardwareModeControl.vue'

export default {
  name: 'Dashboard',
  components: {
    RealtimeChart,
    SystemStatus,
    ControlPanel,
    HardwareModeControl
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}
</style>