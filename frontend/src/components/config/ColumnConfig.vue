<template>
    <div class="column-config">
        <!-- 操作工具栏 -->
        <div class="toolbar">
            <div class="toolbar-left">
                <h3>柱子参数管理</h3>
                <p class="toolbar-description">
                    管理色谱柱的技术参数和规格信息
                </p>
            </div>
            <div class="toolbar-right">
                <el-button
                    type="primary"
                    @click="showAddDialog = true"
                    icon="Plus"
                >
                    新增柱子
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
                placeholder="搜索柱子编号、规格..."
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
            :data="filteredColumns"
            v-loading="loading"
            stripe
            class="column-table"
            empty-text="暂无柱子参数数据"
        >
            <el-table-column
                prop="column_code"
                label="柱子编号"
                width="120"
                fixed="left"
            >
                <template #default="scope">
                    <el-tag type="primary" size="small">
                        {{ scope.row.column_code }}
                    </el-tag>
                </template>
            </el-table-column>

            <el-table-column
                prop="specification_g"
                label="规格(g)"
                width="100"
                sortable
            >
                <template #default="scope">
                    <span>{{ scope.row.specification_g || "-" }}</span>
                </template>
            </el-table-column>

            <el-table-column
                prop="max_pressure_bar"
                label="最大压力(bar)"
                width="180"
                sortable
            >
                <template #default="scope">
                    <el-text
                        :type="
                            scope.row.max_pressure_bar > 200
                                ? 'danger'
                                : 'success'
                        "
                        style="font-weight: 600"
                    >
                        {{ scope.row.max_pressure_bar || "-" }}
                    </el-text>
                </template>
            </el-table-column>

            <el-table-column
                prop="flow_rate_ml_min"
                label="流速(ml/min)"
                width="150"
                sortable
            >
                <template #default="scope">
                    <span>{{ scope.row.flow_rate_ml_min || "-" }}</span>
                </template>
            </el-table-column>

            <el-table-column
                prop="column_volume_cv_ml"
                label="柱体积(ml)"
                width="120"
                sortable
            >
                <template #default="scope">
                    <span>{{ scope.row.column_volume_cv_ml || "-" }}</span>
                </template>
            </el-table-column>

            <el-table-column
                prop="sample_load_amount"
                label="样品装载量"
                width="140"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <span>{{ scope.row.sample_load_amount || "-" }}</span>
                </template>
            </el-table-column>

            <el-table-column
                prop="created_at"
                label="创建时间"
                width="180"
                sortable
            >
                <template #default="scope">
                    <span>{{ formatDate(scope.row.created_at) }}</span>
                </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                    <el-button
                        size="small"
                        @click="editColumn(scope.row)"
                        icon="Edit"
                    >
                        编辑
                    </el-button>
                    <el-button
                        size="small"
                        type="danger"
                        @click="confirmDelete(scope.row)"
                        icon="Delete"
                    >
                        删除
                    </el-button>
                </template>
            </el-table-column>
        </el-table>

        <!-- 新增/编辑柱子对话框 -->
        <el-dialog
            v-model="showAddDialog"
            :title="isEdit ? '编辑柱子参数' : '新增柱子参数'"
            width="600px"
            :before-close="handleClose"
        >
            <el-form
                :model="columnForm"
                :rules="formRules"
                ref="columnFormRef"
                label-width="120px"
            >
                <el-form-item label="柱子编号" prop="column_code">
                    <el-input
                        v-model="columnForm.column_code"
                        placeholder="请输入柱子编号，如：COL001"
                    />
                </el-form-item>

                <el-form-item label="规格(g)" prop="specification_g">
                    <el-input-number
                        v-model="columnForm.specification_g"
                        :min="1"
                        :max="1000"
                        placeholder="规格重量"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="最大压力(bar)" prop="max_pressure_bar">
                    <el-input-number
                        v-model="columnForm.max_pressure_bar"
                        :min="1"
                        :max="1000"
                        placeholder="最大承受压力"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="流速(ml/min)" prop="flow_rate_ml_min">
                    <el-input-number
                        v-model="columnForm.flow_rate_ml_min"
                        :min="0.01"
                        :max="50"
                        :step="0.01"
                        :precision="2"
                        placeholder="推荐流速"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="柱体积(ml)" prop="column_volume_cv_ml">
                    <el-input-number
                        v-model="columnForm.column_volume_cv_ml"
                        :min="0.1"
                        :max="200"
                        :step="0.1"
                        :precision="1"
                        placeholder="柱内体积"
                        style="width: 100%"
                    />
                </el-form-item>

                <el-form-item label="样品装载量" prop="sample_load_amount">
                    <el-input
                        v-model="columnForm.sample_load_amount"
                        placeholder="如：1-10mg, 50-500μL等"
                    />
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
    name: "ColumnConfig",
    setup() {
        // 响应式数据
        const columns = ref([]);
        const loading = ref(false);
        const searchText = ref("");
        const showAddDialog = ref(false);
        const isEdit = ref(false);
        const columnFormRef = ref(null);

        // 表单数据
        const columnForm = reactive({
            column_id: null,
            column_code: "",
            specification_g: null,
            max_pressure_bar: null,
            flow_rate_ml_min: null,
            column_volume_cv_ml: null,
            sample_load_amount: "",
        });

        // 表单验证规则
        const formRules = {
            column_code: [
                { required: true, message: "请输入柱子编号", trigger: "blur" },
                {
                    min: 2,
                    max: 20,
                    message: "长度在 2 到 20 个字符",
                    trigger: "blur",
                },
            ],
            max_pressure_bar: [
                { required: true, message: "请输入最大压力", trigger: "blur" },
            ],
            flow_rate_ml_min: [
                { required: true, message: "请输入推荐流速", trigger: "blur" },
            ],
            column_volume_cv_ml: [
                { required: true, message: "请输入柱体积", trigger: "blur" },
            ],
        };

        // 过滤数据
        const filteredColumns = computed(() => {
            if (!searchText.value) {
                return columns.value;
            }
            return columns.value.filter(
                (column) =>
                    (column.column_code || "")
                        .toLowerCase()
                        .includes(searchText.value.toLowerCase()) ||
                    (column.specification_g || "")
                        .toString()
                        .includes(searchText.value) ||
                    (column.sample_load_amount || "")
                        .toLowerCase()
                        .includes(searchText.value.toLowerCase())
            );
        });

        // 方法
        const fetchColumns = async () => {
            loading.value = true;
            try {
                const response = await fetch("http://0.0.0.0:8008/api/columns/");
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.columns) {
                        columns.value = data.columns;
                        console.log(
                            "获取柱子参数成功:",
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
                console.error("获取柱子参数失败:", error);
                ElMessage.error("获取柱子参数失败: " + error.message);
                // 发生错误时使用模拟数据作为后备
                columns.value = [
                    {
                        column_id: 1,
                        column_code: "COL001",
                        specification_g: 50,
                        max_pressure_bar: 300,
                        flow_rate_ml_min: 1.0,
                        column_volume_cv_ml: 5.5,
                        sample_load_amount: "1-10mg",
                        created_at: "2024-01-15T10:30:00",
                    },
                    {
                        column_id: 2,
                        column_code: "COL002",
                        specification_g: 100,
                        max_pressure_bar: 250,
                        flow_rate_ml_min: 1.5,
                        column_volume_cv_ml: 10.2,
                        sample_load_amount: "5-50mg",
                        created_at: "2024-02-20T14:20:00",
                    },
                ];
            } finally {
                loading.value = false;
            }
        };

        const refreshData = () => {
            fetchColumns();
        };

        const resetForm = () => {
            Object.assign(columnForm, {
                column_id: null,
                column_code: "",
                specification_g: null,
                max_pressure_bar: null,
                flow_rate_ml_min: null,
                column_volume_cv_ml: null,
                sample_load_amount: "",
            });
        };

        const editColumn = (row) => {
            isEdit.value = true;
            Object.assign(columnForm, row);
            showAddDialog.value = true;
        };

        const confirmDelete = (row) => {
            ElMessageBox.confirm(
                `确定要删除柱子 "${row.column_code}" 吗？此操作不可撤销。`,
                "删除确认",
                {
                    confirmButtonText: "确定删除",
                    cancelButtonText: "取消",
                    type: "warning",
                }
            )
                .then(() => {
                    deleteColumn(row.column_id);
                })
                .catch(() => {
                    // 用户取消
                });
        };

        const deleteColumn = async (columnId) => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/columns/${columnId}`,
                    {
                        method: "DELETE",
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success(data.message || "删除成功");
                        fetchColumns();
                    } else {
                        throw new Error(data.message || "删除失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("删除柱子参数失败:", error);
                ElMessage.error("删除失败: " + error.message);
            }
        };

        const submitForm = () => {
            columnFormRef.value.validate((valid) => {
                if (valid) {
                    if (isEdit.value) {
                        updateColumn();
                    } else {
                        createColumn();
                    }
                }
            });
        };

        const createColumn = async () => {
            try {
                const requestData = {
                    column_code: columnForm.column_code,
                    specification_g: columnForm.specification_g,
                    max_pressure_bar: columnForm.max_pressure_bar,
                    flow_rate_ml_min: columnForm.flow_rate_ml_min,
                    column_volume_cv_ml: columnForm.column_volume_cv_ml,
                    sample_load_amount: columnForm.sample_load_amount,
                };

                const response = await fetch(
                    "http://0.0.0.0:8008/api/columns/",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(requestData),
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    ElMessage.success("创建成功");
                    handleClose();
                    fetchColumns();
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.message || "创建失败");
                }
            } catch (error) {
                console.error("创建柱子参数失败:", error);
                ElMessage.error("创建失败: " + error.message);
            }
        };

        const updateColumn = async () => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/columns/${columnForm.column_id}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(columnForm),
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success(data.message || "更新成功");
                        handleClose();
                        fetchColumns();
                    } else {
                        throw new Error(data.message || "更新失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("更新柱子参数失败:", error);
                ElMessage.error("更新失败: " + error.message);
            }
        };

        const handleClose = () => {
            showAddDialog.value = false;
            isEdit.value = false;
            resetForm();
            if (columnFormRef.value) {
                columnFormRef.value.resetFields();
            }
        };

        const formatDate = (dateString) => {
            if (!dateString) return "-";
            return new Date(dateString).toLocaleString("zh-CN");
        };

        // 生命周期
        onMounted(() => {
            fetchColumns();
        });

        return {
            columns,
            loading,
            searchText,
            showAddDialog,
            isEdit,
            columnForm,
            columnFormRef,
            formRules,
            filteredColumns,
            fetchColumns,
            refreshData,
            editColumn,
            confirmDelete,
            submitForm,
            handleClose,
            formatDate,
        };
    },
};
</script>

<style scoped>
.column-config {
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
}

.column-table {
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

.dialog-footer {
    text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .column-config {
        padding: 16px;
    }

    .toolbar {
        flex-direction: column;
        gap: 16px;
        align-items: stretch;
    }

    .toolbar-right {
        justify-content: flex-start;
    }

    .search-bar {
        text-align: center;
    }

    .search-bar .el-input {
        width: 100% !important;
        max-width: 300px;
    }
}
</style>
