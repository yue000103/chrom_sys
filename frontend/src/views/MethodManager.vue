<template>
  <div class="method-manager">
    <el-row :gutter="20">
      <!-- 方法库列表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>方法库</span>
              <el-button type="primary" @click="showCreateMethod = true">
                <el-icon><Plus /></el-icon>
                创建方法
              </el-button>
            </div>
          </template>

          <!-- 搜索和筛选 -->
          <el-row :gutter="20" class="mb-3">
            <el-col :span="12">
              <el-input
                v-model="searchText"
                placeholder="搜索方法名称..."
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-select v-model="filterType" placeholder="方法类型">
                <el-option label="全部" value="all" />
                <el-option label="系统方法" value="system" />
                <el-option label="用户方法" value="user" />
                <el-option label="常用方法" value="favorite" />
              </el-select>
            </el-col>
          </el-row>

          <!-- 方法卡片列表 -->
          <div class="method-grid">
            <el-card
              v-for="method in filteredMethods"
              :key="method.id"
              class="method-card"
              :class="{ 'favorite': method.isFavorite, 'system': method.type === 'system' }"
              shadow="hover"
            >
              <div class="method-header">
                <h4>{{ method.name }}</h4>
                <div class="method-badges">
                  <el-tag v-if="method.isFavorite" type="warning" size="small">
                    <el-icon><Star /></el-icon>
                    常用
                  </el-tag>
                  <el-tag v-if="method.type === 'system'" type="info" size="small">
                    <el-icon><Lock /></el-icon>
                    系统
                  </el-tag>
                </div>
              </div>

              <div class="method-info">
                <p class="description">{{ method.description || '暂无描述' }}</p>
                <div class="method-params">
                  <span>流速: {{ method.flowRate }}mL/min</span>
                  <span>运行时间: {{ method.runTime }}min</span>
                  <span>波长: {{ method.wavelength }}nm</span>
                </div>
                <div class="method-meta">
                  <span class="created-time">创建: {{ formatDate(method.createdAt) }}</span>
                  <span class="usage-count">使用: {{ method.usageCount }}次</span>
                </div>
              </div>

              <div class="method-actions">
                <el-button size="small" @click="editMethod(method)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" @click="copyMethod(method)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="exportMethod(method)">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteMethod(method)"
                  :disabled="method.type === 'system'"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-col>

      <!-- 方法详情/编辑面板 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>{{ selectedMethod ? '方法详情' : '选择方法查看详情' }}</span>
          </template>

          <div v-if="selectedMethod" class="method-details">
            <h3>{{ selectedMethod.name }}</h3>

            <!-- 基本信息 -->
            <el-divider content-position="left">基本信息</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>方法名称:</label>
                <span>{{ selectedMethod.name }}</span>
              </div>
              <div class="detail-item">
                <label>描述:</label>
                <span>{{ selectedMethod.description || '暂无' }}</span>
              </div>
              <div class="detail-item">
                <label>类型:</label>
                <el-tag :type="selectedMethod.type === 'system' ? 'info' : 'success'">
                  {{ selectedMethod.type === 'system' ? '系统方法' : '用户方法' }}
                </el-tag>
              </div>
            </div>

            <!-- 色谱参数 -->
            <el-divider content-position="left">色谱参数</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>柱子:</label>
                <span>{{ selectedMethod.column }}</span>
              </div>
              <div class="detail-item">
                <label>流速:</label>
                <span>{{ selectedMethod.flowRate }} mL/min</span>
              </div>
              <div class="detail-item">
                <label>运行时间:</label>
                <span>{{ selectedMethod.runTime }} min</span>
              </div>
              <div class="detail-item">
                <label>检测波长:</label>
                <span>{{ selectedMethod.wavelength }} nm</span>
              </div>
            </div>

            <!-- 梯度信息 -->
            <el-divider content-position="left">梯度程序</el-divider>
            <div class="detail-section">
              <div class="detail-item">
                <label>梯度模式:</label>
                <span>{{ selectedMethod.gradientMode === 'auto' ? '自动梯度' : '手动梯度' }}</span>
              </div>
            </div>
          </div>

          <el-empty v-else description="请选择方法查看详情" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑方法对话框 -->
    <el-dialog
      v-model="showCreateMethod"
      title="创建新方法"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <MethodCreateWizard @save="handleSaveMethod" @cancel="showCreateMethod = false" />
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import MethodCreateWizard from '../components/method/MethodCreateWizard.vue'

