<template>
    <div class="method-manager">
        <el-row :gutter="20">
            <!-- 方法库列表 -->
            <el-col :span="16">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>方法库</span>
                            <el-button
                                type="primary"
                                @click="showCreateMethod = true"
                            >
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
                            <el-select
                                v-model="filterType"
                                placeholder="方法类型"
                            >
                                <el-option label="全部" value="all" />
                                <el-option label="系统方法" value="system" />
                                <el-option label="用户方法" value="user" />
                                <el-option label="常用方法" value="favorite" />
                            </el-select>
                        </el-col>
                    </el-row>

                    <!-- 加载状态 -->
                    <el-skeleton
                        v-if="loading"
                        :rows="4"
                        :loading="loading"
                        animated
                        style="margin-bottom: 20px"
                    />

                    <!-- 方法卡片列表 -->
                    <div v-else class="method-grid">
                        <el-card
                            v-for="method in filteredMethods"
                            :key="method.id"
                            class="method-card"
                            :class="{
                                favorite: method.isFavorite,
                                system: method.type === 'system',
                            }"
                            shadow="hover"
                        >
                            <div class="method-header">
                                <h4>{{ method.name }}</h4>
                                <div class="method-badges">
                                    <el-tag
                                        v-if="method.isFavorite"
                                        type="warning"
                                        size="small"
                                    >
                                        <el-icon><Star /></el-icon>
                                        常用
                                    </el-tag>
                                    <el-tag
                                        v-if="method.type === 'system'"
                                        type="info"
                                        size="small"
                                    >
                                        <el-icon><Lock /></el-icon>
                                        系统
                                    </el-tag>
                                </div>
                            </div>

                            <div class="method-info">
                                <p class="description">
                                    {{ method.description || "暂无描述" }}
                                </p>
                                <div class="method-params">
                                    <span
                                        >流速: {{ method.flowRate }}mL/min</span
                                    >
                                    <span
                                        >运行时间: {{ method.runTime }}min</span
                                    >
                                    <span>波长: {{ method.wavelength }}nm</span>
                                </div>
                                <div class="method-meta">
                                    <span class="created-time"
                                        >创建:
                                        {{ formatDate(method.createdAt) }}</span
                                    >
                                    <span class="usage-count"
                                        >使用: {{ method.usageCount }}次</span
                                    >
                                </div>
                            </div>

                            <div class="method-actions">
                                <el-button
                                    size="small"
                                    @click="editMethod(method)"
                                >
                                    <el-icon><Edit /></el-icon>
                                    编辑
                                </el-button>
                                <el-button
                                    size="small"
                                    @click="copyMethod(method)"
                                >
                                    <el-icon><CopyDocument /></el-icon>
                                    复制
                                </el-button>
                                <el-button
                                    size="small"
                                    @click="exportMethod(method)"
                                >
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
                        <span>{{
                            selectedMethod ? "方法详情" : "选择方法查看详情"
                        }}</span>
                    </template>

                    <div v-if="selectedMethod" class="method-details">
                        <h3>{{ selectedMethod.name }}</h3>

                        <!-- 基本信息 -->
                        <el-divider content-position="left"
                            >基本信息</el-divider
                        >
                        <div class="detail-section">
                            <div class="detail-item">
                                <label>方法名称:</label>
                                <span>{{ selectedMethod.name }}</span>
                            </div>
                            <div class="detail-item">
                                <label>描述:</label>
                                <span>{{
                                    selectedMethod.description || "暂无"
                                }}</span>
                            </div>
                            <div class="detail-item">
                                <label>类型:</label>
                                <el-tag
                                    :type="
                                        selectedMethod.type === 'system'
                                            ? 'info'
                                            : 'success'
                                    "
                                >
                                    {{
                                        selectedMethod.type === "system"
                                            ? "制备方法"
                                            : "分析方法"
                                    }}
                                </el-tag>
                            </div>
                        </div>

                        <!-- 色谱参数 -->
                        <el-divider content-position="left"
                            >色谱参数</el-divider
                        >
                        <div class="detail-section">
                            <div class="detail-item">
                                <label>柱子:</label>
                                <span>{{ selectedMethod.column }}</span>
                            </div>
                            <div class="detail-item">
                                <label>流速:</label>
                                <span
                                    >{{ selectedMethod.flowRate }} mL/min</span
                                >
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
                        <el-divider content-position="left"
                            >梯度程序</el-divider
                        >
                        <div class="detail-section">
                            <div class="detail-item">
                                <label>梯度模式:</label>
                                <span>{{
                                    selectedMethod.gradientMode === "auto"
                                        ? "自动梯度"
                                        : "手动梯度"
                                }}</span>
                            </div>
                        </div>
                    </div>

                    <el-empty v-else description="请选择方法查看详情" />
                </el-card>
            </el-col>
        </el-row>

        <!-- 创建方法对话框 -->
        <el-dialog
            v-model="showCreateMethod"
            title="创建新方法"
            width="80%"
            :before-close="handleCloseDialog"
        >
            <MethodCreateWizard
                @save="handleSaveMethod"
                @cancel="showCreateMethod = false"
            />
        </el-dialog>

        <!-- 编辑方法对话框 -->
        <el-dialog
            v-model="showEditMethod"
            title="编辑方法"
            width="80%"
            :before-close="handleCloseDialog"
        >
            <MethodEditWizard
                :method="selectedMethod"
                @save="handleUpdateMethod"
                @cancel="showEditMethod = false"
            />
        </el-dialog>
    </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import MethodCreateWizard from "../components/method/MethodCreateWizard.vue";
