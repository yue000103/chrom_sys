<template>
  <div class="device-control">
    <h2>设备控制面板</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <RelayPanel />
      </el-col>
      <el-col :span="8">
        <PumpPanel />
      </el-col>
      <el-col :span="8">
        <ValvePanel />
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <SensorPanel />
      </el-col>
      <el-col :span="12">
        <DetectorPanel />
      </el-col>
    </el-row>
  </div>
</template>

<script>
import RelayPanel from '../components/device-panels/RelayPanel.vue'
import PumpPanel from '../components/device-panels/PumpPanel.vue'
import ValvePanel from '../components/device-panels/ValvePanel.vue'
import SensorPanel from '../components/device-panels/SensorPanel.vue'
import DetectorPanel from '../components/device-panels/DetectorPanel.vue'

export default {
  name: 'DeviceControl',
  components: {
    RelayPanel,
    PumpPanel,
    ValvePanel,
    SensorPanel,
    DetectorPanel
  }
}
</script>