export default {
  name: 'MethodManager',
  components: {
    MethodCreateWizard
  },
  setup() {
    const searchText = ref('')
    const filterType = ref('all')
    const showCreateMethod = ref(false)
    const selectedMethod = ref(null)

    // 模拟方法数据
    const methods = ref([
      {
        id: 1,
        name: '标准分析方法-01',
        description: '用于蛋白质分离的标准方法',
        type: 'system',
        isFavorite: true,
        column: 'C18-150mm',
        flowRate: 1.0,
        runTime: 30,
        wavelength: 254,
        gradientMode: 'auto',
        createdAt: new Date('2024-01-15'),
        usageCount: 25
      },
      {
        id: 2,
        name: '快速检测方法',
        description: '用于快速样品筛选',
        type: 'user',
        isFavorite: false,
        column: 'C18-100mm',
        flowRate: 1.5,
        runTime: 15,
        wavelength: 280,
        gradientMode: 'manual',
        createdAt: new Date('2024-02-20'),
        usageCount: 12
      },
      {
        id: 3,
        name: '高分辨分离方法',
        description: '用于复杂样品的高分辨分离',
        type: 'user',
        isFavorite: true,
        column: 'C18-250mm',
        flowRate: 0.8,
        runTime: 60,
        wavelength: 254,
        gradientMode: 'auto',
        createdAt: new Date('2024-03-10'),
        usageCount: 8
      }
    ])

    const filteredMethods = computed(() => {
      let filtered = methods.value

      // 搜索过滤
      if (searchText.value) {
        filtered = filtered.filter(method =>
          method.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
          (method.description && method.description.toLowerCase().includes(searchText.value.toLowerCase()))
        )
      }

      // 类型过滤
      if (filterType.value !== 'all') {
        if (filterType.value === 'favorite') {
          filtered = filtered.filter(method => method.isFavorite)
        } else {
          filtered = filtered.filter(method => method.type === filterType.value)
        }
      }

      return filtered
    })

    const formatDate = (date) => {
      return date.toLocaleDateString('zh-CN')
    }

    const editMethod = (method) => {
      selectedMethod.value = method
      console.log('编辑方法:', method.name)
    }

    const copyMethod = (method) => {
      console.log('复制方法:', method.name)
    }

    const exportMethod = (method) => {
      console.log('导出方法:', method.name)
    }

    const deleteMethod = (method) => {
      console.log('删除方法:', method.name)
    }

    const handleSaveMethod = (methodData) => {
      console.log('保存方法:', methodData)
      showCreateMethod.value = false
    }

    const handleCloseDialog = (done) => {
      done()
    }

    onMounted(() => {
      // 默认选择第一个方法
      if (methods.value.length > 0) {
        selectedMethod.value = methods.value[0]
      }
    })

    return {
      searchText,
      filterType,
      showCreateMethod,
      selectedMethod,
      methods,
      filteredMethods,
      formatDate,
      editMethod,
      copyMethod,
      exportMethod,
      deleteMethod,
      handleSaveMethod,
      handleCloseDialog
    }
  }
}
</script>

<style scoped>
.method-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mb-3 {
  margin-bottom: 20px;
}

.method-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.method-card {
  transition: all 0.3s ease;
}

.method-card:hover {
  transform: translateY(-2px);
}

.method-card.favorite {
  border-left: 4px solid #f39c12;
}

.method-card.system {
  border-left: 4px solid #3498db;
}

.method-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.method-header h4 {
  margin: 0;
  color: #333;
}

.method-badges {
  display: flex;
  gap: 4px;
}

.method-info {
  margin-bottom: 16px;
}

.description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.method-params {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.method-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.method-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.method-details {
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
</style>