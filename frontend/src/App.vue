<template>
  <div id="app" @click="handleAppClick">
    <div class="app-container">
      <!-- 紫色顶部状态栏 -->
      <header class="top-status-bar">
        <div class="status-content">
          <div class="system-info">
            <div class="system-brand">ChromaFlow</div>
            <div class="system-version">v1.0.0</div>
          </div>

          <div class="status-indicators">
            <div class="status-item pump">
              <div class="status-dot blue"></div>
              <span>泵</span>
            </div>
            <div class="status-item detector">
              <div class="status-dot green"></div>
              <span>检测器</span>
            </div>
            <div class="status-item pressure">
              <div class="status-dot orange" :class="{ red: currentPressure > 300 }"></div>
              <span>{{ currentPressure }}bar</span>
            </div>
            <div class="status-item alarm" v-if="alarmCount > 0">
              <div class="status-dot red blink"></div>
              <span>{{ alarmCount }}报警</span>
            </div>
          </div>

          <div class="system-time">
            <div class="time-display">{{ currentTime }}</div>
            <div class="runtime">运行: {{ runtimeDisplay }}</div>
          </div>
        </div>
      </header>

      <!-- 悬浮式导航按钮 -->
      <div class="nav-trigger" @click.stop="toggleNav" :class="{ active: showNav }">
        <div class="nav-icon">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <!-- 悬浮导航面板 -->
      <div class="floating-nav" :class="{ show: showNav }" @click.stop>
        <div class="nav-header">
          <h3>功能导航</h3>
          <button class="close-btn" @click="toggleNav">×</button>
        </div>

        <div class="nav-grid">
          <div
            v-for="item in navItems"
            :key="item.name"
            class="nav-item"
            :class="{ active: activeTab === item.name }"
            @click="switchTab(item.name)"
          >
            <div class="nav-icon-container" :style="{ backgroundColor: item.color }">
              <el-icon class="nav-item-icon"><component :is="item.icon" /></el-icon>
            </div>
            <div class="nav-item-label">{{ item.label }}</div>
            <div v-if="item.badge" class="nav-badge">{{ item.badge }}</div>
          </div>
        </div>
      </div>

      <!-- 遮罩层 -->
      <div class="nav-overlay" :class="{ show: showNav }" @click="toggleNav"></div>

      <!-- 主要内容区域 -->
      <main class="app-main">
        <div class="content-wrapper">
          <ExperimentManagement v-show="activeTab === 'experiment'" />
          <MethodManager v-show="activeTab === 'method'" />
          <RealtimeMonitoring v-show="activeTab === 'monitoring'" />
          <DataAnalysis v-show="activeTab === 'analysis'" />
          <HistoryData v-show="activeTab === 'history'" />
          <SystemConfig v-show="activeTab === 'config'" />
          <AlarmCenter v-show="activeTab === 'alarm'" />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ExperimentManagement from './views/ExperimentManagement.vue'
import MethodManager from './views/MethodManager.vue'
import RealtimeMonitoring from './views/RealtimeMonitoring.vue'
import DataAnalysis from './views/DataAnalysis.vue'
import HistoryData from './views/HistoryData.vue'
import SystemConfig from './views/SystemConfig.vue'
import AlarmCenter from './views/AlarmCenter.vue'

export default {
  name: 'App',
  components: {
    ExperimentManagement,
    MethodManager,
    RealtimeMonitoring,
    DataAnalysis,
    HistoryData,
    SystemConfig,
    AlarmCenter
  },
  setup() {
    const activeTab = ref('monitoring')
    const currentTime = ref('')
    const alarmCount = ref(2)
    const showNav = ref(false)
    const currentPressure = ref(185)
    const systemStartTime = ref(new Date(Date.now() - 2 * 60 * 60 * 1000)) // 2小时前启动

    // 导航菜单项配置
    const navItems = ref([
      {
        name: 'monitoring',
        label: '实时监控',
        icon: 'Monitor',
        color: '#409eff'
      },
      {
        name: 'experiment',
        label: '实验管理',
        icon: 'Operation',
        color: '#67c23a'
      },
      {
        name: 'method',
        label: '方法管理',
        icon: 'Document',
        color: '#e6a23c'
      },
      {
        name: 'analysis',
        label: '数据分析',
        icon: 'TrendCharts',
        color: '#f56c6c'
      },
      {
        name: 'history',
        label: '历史数据',
        icon: 'Clock',
        color: '#909399'
      },
      {
        name: 'config',
        label: '系统配置',
        icon: 'Setting',
        color: '#606266'
      },
      {
        name: 'alarm',
        label: '报警中心',
        icon: 'Warning',
        color: '#f56c6c',
        badge: alarmCount.value > 0 ? alarmCount.value : null
      }
    ])

    // 计算系统运行时间
    const runtimeDisplay = computed(() => {
      const elapsed = Date.now() - systemStartTime.value.getTime()
      const hours = Math.floor(elapsed / (60 * 60 * 1000))
      const minutes = Math.floor((elapsed % (60 * 60 * 1000)) / (60 * 1000))
      return `${hours}h ${minutes}m`
    })

    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }

    // 切换导航面板
    const toggleNav = () => {
      showNav.value = !showNav.value
    }

    // 切换标签页
    const switchTab = (tabName) => {
      activeTab.value = tabName
      showNav.value = false
    }

    // 处理应用点击事件（用于关闭导航）
    const handleAppClick = () => {
      if (showNav.value) {
        showNav.value = false
      }
    }

    let timeInterval = null
    let pressureInterval = null

    onMounted(() => {
      updateTime()
      timeInterval = setInterval(updateTime, 1000)

      // 模拟压力数据变化
      pressureInterval = setInterval(() => {
        currentPressure.value = Math.round(180 + Math.random() * 40)
      }, 5000)
    })

    onUnmounted(() => {
      if (timeInterval) {
        clearInterval(timeInterval)
      }
      if (pressureInterval) {
        clearInterval(pressureInterval)
      }
    })

    return {
      activeTab,
      currentTime,
      alarmCount,
      showNav,
      currentPressure,
      runtimeDisplay,
      navItems,
      toggleNav,
      switchTab,
      handleAppClick
    }
  }
}
</script>

