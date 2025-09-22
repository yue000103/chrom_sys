<template>
    <div class="rack-config">
        <!-- 操作工具栏 -->
        <div class="toolbar">
            <div class="toolbar-left">
                <p class="toolbar-description">管理试管架的配置信息</p>
            </div>
            <div class="toolbar-right">
                <el-button
                    type="primary"
                    @click="showAddDialog = true"
                    icon="Plus"
                >
                    新增试管架
                </el-button>
                <el-button @click="refreshData" icon="Refresh">
                    刷新
                </el-button>
            </div>
        </div>

        <!-- 搜索栏 -->
        <div class="search-bar">
            <el-input
                v-model="searchText"
                placeholder="搜索试管架编号、名称..."
                clearable
                style="width: 300px"
            >
                <template #prefix>
                    <el-icon><Search /></el-icon>
                </template>
            </el-input>
        </div>

        <!-- 数据表格 -->
        <el-table
            :data="filteredRacks"
            v-loading="loading"
            stripe
            class="rack-table"
            empty-text="暂无试管架数据"
        >
            <el-table-column
                prop="rack_id"
                label="试管架编号"
                width="150"
                fixed="left"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <div class="rack-name">
                        <el-tag type="primary" size="small">
                            {{ scope.row.rack_id }}
                        </el-tag>
                    </div>
                </template>
            </el-table-column>

            <el-table-column
                prop="tube_count"
                label="试管数量"
                width="120"
                align="center"
            >
                <template #default="scope">
                    <el-text type="primary" style="font-weight: 600">
                        {{ scope.row.tube_count || "-" }} 支
                    </el-text>
                </template>
            </el-table-column>

            <el-table-column
                prop="tube_volume_ml"
                label="试管容量"
                width="120"
                align="center"
            >
                <template #default="scope">
                    <el-text type="info">
                        {{ scope.row.tube_volume_ml || "-" }} ml
                    </el-text>
                </template>
            </el-table-column>

            <el-table-column
                prop="status"
                label="状态"
                width="120"
                align="center"
            >
                <template #default="scope">
                    <el-tag
                        :type="scope.row.status === '使用' ? 'success' : 'info'"
                        size="small"
                    >
                        {{ scope.row.status }}
                    </el-tag>
                </template>
            </el-table-column>

            <el-table-column
                prop="created_at"
                label="创建时间"
                width="160"
                sortable
            >
                <template #default="scope">
                    <span>{{ formatDate(scope.row.created_at) }}</span>
                </template>
            </el-table-column>

            <el-table-column
                prop="rack_name"
                label="试管架名称"
                min-width="150"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <span>{{ scope.row.rack_name || "-" }}</span>
                </template>
            </el-table-column>

            <el-table-column label="操作" width="280" fixed="right">
                <template #default="scope">
                    <el-button
                        size="small"
                        @click="editRack(scope.row)"
                        icon="Edit"
                    >
                        编辑
                    </el-button>
                    <el-button
                        size="small"
                        :type="scope.row.status === '使用' ? 'warning' : 'success'"
                        @click="toggleRackStatus(scope.row)"
                        :disabled="loading"
                    >
                        {{ scope.row.status === '使用' ? '停用' : '启用' }}
                    </el-button>
                    <el-button
                        size="small"
                        type="danger"
                        @click="confirmDelete(scope.row)"
                        icon="Delete"
                        :disabled="scope.row.status === '使用'"
                    >
                        删除
                    </el-button>
                </template>
            </el-table-column>
        </el-table>

        <!-- 新增/编辑试管架对话框 -->
        <el-dialog
            v-model="showAddDialog"
            :title="isEdit ? '编辑试管架' : '新增试管架'"
            width="600px"
            :before-close="handleClose"
        >
            <el-form
                :model="rackForm"
                :rules="formRules"
                ref="rackFormRef"
                label-width="120px"
            >
                <el-form-item label="试管架名称" prop="rack_name">
                    <el-input
                        v-model="rackForm.rack_name"
                        placeholder="请输入试管架名称，如：主试管架1"
                    />
                </el-form-item>

                <el-form-item label="试管数量" prop="tube_count">
                    <el-input-number
                        v-model="rackForm.tube_count"
                        :min="1"
                        :max="200"
                        placeholder="试管架试管数量"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="试管容量(ml)" prop="tube_volume_ml">
                    <el-input-number
                        v-model="rackForm.tube_volume_ml"
                        :min="1"
                        :max="1000"
                        placeholder="单个试管容量"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="状态" prop="status">
                    <el-select v-model="rackForm.status" placeholder="选择试管架状态">
                        <el-option label="未使用" value="未使用" />
                        <el-option label="使用" value="使用" />
                    </el-select>
                </el-form-item>

            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="handleClose">取消</el-button>
                    <el-button type="primary" @click="submitForm">
                        {{ isEdit ? "更新" : "创建" }}
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

