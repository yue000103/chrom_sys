<template>
  <el-card class="chart-container">
    <template #header>
      <span>实时数据图表</span>
    </template>
    <div ref="chartContainer" class="d3-chart-container"></div>
  </el-card>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as d3 from 'd3'
import { useRealtimeDataStore } from '../../store/modules/realtime-data'

export default {
  name: 'RealtimeChart',
  setup() {
    const chartContainer = ref(null)
    const store = useRealtimeDataStore()
    let svg = null
    let xScale = null
    let yScale = null
    let line = null

    const margin = { top: 20, right: 30, bottom: 40, left: 50 }
    const width = 800 - margin.left - margin.right
    const height = 300 - margin.top - margin.bottom

    const initChart = () => {
      // 清理之前的图表
      d3.select(chartContainer.value).selectAll("*").remove()

      // 创建SVG
      svg = d3.select(chartContainer.value)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`)

      // 创建比例尺
      xScale = d3.scaleTime()
        .range([0, width])

      yScale = d3.scaleLinear()
        .range([height, 0])
        .domain([0, 100])

      // 创建线条生成器
      line = d3.line()
        .x(d => xScale(d.timestamp))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX)

      // 添加X轴
      svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${height})`)

      // 添加Y轴
      svg.append('g')
        .attr('class', 'y-axis')

      // 添加X轴标签
      svg.append('text')
        .attr('class', 'x-label')
        .attr('text-anchor', 'middle')
        .attr('x', width / 2)
        .attr('y', height + margin.bottom - 5)
        .text('时间')

      // 添加Y轴标签
      svg.append('text')
        .attr('class', 'y-label')
        .attr('text-anchor', 'middle')
        .attr('transform', 'rotate(-90)')
        .attr('x', -height / 2)
        .attr('y', -margin.left + 15)
        .text('数值')

      // 添加线条路径
      svg.append('path')
        .attr('class', 'data-line')
        .attr('fill', 'none')
        .attr('stroke', '#FF0000')
        .attr('stroke-width', 2)

      // 添加数据点
      svg.append('g')
        .attr('class', 'data-points')
    }

    const updateChart = () => {
      if (!svg) return

      const data = store.dataPoints.map(point => ({
        timestamp: new Date(point.timestamp),
        value: point.value
      }))

      if (data.length === 0) return

      // 更新X轴比例尺
      xScale.domain(d3.extent(data, d => d.timestamp))

      // 更新轴
      const xAxis = d3.axisBottom(xScale)
        .tickFormat(d3.timeFormat('%H:%M:%S'))

      svg.select('.x-axis')
        .call(xAxis)

      svg.select('.y-axis')
        .call(d3.axisLeft(yScale))

      // 更新线条
      svg.select('.data-line')
        .datum(data)
        .attr('d', line)

      // 更新数据点
      const circles = svg.select('.data-points')
        .selectAll('circle')
        .data(data)

      circles.enter()
        .append('circle')
        .merge(circles)
        .attr('cx', d => xScale(d.timestamp))
        .attr('cy', d => yScale(d.value))
        .attr('r', 0)
        .attr('fill', '#4bc0c0')

      circles.exit().remove()
    }

    onMounted(() => {
      initChart()

      // 监听数据变化
      watch(() => store.dataPoints, () => {
        updateChart()
      }, { deep: true })
    })

    onUnmounted(() => {
      if (svg) {
        d3.select(chartContainer.value).selectAll("*").remove()
      }
    })

    return {
      chartContainer
    }
  }
}
</script>

<style scoped>
.chart-container {
  height: 450px;
}

.d3-chart-container {
  width: 100%;
  height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.x-axis) text {
  font-size: 12px;
  font-family: 'Arial', sans-serif;
}

:deep(.y-axis) text {
  font-size: 12px;
  font-family: 'Arial', sans-serif;
}

:deep(.x-label),
:deep(.y-label) {
  font-size: 14px;
  font-weight: bold;
  fill: #666;
}

:deep(.data-line) {
  filter: drop-shadow(0 2px 4px rgba(75, 192, 192, 0.3));
}

:deep(.data-points circle) {
  filter: drop-shadow(0 1px 2px rgba(75, 192, 192, 0.5));
}
</style>