<style scoped>
#app {
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333;
  background-color: #f5f5f5;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 紫色顶部状态栏 - 扁平化设计 */
.top-status-bar {
  height: 50px;
  background-color: #7c3aed;
  color: white;
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1000;
  border: none;
}

.status-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.system-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.system-brand {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.system-version {
  font-size: 12px;
  opacity: 0.8;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 0;
}

.status-indicators {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 0;
  flex-shrink: 0;
}

.status-dot.blue {
  background-color: #409eff;
}

.status-dot.green {
  background-color: #67c23a;
}

.status-dot.orange {
  background-color: #e6a23c;
}

.status-dot.red {
  background-color: #f56c6c;
}

.status-dot.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

.system-time {
  text-align: right;
}

.time-display {
  font-size: 14px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.runtime {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 2px;
}

/* 悬浮导航触发按钮 */
.nav-trigger {
  position: fixed;
  top: 70px;
  left: 20px;
  width: 50px;
  height: 50px;
  background-color: #ffffff;
  border: 2px solid #e1e5e9;
  border-radius: 0;
  cursor: pointer;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-trigger:hover {
  border-color: #7c3aed;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.nav-trigger.active {
  background-color: #7c3aed;
  border-color: #7c3aed;
}

.nav-trigger.active .nav-icon span {
  background-color: white;
}

.nav-icon {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-icon span {
  width: 20px;
  height: 2px;
  background-color: #666;
  transition: all 0.3s ease;
}

.nav-trigger.active .nav-icon span:nth-child(1) {
  transform: rotate(45deg) translate(6px, 6px);
}

.nav-trigger.active .nav-icon span:nth-child(2) {
  opacity: 0;
}

.nav-trigger.active .nav-icon span:nth-child(3) {
  transform: rotate(-45deg) translate(6px, -6px);
}

/* 悬浮导航面板 */
.floating-nav {
  position: fixed;
  top: 70px;
  left: 80px;
  width: 320px;
  max-height: calc(100vh - 120px);
  background-color: white;
  border: 2px solid #e1e5e9;
  border-radius: 0;
  z-index: 1002;
  transform: translateX(-100%);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.floating-nav.show {
  transform: translateX(0);
  opacity: 1;
  visibility: visible;
}

.nav-header {
  padding: 16px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e1e5e9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.close-btn:hover {
  color: #333;
}

.nav-grid {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  background-color: #ffffff;
  border: 2px solid #e1e5e9;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item:hover {
  border-color: #7c3aed;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.15);
}

.nav-item.active {
  border-color: #7c3aed;
  background-color: #faf5ff;
}

.nav-icon-container {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 0;
}

.nav-item-icon {
  font-size: 24px;
  color: white;
}

.nav-item-label {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  text-align: center;
}

.nav-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: #f56c6c;
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 0;
  min-width: 16px;
  text-align: center;
}

/* 遮罩层 */
.nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 999;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.nav-overlay.show {
  opacity: 1;
  visibility: visible;
}

/* 主要内容区域 */
.app-main {
  flex: 1;
  overflow: hidden;
  background-color: #ffffff;
}

.content-wrapper {
  width: 100%;
  height: 100%;
  overflow: auto;
}

/* 10.1寸屏幕适配 */
@media screen and (min-width: 1280px) and (max-width: 1366px) {
  .floating-nav {
    width: 380px;
  }

  .nav-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .nav-item {
    padding: 16px 12px;
  }

  .nav-icon-container {
    width: 40px;
    height: 40px;
  }

  .nav-item-icon {
    font-size: 20px;
  }
}

/* 触摸屏优化 */
@media (hover: none) and (pointer: coarse) {
  .nav-trigger {
    width: 60px;
    height: 60px;
  }

  .nav-item {
    padding: 24px 16px;
  }

  .nav-item:hover {
    transform: none;
    box-shadow: none;
  }

  .nav-item:active {
    transform: scale(0.95);
  }
}
</style>