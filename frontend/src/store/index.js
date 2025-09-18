import { createPinia } from 'pinia'

// 导入所有store模块
import { useExperimentStore } from './modules/experiment'
import { useDeviceStore } from './modules/device'
import { useDataStore } from './modules/data'
import { useConfigStore } from './modules/config'
import { useAlarmStore } from './modules/alarm'

// 创建pinia实例
const pinia = createPinia()

// 添加持久化插件（可选）
pinia.use(({ store }) => {
  // 在这里可以添加全局插件，比如持久化存储
  const storeName = store.$id

  // 监听状态变化，自动保存到localStorage
  store.$subscribe((mutation, state) => {
    // 只保存特定的store到localStorage
    if (['config', 'experiment'].includes(storeName)) {
      try {
        localStorage.setItem(`pinia_${storeName}`, JSON.stringify(state))
      } catch (error) {
        console.warn(`无法保存 ${storeName} 状态到localStorage:`, error)
      }
    }
  })

  // 从localStorage恢复状态
  const savedState = localStorage.getItem(`pinia_${storeName}`)
  if (savedState) {
    try {
      const parsedState = JSON.parse(savedState)
      store.$patch(parsedState)
    } catch (error) {
      console.warn(`无法从localStorage恢复 ${storeName} 状态:`, error)
    }
  }
})

// 导出pinia实例和所有store
export {
  pinia,
  useExperimentStore,
  useDeviceStore,
  useDataStore,
  useConfigStore,
  useAlarmStore
}

// 默认导出pinia实例
export default pinia