export default {
    name: "RackConfig",
    setup() {
        // 响应式数据
        const racks = ref([]);
        const loading = ref(false);
        const searchText = ref("");
        const showAddDialog = ref(false);
        const isEdit = ref(false);
        const rackFormRef = ref(null);

        // 表单数据
        const rackForm = reactive({
            rack_name: "",
            tube_count: 40,
            tube_volume_ml: 50,
            status: "未使用",
        });

        // 表单验证规则
        const formRules = {
            rack_name: [
                {
                    required: true,
                    message: "请输入试管架名称",
                    trigger: "blur",
                },
                {
                    min: 1,
                    max: 100,
                    message: "长度在 1 到 100 个字符",
                    trigger: "blur",
                },
            ],
            tube_count: [
                {
                    required: true,
                    message: "请输入试管数量",
                    trigger: "blur",
                },
            ],
            tube_volume_ml: [
                {
                    required: true,
                    message: "请输入试管容量",
                    trigger: "blur",
                },
            ],
            status: [
                {
                    required: true,
                    message: "请选择试管架状态",
                    trigger: "change",
                },
            ],
        };

        // 过滤数据
        const filteredRacks = computed(() => {
            let filtered = racks.value;

            // 搜索过滤
            if (searchText.value) {
                const search = searchText.value.toLowerCase();
                filtered = filtered.filter(
                    (rack) =>
                        (rack.rack_id || "").toLowerCase().includes(search) ||
                        (rack.rack_name || "").toLowerCase().includes(search)
                );
            }

            return filtered;
        });

        // 方法
        const fetchRacks = async () => {
            loading.value = true;
            try {
                const response = await fetch("http://0.0.0.0:8008/api/racks/");
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.rack_list) {
                        racks.value = data.rack_list;
                        console.log(
                            "获取试管架数据成功:",
                            data.message,
                            "总数:",
                            data.total_count
                        );
                    } else {
                        throw new Error(data.message || "获取数据失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("获取试管架数据失败:", error);
                ElMessage.error("获取试管架数据失败: " + error.message);
                // 发生错误时使用模拟数据作为后备
                racks.value = [
                    {
                        rack_id: 1,
                        rack_name: "主试管架1",
                        tube_count: 40,
                        tube_volume_ml: 50,
                        status: "使用",
                        created_at: "2024-01-15T10:30:00",
                    },
                    {
                        rack_id: 2,
                        rack_name: "备用试管架",
                        tube_count: 60,
                        tube_volume_ml: 100,
                        status: "未使用",
                        created_at: "2024-01-16T14:20:00",
                    },
                    {
                        rack_id: 3,
                        rack_name: "标准试管架",
                        tube_count: 40,
                        tube_volume_ml: 50,
                        status: "未使用",
                        created_at: "2024-01-10T09:15:00",
                    },
                ];
            } finally {
                loading.value = false;
            }
        };

        const refreshData = () => {
            fetchRacks();
        };

        const resetForm = () => {
            Object.assign(rackForm, {
                rack_name: "",
                tube_count: 40,
                tube_volume_ml: 50,
                status: "未使用",
            });
        };

        const editRack = (row) => {
            isEdit.value = true;
            Object.assign(rackForm, row);
            showAddDialog.value = true;
        };

        const toggleRackStatus = async (row) => {
            try {
                const newStatus = row.status === "使用" ? "未使用" : "使用";

                if (newStatus === "使用") {
                    // 检查是否已有正在使用的试管架
                    const currentActiveRack = racks.value.find(rack =>
                        rack.status === "使用" && rack.rack_id !== row.rack_id
                    );

                    if (currentActiveRack) {
                        await ElMessageBox.confirm(
                            `当前试管架 "${currentActiveRack.rack_name}" 正在使用中。\n启用 "${row.rack_name}" 将自动停用当前使用的试管架。\n\n确定要继续吗？`,
                            "试管架使用确认",
                            {
                                confirmButtonText: "确定启用",
                                cancelButtonText: "取消",
                                type: "warning",
                                dangerouslyUseHTMLString: true
                            }
                        );
                    } else {
                        await ElMessageBox.confirm(
                            `确定要启用试管架 "${row.rack_name}" 吗？`,
                            "启用确认",
                            {
                                confirmButtonText: "确定启用",
                                cancelButtonText: "取消",
                                type: "info"
                            }
                        );
                    }
                } else {
                    await ElMessageBox.confirm(
                        `确定要停用试管架 "${row.rack_name}" 吗？`,
                        "停用确认",
                        {
                            confirmButtonText: "确定停用",
                            cancelButtonText: "取消",
                            type: "warning"
                        }
                    );
                }

                // 调用API更新状态
                await updateRackStatus(row.rack_id, newStatus);

            } catch (error) {
                // 用户取消或操作失败
                console.log("状态切换操作取消或失败");
            }
        };

        const updateRackStatus = async (rackId, status) => {
            try {
                const response = await fetch(`http://0.0.0.0:8008/api/racks/${rackId}/status`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success(data.message || `试管架状态已更新为: ${status}`);
                        fetchRacks(); // 刷新列表
                    } else {
                        throw new Error(data.message || '状态更新失败');
                    }
                } else {
                    throw new Error('API请求失败');
                }
            } catch (error) {
                console.error('更新试管架状态失败:', error);
                ElMessage.error('更新试管架状态失败: ' + error.message);
                throw error;
            }
        };

        const confirmDelete = (row) => {
            if (row.status === "使用") {
                ElMessage.warning("正在使用的试管架不能删除，请先停用后再删除");
                return;
            }

            ElMessageBox.confirm(
                `确定要删除试管架 "${row.rack_name || row.rack_id}" 吗？此操作不可撤销。`,
                "删除确认",
                {
                    confirmButtonText: "确定删除",
                    cancelButtonText: "取消",
                    type: "warning",
                }
            )
                .then(() => {
                    deleteRack(row.rack_id);
                })
                .catch(() => {
                    // 用户取消
                });
        };

        const deleteRack = async (rackId) => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/racks/${rackId}`,
                    {
                        method: "DELETE",
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success(data.message || "删除成功");
                        fetchRacks();
                    } else {
                        throw new Error(data.message || "删除失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("删除试管架失败:", error);
                ElMessage.error("删除失败: " + error.message);
            }
        };

        const submitForm = () => {
            rackFormRef.value.validate((valid) => {
                if (valid) {
                    if (isEdit.value) {
                        updateRack();
                    } else {
                        createRack();
                    }
                }
            });
        };

        const createRack = async () => {
            try {
                // 如果是创建新的使用中试管架，需要确认
                if (rackForm.status === "使用") {
                    const currentActiveRack = racks.value.find(rack => rack.status === "使用");

                    if (currentActiveRack) {
                        await ElMessageBox.confirm(
                            `当前试管架 "${currentActiveRack.rack_name}" 正在使用中。\n创建新的使用中试管架将自动停用当前使用的试管架。\n\n确定要继续吗？`,
                            "试管架使用确认",
                            {
                                confirmButtonText: "确定创建",
                                cancelButtonText: "取消",
                                type: "warning",
                                dangerouslyUseHTMLString: true
                            }
                        );
                    } else {
                        await ElMessageBox.confirm(
                            `确定要创建使用中的试管架 "${rackForm.rack_name}" 吗？`,
                            "创建确认",
                            {
                                confirmButtonText: "确定创建",
                                cancelButtonText: "取消",
                                type: "info"
                            }
                        );
                    }
                }

                const requestData = {
                    rack_name: rackForm.rack_name,
                    tube_count: rackForm.tube_count,
                    tube_volume_ml: rackForm.tube_volume_ml,
                    status: rackForm.status,
                };

                const response = await fetch("http://0.0.0.0:8008/api/racks/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(requestData),
                });

                if (response.ok) {
                    const data = await response.json();
                    ElMessage.success("创建成功");
                    handleClose();
                    fetchRacks();
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.message || "创建失败");
                }
            } catch (error) {
                console.error("创建试管架失败:", error);
                ElMessage.error("创建失败: " + error.message);
            }
        };

        const updateRack = async () => {
            try {
                // 如果正在编辑状态并且改为使用中，需要确认
                const originalRack = racks.value.find(r => r.rack_id === rackForm.rack_id);
                if (originalRack && originalRack.status !== rackForm.status && rackForm.status === "使用") {
                    const currentActiveRack = racks.value.find(rack =>
                        rack.status === "使用" && rack.rack_id !== rackForm.rack_id
                    );

                    if (currentActiveRack) {
                        await ElMessageBox.confirm(
                            `当前试管架 "${currentActiveRack.rack_name}" 正在使用中。\n更新 "${rackForm.rack_name}" 为使用状态将自动停用当前使用的试管架。\n\n确定要继续吗？`,
                            "试管架使用确认",
                            {
                                confirmButtonText: "确定更新",
                                cancelButtonText: "取消",
                                type: "warning",
                                dangerouslyUseHTMLString: true
                            }
                        );
                    } else {
                        await ElMessageBox.confirm(
                            `确定要将试管架 "${rackForm.rack_name}" 更新为使用状态吗？`,
                            "更新确认",
                            {
                                confirmButtonText: "确定更新",
                                cancelButtonText: "取消",
                                type: "info"
                            }
                        );
                    }
                }

                const response = await fetch(
                    `http://0.0.0.0:8008/api/racks/${rackForm.rack_id}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(rackForm),
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success(data.message || "更新成功");
                        handleClose();
                        fetchRacks();
                    } else {
                        throw new Error(data.message || "更新失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("更新试管架失败:", error);
                ElMessage.error("更新失败: " + error.message);
            }
        };

        const handleClose = () => {
            showAddDialog.value = false;
            isEdit.value = false;
            resetForm();
            if (rackFormRef.value) {
                rackFormRef.value.resetFields();
            }
        };

        const formatDate = (dateString) => {
            if (!dateString) return "-";
            return new Date(dateString).toLocaleString("zh-CN");
        };

        // 生命周期
        onMounted(() => {
            fetchRacks();
        });

        return {
            racks,
            loading,
            searchText,
            showAddDialog,
            isEdit,
            rackForm,
            rackFormRef,
            formRules,
            filteredRacks,
            fetchRacks,
            refreshData,
            editRack,
            toggleRackStatus,
            updateRackStatus,
            confirmDelete,
            submitForm,
            handleClose,
            formatDate,
        };
    },
};
</script>