import MethodEditWizard from "../components/method/MethodEditWizard.vue";

export default {
    name: "MethodManager",
    components: {
        MethodCreateWizard,
        MethodEditWizard,
    },
    setup() {
        const searchText = ref("");
        const filterType = ref("all");
        const showCreateMethod = ref(false);
        const showEditMethod = ref(false);
        const selectedMethod = ref(null);
        const loading = ref(false);

        // 方法数据
        const methods = ref([]);

        // 获取方法列表的API调用
        const fetchMethods = async () => {
            loading.value = true;
            try {
                const response = await fetch('http://localhost:8008/api/methods/?limit=50');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                if (data.success && data.methods) {
                    // 将API数据映射为组件需要的格式
                    methods.value = data.methods.map(method => {
                        // 安全地提取波长信息
                        let wavelength = method.detector_wavelength;
                        if (Array.isArray(wavelength)) {
                            wavelength = wavelength[0];
                        }
                        // 移除单位后缀进行显示
                        const wavelengthNum = typeof wavelength === 'string'
                            ? wavelength.replace(/[^0-9.]/g, '')
                            : wavelength;

                        return {
                            id: method.method_id,
                            name: method.method_name || '未命名方法',
                            description: `${method.gradient_elution_mode === 'auto' ? '自动梯度' : '手动梯度'}方法${method.gradient_time_table ? ' - 自定义时间表' : ''}`,
                            type: 'user', // 可以根据需要调整
                            isFavorite: false, // 可以根据需要调整
                            column: `Column ${method.column_id}`,
                            flowRate: method.flow_rate_ml_min || 0,
                            runTime: method.run_time_min || 0,
                            wavelength: wavelengthNum || 254,
                            gradientMode: method.gradient_elution_mode || 'manual',
                            createdAt: method.created_at ? new Date(method.created_at) : new Date(),
                            updatedAt: method.updated_at ? new Date(method.updated_at) : null,
                            usageCount: 0, // 可以根据需要调整
                            // 保留原始API数据
                            originalData: method
                        };
                    });

                    console.log('获取方法列表成功:', methods.value);
                } else {
                    throw new Error(data.message || '获取方法列表失败');
                }
            } catch (error) {
                console.error('获取方法列表失败:', error);
                ElMessage.error({
                    message: `获取方法列表失败: ${error.message}`,
                    duration: 5000,
                    showClose: true
                });

                // 如果API调用失败，使用空数据或示例数据
                if (process.env.NODE_ENV === 'development') {
                    methods.value = [
                        {
                            id: 1,
                            name: "标准分析方法-01",
                            description: "用于蛋白质分离的标准方法(演示数据)",
                            type: "system",
                            isFavorite: true,
                            column: "C18-150mm",
                            flowRate: 1.0,
                            runTime: 30,
                            wavelength: 254,
                            gradientMode: "auto",
                            createdAt: new Date("2024-01-15"),
                            usageCount: 25,
                            originalData: {
                                method_id: 1,
                                method_name: "标准分析方法-01",
                                column_id: 1,
                                flow_rate_ml_min: 1,
                                run_time_min: 30,
                                detector_wavelength: "254nm",
                                peak_driven: false,
                                gradient_elution_mode: "auto",
                                created_at: "2024-01-15T00:00:00"
                            }
                        }
                    ];
                } else {
                    methods.value = [];
                }
            } finally {
                loading.value = false;
            }
        };

        const filteredMethods = computed(() => {
            let filtered = methods.value;

            // 搜索过滤
            if (searchText.value) {
                filtered = filtered.filter(
                    (method) =>
                        method.name
                            .toLowerCase()
                            .includes(searchText.value.toLowerCase()) ||
                        (method.description &&
                            method.description
                                .toLowerCase()
                                .includes(searchText.value.toLowerCase()))
                );
            }

            // 类型过滤
            if (filterType.value !== "all") {
                if (filterType.value === "favorite") {
                    filtered = filtered.filter((method) => method.isFavorite);
                } else {
                    filtered = filtered.filter(
                        (method) => method.type === filterType.value
                    );
                }
            }

            return filtered;
        });

        const formatDate = (date) => {
            return date.toLocaleDateString("zh-CN");
        };

        const editMethod = (method) => {
            selectedMethod.value = method;
            showEditMethod.value = true;
            console.log("编辑方法:", method.name);
        };

        const copyMethod = async (method) => {
            try {
                // 获取源方法的详细信息
                const originalData = method.originalData || method;

                // 创建复制的方法数据，修改名称
                const copyData = {
                    method_name: `${originalData.method_name}_复制`,
                    column_id: originalData.column_id,
                    flow_rate_ml_min: originalData.flow_rate_ml_min,
                    run_time_min: originalData.run_time_min,
                    detector_wavelength: Array.isArray(originalData.detector_wavelength)
                        ? originalData.detector_wavelength[0]
                        : originalData.detector_wavelength,
                    peak_driven: originalData.peak_driven || false,
                    gradient_elution_mode: originalData.gradient_elution_mode || 'manual',
                    gradient_time_table: originalData.gradient_time_table || '',
                    auto_gradient_params: originalData.auto_gradient_params || ''
                };

                const response = await fetch('http://localhost:8008/api/methods/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(copyData),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    ElMessage.success(data.message || '方法复制成功');
                    // 刷新方法列表
                    await fetchMethods();
                } else {
                    throw new Error(data.message || '复制方法失败');
                }
            } catch (error) {
                console.error('复制方法失败:', error);
                ElMessage.error(error.message || '复制方法失败');
            }
        };

        const exportMethod = (method) => {
            try {
                // 生成JSON数据
                const exportData = {
                    method: method.originalData || method,
                    exportTime: new Date().toISOString(),
                    version: '1.0'
                };

                // 创建下载链接
                const dataStr = JSON.stringify(exportData, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);

                // 创建下载元素
                const link = document.createElement('a');
                link.href = url;
                link.download = `method_${method.name}_${new Date().toISOString().slice(0, 10)}.json`;

                // 触发下载
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                // 清理URL
                URL.revokeObjectURL(url);

                ElMessage.success('方法导出成功');
                console.log('导出方法:', method.name);
            } catch (error) {
                console.error('导出方法失败:', error);
                ElMessage.error('导出方法失败');
            }
        };

        const deleteMethod = async (method) => {
            try {
                await ElMessageBox.confirm(
                    `确定要删除方法 "${method.name}" 吗？此操作不可逆。`,
                    '删除确认',
                    {
                        confirmButtonText: '删除',
                        cancelButtonText: '取消',
                        type: 'warning',
                    }
                );

                const response = await fetch(`http://localhost:8008/api/methods/${method.id}`, {
                    method: 'DELETE',
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    ElMessage.success(data.message || '方法删除成功');
                    // 从列表中移除已删除的方法
                    methods.value = methods.value.filter(m => m.id !== method.id);
                    // 如果删除的是当前选中的方法，清除选择
                    if (selectedMethod.value && selectedMethod.value.id === method.id) {
                        selectedMethod.value = null;
                    }
                } else {
                    throw new Error(data.message || '删除方法失败');
                }
            } catch (error) {
                if (error.message !== 'cancel') {
                    console.error('删除方法失败:', error);
                    ElMessage.error(error.message || '删除方法失败');
                }
            }
        };

        const handleSaveMethod = async (methodData) => {
            const loadingMessage = ElMessage({
                message: '正在创建方法...',
                type: 'info',
                duration: 0, // 不自动关闭
                showClose: false
            });

            try {
                // 数据映射：将前端数据映射到API期望的格式（与编辑方法保持一致）
                const apiData = {
                    method_name: methodData.name || methodData.method_name,
                    column_id: methodData.column_id,
                    flow_rate_ml_min: methodData.flowRate || methodData.flow_rate_ml_min || 1,
                    run_time_min: methodData.runTime || methodData.run_time_min || 30,
                    detector_wavelength: `${methodData.wavelengthA || methodData.detector_wavelength || 254}nm`,
                    peak_driven: false, // 根据需要设置
                    gradient_elution_mode: methodData.gradientMode || methodData.gradient_elution_mode || 'auto',
                    gradient_time_table: methodData.gradientMode === 'manual' && methodData.manualGradient
                        ? methodData.manualGradient.map(row =>
                            `${row.time}:${row.solutionA}:${row.solutionB}:${row.solutionC}:${row.solutionD}`
                          ).join(',')
                        : (methodData.gradient_time_table || ''),
                    auto_gradient_params: methodData.gradientMode === 'auto' && methodData.autoGradient
                        ? JSON.stringify(methodData.autoGradient)
                        : (methodData.auto_gradient_params || '')
                };

                // 验证必需字段
                if (!apiData.column_id) {
                    throw new Error('请选择色谱柱');
                }
                if (!apiData.method_name) {
                    throw new Error('请输入方法名称');
                }

                console.log('发送创建请求数据:', apiData);

                const response = await fetch('http://localhost:8008/api/methods/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(apiData),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || `HTTP error! status: ${response.status}`);
                }

                if (data.success) {
                    ElMessage.success({
                        message: data.message || '方法创建成功',
                        duration: 3000
                    });
                    showCreateMethod.value = false;
                    // 刷新方法列表
                    await fetchMethods();
                } else {
                    throw new Error(data.message || '创建方法失败');
                }
            } catch (error) {
                console.error('保存方法失败:', error);
                ElMessage.error({
                    message: error.message || '保存方法失败',
                    duration: 5000,
                    showClose: true
                });
            } finally {
                loadingMessage.close();
            }
        };

        const handleUpdateMethod = async (methodData) => {
            const loadingMessage = ElMessage({
                message: '正在更新方法...',
                type: 'info',
                duration: 0,
                showClose: false
            });

            try {
                console.log('更新方法数据:', methodData);
                console.log('选中的方法ID:', selectedMethod.value.id);

                const response = await fetch(`http://localhost:8008/api/methods/${selectedMethod.value.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(methodData),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || `HTTP error! status: ${response.status}`);
                }

                if (data.success) {
                    ElMessage.success({
                        message: data.message || '方法更新成功',
                        duration: 3000
                    });
                    showEditMethod.value = false;
                    // 刷新方法列表
                    await fetchMethods();

                    // 更新选中的方法信息
                    if (data.method) {
                        const updatedMethod = methods.value.find(m => m.id === selectedMethod.value.id);
                        if (updatedMethod) {
                            selectedMethod.value = updatedMethod;
                        }
                    }
                } else {
                    throw new Error(data.message || '更新方法失败');
                }
            } catch (error) {
                console.error('更新方法失败:', error);
                ElMessage.error({
                    message: error.message || '更新方法失败',
                    duration: 5000,
                    showClose: true
                });
            } finally {
                loadingMessage.close();
            }
        };

        const handleCloseDialog = (done) => {
            done();
        };

        onMounted(async () => {
            // 获取方法列表
            await fetchMethods();

            // 默认选择第一个方法
            if (methods.value.length > 0) {
                selectedMethod.value = methods.value[0];
            }
        });

        return {
            searchText,
            filterType,
            showCreateMethod,
            showEditMethod,
            selectedMethod,
            methods,
            loading,
            filteredMethods,
            formatDate,
            editMethod,
            copyMethod,
            exportMethod,
            deleteMethod,
            handleSaveMethod,
            handleUpdateMethod,
            handleCloseDialog,
            fetchMethods,
        };
    },
};
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
