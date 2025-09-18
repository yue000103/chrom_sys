<template>
  <div class="data-analysis">
    <h2>数据分析</h2>
    <PressureChart />
    <DetectorChart />
  </div>
</template>

<script>
import PressureChart from '../components/charts/PressureChart.vue'
import DetectorChart from '../components/charts/DetectorChart.vue'

export default {
  name: 'DataAnalysis',
  components: {
    PressureChart,
    DetectorChart
  }
}
</script>