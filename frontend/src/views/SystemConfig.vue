<template>
    <div class="system-config">
        <!-- 页面标题 -->
        <div class="page-header">
            <h1>系统配置管理</h1>
            <p class="page-description">配置和管理色谱系统的基础参数</p>
        </div>

        <!-- 配置选项卡 -->
        <el-tabs v-model="activeTab" type="card" class="config-tabs">
            <!-- 柱子参数管理 -->
            <el-tab-pane label="柱子参数" name="columns">
                <template #label>
                    <span>
                        <el-icon><Tools /></el-icon>
                        柱子参数
                    </span>
                </template>
                <ColumnConfig />
            </el-tab-pane>

            <!-- SMILES管理 -->
            <el-tab-pane label="SMILES管理" name="smiles">
                <template #label>
                    <span>
                        <el-icon><Orange /></el-icon>
                        SMILES管理
                    </span>
                </template>
                <SmilesConfig />
            </el-tab-pane>

            <!-- 试管架管理 -->
            <el-tab-pane label="试管架管理" name="racks">
                <template #label>
                    <span>
                        <el-icon><Grid /></el-icon>
                        试管架管理
                    </span>
                </template>
                <RackConfig />
            </el-tab-pane>

        </el-tabs>
    </div>
</template>

<script>
import { ref } from 'vue'
import ColumnConfig from '../components/config/ColumnConfig.vue'
import SmilesConfig from '../components/config/SmilesConfig.vue'
import RackConfig from '../components/config/RackConfig.vue'

export default {
    name: 'SystemConfig',
    components: {
        ColumnConfig,
        SmilesConfig,
        RackConfig
    },
    setup() {
        const activeTab = ref('columns')

        return {
            activeTab
        }
    }
}
</script>

<style scoped>
.system-config {
    padding: 24px;
    min-height: 100vh;
    background: #f5f7fa;
}

.page-header {
    margin-bottom: 32px;
    padding: 24px 0;
    border-bottom: 1px solid #ebeef5;
    background: white;
    border-radius: 8px 8px 0 0;
    padding: 24px 32px;
}

.page-header h1 {
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 12px;
}

.page-description {
    margin: 0;
    font-size: 14px;
    color: #606266;
    line-height: 1.5;
}

.config-tabs {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

:deep(.el-tabs__header) {
    margin: 0;
    background: #fafafa;
    padding: 0 24px;
    border-bottom: 1px solid #ebeef5;
}

:deep(.el-tabs__nav-wrap::after) {
    display: none;
}

:deep(.el-tabs__item) {
    padding: 16px 24px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px 8px 0 0;
    margin-right: 8px;
    transition: all 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
    background: white;
    border-bottom-color: white;
    color: #409eff;
}

:deep(.el-tabs__item span) {
    display: flex;
    align-items: center;
    gap: 8px;
}

:deep(.el-tabs__content) {
    padding: 0;
}

:deep(.el-tab-pane) {
    min-height: 600px;
}


/* 响应式设计 */
@media (max-width: 768px) {
    .system-config {
        padding: 16px;
    }

    .page-header {
        padding: 16px 20px;
    }

    .page-header h1 {
        font-size: 24px;
    }

    :deep(.el-tabs__header) {
        padding: 0 16px;
    }

    :deep(.el-tabs__item) {
        padding: 12px 16px;
        font-size: 14px;
    }
}
</style>