<style scoped>
.rack-config {
    padding: 24px;
    background: white;
}

.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
}

.toolbar-left h3 {
    margin: 0 0 4px 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
}

.toolbar-description {
    margin: 0;
    font-size: 14px;
    color: #606266;
}

.toolbar-right {
    display: flex;
    gap: 12px;
}

.search-bar {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
}

.rack-table {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    overflow: hidden;
}

:deep(.el-table__header) {
    background-color: #f8f9fa;
}

:deep(.el-table__header th) {
    background-color: #f8f9fa !important;
    color: #606266;
    font-weight: 600;
}

.rack-name {
    display: flex;
    align-items: center;
}

.occupancy-view {
    padding: 16px;
}

.rack-info {
    margin-bottom: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
}

.rack-info h4 {
    margin: 0 0 8px 0;
    color: #303133;
}

.rack-info p {
    margin: 4px 0;
    color: #666;
}

.rack-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;
    margin-bottom: 20px;
    max-height: 400px;
    overflow-y: auto;
}

.slot {
    width: 40px;
    height: 40px;
    border: 2px solid #ddd;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
}

.slot:hover {
    border-color: #409eff;
    transform: scale(1.05);
}

.slot.occupied {
    background-color: #f56c6c;
    border-color: #f56c6c;
    color: white;
}

.slot.empty {
    background-color: #f8f9fa;
    border-color: #e4e7ed;
}

.slot-number {
    font-size: 10px;
    position: absolute;
    top: 2px;
    left: 2px;
}

.slot-content {
    font-size: 16px;
}

.occupancy-controls {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.statistics-content {
    padding: 16px;
}

.dialog-footer {
    text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .rack-config {
        padding: 16px;
    }

    .toolbar {
        flex-direction: column;
        gap: 16px;
        align-items: stretch;
    }

    .toolbar-right {
        justify-content: flex-start;
        flex-wrap: wrap;
    }

    .search-bar {
        flex-direction: column;
        gap: 10px;
        align-items: stretch;
    }

    .search-bar .el-input,
    .search-bar .el-select {
        width: 100% !important;
    }

    .rack-grid {
        grid-template-columns: repeat(8, 1fr);
    }

    .slot {
        width: 35px;
        height: 35px;
    }
}
</style>
