<template>
    <div class="smiles-config">
        <!-- 操作工具栏 -->
        <div class="toolbar">
            <div class="toolbar-left">
                <h3>SMILES化合物管理</h3>
                <p class="toolbar-description">
                    管理化合物的SMILES结构信息和相关数据
                </p>
            </div>
            <div class="toolbar-right">
                <el-button
                    type="primary"
                    @click="showAddDialog = true"
                    icon="Plus"
                >
                    新增化合物
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
                placeholder="搜索化合物名称、SMILES字符串、分子式..."
                clearable
                style="width: 400px"
            >
                <template #prefix>
                    <el-icon><Search /></el-icon>
                </template>
            </el-input>
        </div>

        <!-- 数据表格 -->
        <el-table
            :data="filteredSmiles"
            v-loading="loading"
            stripe
            class="smiles-table"
            empty-text="暂无SMILES数据"
        >
            <el-table-column
                prop="smiles_description"
                label="化合物名称"
                width="150"
                fixed="left"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <div class="compound-name">
                        <el-tag type="success" size="small">
                            {{ scope.row.smiles_description || "未命名" }}
                        </el-tag>
                    </div>
                </template>
            </el-table-column>

            <el-table-column
                prop="smiles_string"
                label="SMILES字符串"
                width="200"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <div class="smiles-string">
                        <el-text class="monospace-text">
                            {{ scope.row.smiles_string || "-" }}
                        </el-text>
                        <el-button
                            v-if="scope.row.smiles_string"
                            size="small"
                            text
                            @click="copyToClipboard(scope.row.smiles_string)"
                            icon="CopyDocument"
                            class="copy-btn"
                        />
                    </div>
                </template>
            </el-table-column>

            <el-table-column
                prop="molecular_formula"
                label="分子式"
                width="120"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <el-text class="molecular-formula">
                        {{ scope.row.molecular_formula || "-" }}
                    </el-text>
                </template>
            </el-table-column>

            <el-table-column
                prop="molecular_weight"
                label="分子量"
                width="100"
                sortable
            >
                <template #default="scope">
                    <el-text type="primary" style="font-weight: 600">
                        {{
                            scope.row.molecular_weight
                                ? scope.row.molecular_weight.toFixed(2)
                                : "-"
                        }}
                    </el-text>
                </template>
            </el-table-column>

            <el-table-column
                prop="cas_number"
                label="CAS号"
                width="120"
                show-overflow-tooltip
            >
                <template #default="scope">
                    <span>{{ scope.row.cas_number || "-" }}</span>
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
                prop="updated_at"
                label="更新时间"
                width="160"
                sortable
            >
                <template #default="scope">
                    <span>{{ formatDate(scope.row.updated_at) }}</span>
                </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                    <el-button
                        size="small"
                        @click="editSmiles(scope.row)"
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

        <!-- 新增/编辑SMILES对话框 -->
        <el-dialog
            v-model="showAddDialog"
            :title="isEdit ? '编辑化合物信息' : '新增化合物信息'"
            width="700px"
            :before-close="handleClose"
        >
            <el-form
                :model="smilesForm"
                :rules="formRules"
                ref="smilesFormRef"
                label-width="120px"
            >
                <el-form-item label="化合物名称" prop="smiles_description">
                    <el-input
                        v-model="smilesForm.smiles_description"
                        placeholder="如：咖啡因、苯甲酸等"
                    />
                </el-form-item>

                <el-form-item label="SMILES字符串" prop="smiles_string">
                    <el-input
                        v-model="smilesForm.smiles_string"
                        placeholder="如：CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
                        class="monospace-input"
                    >
                        <template #append>
                            <el-button @click="validateSmiles" icon="View">
                                验证
                            </el-button>
                        </template>
                    </el-input>
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="分子式" prop="molecular_formula">
                            <el-input
                                v-model="smilesForm.molecular_formula"
                                placeholder="如：C8H10N4O2"
                            />
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="分子量" prop="molecular_weight">
                            <el-input-number
                                v-model="smilesForm.molecular_weight"
                                :min="1"
                                :max="10000"
                                :step="0.01"
                                :precision="2"
                                placeholder="分子量"
                                style="width: 100%"
                            />
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-form-item label="CAS号" prop="cas_number">
                    <el-input
                        v-model="smilesForm.cas_number"
                        placeholder="如：58-08-2"
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
    name: "SmilesConfig",
    setup() {
        // 响应式数据
        const smilesList = ref([]);
        const loading = ref(false);
        const searchText = ref("");
        const showAddDialog = ref(false);
        const isEdit = ref(false);
        const smilesFormRef = ref(null);

        // 表单数据
        const smilesForm = reactive({
            smiles_id: null,
            smiles_description: "",
            smiles_string: "",
            molecular_formula: "",
            molecular_weight: null,
            cas_number: "",
        });

        // 表单验证规则
        const formRules = {
            smiles_description: [
                {
                    required: true,
                    message: "请输入化合物名称",
                    trigger: "blur",
                },
                {
                    min: 1,
                    max: 200,
                    message: "长度在 1 到 200 个字符",
                    trigger: "blur",
                },
            ],
            smiles_string: [
                {
                    required: true,
                    message: "请输入SMILES字符串",
                    trigger: "blur",
                },
            ],
        };

        // 过滤数据
        const filteredSmiles = computed(() => {
            if (!searchText.value) {
                return smilesList.value;
            }
            const search = searchText.value.toLowerCase();
            return smilesList.value.filter(
                (item) =>
                    (item.smiles_description || "")
                        .toLowerCase()
                        .includes(search) ||
                    (item.smiles_string || "").toLowerCase().includes(search) ||
                    (item.molecular_formula || "")
                        .toLowerCase()
                        .includes(search) ||
                    (item.cas_number || "").toLowerCase().includes(search)
            );
        });

        // 方法
        const fetchSmiles = async () => {
            loading.value = true;
            try {
                const response = await fetch("http://0.0.0.0:8008/api/smiles");
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.smiles_list) {
                        smilesList.value = data.smiles_list;
                        console.log(
                            "获取SMILES数据成功:",
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
                console.error("获取SMILES数据失败:", error);
                ElMessage.error("获取SMILES数据失败: " + error.message);
                // 发生错误时使用模拟数据作为后备
                smilesList.value = [
                    {
                        smiles_id: 1,
                        smiles_description: "咖啡因",
                        smiles_string: "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                        molecular_formula: "C8H10N4O2",
                        molecular_weight: 194.19,
                        created_at: "2024-01-15T10:30:00",
                    },
                    {
                        smiles_id: 2,
                        smiles_description: "苯甲酸",
                        smiles_string: "C1=CC=C(C=C1)C(=O)O",
                        molecular_formula: "C7H6O2",
                        molecular_weight: 122.12,
                        created_at: "2024-01-16T11:20:00",
                    },
                    {
                        smiles_id: 3,
                        smiles_description: "水杨酸",
                        smiles_string: "C1=CC=C(C(=C1)C(=O)O)O",
                        molecular_formula: "C7H6O3",
                        molecular_weight: 138.12,
                        created_at: "2024-01-17T09:15:00",
                    },
                ];
            } finally {
                loading.value = false;
            }
        };

        const refreshData = () => {
            fetchSmiles();
        };

        const resetForm = () => {
            Object.assign(smilesForm, {
                smiles_id: null,
                smiles_description: "",
                smiles_string: "",
                molecular_formula: "",
                molecular_weight: null,
                cas_number: "",
            });
        };

        const editSmiles = (row) => {
            isEdit.value = true;
            Object.assign(smilesForm, row);
            showAddDialog.value = true;
        };

        const confirmDelete = (row) => {
            ElMessageBox.confirm(
                `确定要删除化合物 "${row.smiles_description}" 吗？此操作不可撤销。`,
                "删除确认",
                {
                    confirmButtonText: "确定删除",
                    cancelButtonText: "取消",
                    type: "warning",
                }
            )
                .then(() => {
                    deleteSmiles(row.smiles_id);
                })
                .catch(() => {
                    // 用户取消
                });
        };

        const deleteSmiles = async (smilesId) => {
            try {
                // TODO: 替换为实际API调用
                const response = await fetch(
                    `http://0.0.0.0:8008/api/smiles/${smilesId}`,
                    {
                        method: "DELETE",
                    }
                );

                if (response.ok) {
                    ElMessage.success("删除成功");
                    fetchSmiles();
                } else {
                    throw new Error("删除失败");
                }
            } catch (error) {
                console.error("删除SMILES数据失败:", error);
                ElMessage.error("删除失败");
            }
        };

        const validateSmiles = () => {
            if (!smilesForm.smiles_string) {
                ElMessage.warning("请先输入SMILES字符串");
                return;
            }
            // 简单的SMILES格式验证
            const smilesPattern = /^[A-Za-z0-9\(\)\[\]\-\+\#\=\@\/\\:]+$/;
            if (smilesPattern.test(smilesForm.smiles_string)) {
                ElMessage.success("SMILES字符串格式正确");
            } else {
                ElMessage.error("SMILES字符串格式可能有误");
            }
        };

        const copyToClipboard = async (text) => {
            try {
                await navigator.clipboard.writeText(text);
                ElMessage.success("已复制到剪贴板");
            } catch (error) {
                console.error("复制失败:", error);
                ElMessage.error("复制失败");
            }
        };

        const submitForm = () => {
            smilesFormRef.value.validate((valid) => {
                if (valid) {
                    if (isEdit.value) {
                        updateSmiles();
                    } else {
                        createSmiles();
                    }
                }
            });
        };

        const createSmiles = async () => {
            try {
                // TODO: 替换为实际API调用
                const response = await fetch("http://0.0.0.0:8008/api/smiles", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(smilesForm),
                });

                if (response.ok) {
                    ElMessage.success("创建成功");
                    handleClose();
                    fetchSmiles();
                } else {
                    throw new Error("创建失败");
                }
            } catch (error) {
                console.error("创建SMILES数据失败:", error);
                ElMessage.error("创建失败");
            }
        };

        const updateSmiles = async () => {
            try {
                // TODO: 替换为实际API调用
                const response = await fetch(
                    `http://0.0.0.0:8008/api/smiles/${smilesForm.smiles_id}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(smilesForm),
                    }
                );

                if (response.ok) {
                    ElMessage.success("更新成功");
                    handleClose();
                    fetchSmiles();
                } else {
                    throw new Error("更新失败");
                }
            } catch (error) {
                console.error("更新SMILES数据失败:", error);
                ElMessage.error("更新失败");
            }
        };

        const handleClose = () => {
            showAddDialog.value = false;
            isEdit.value = false;
            resetForm();
            if (smilesFormRef.value) {
                smilesFormRef.value.resetFields();
            }
        };

        const formatDate = (dateString) => {
            if (!dateString) return "-";
            return new Date(dateString).toLocaleString("zh-CN");
        };

        // 生命周期
        onMounted(() => {
            fetchSmiles();
        });

        return {
            smilesList,
            loading,
            searchText,
            showAddDialog,
            isEdit,
            smilesForm,
            smilesFormRef,
            formRules,
            filteredSmiles,
            fetchSmiles,
            refreshData,
            editSmiles,
            confirmDelete,
            validateSmiles,
            copyToClipboard,
            submitForm,
            handleClose,
            formatDate,
        };
    },
};
</script>

<style scoped>
.smiles-config {
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

.smiles-table {
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

.compound-name {
    line-height: 1.4;
}

.smiles-description {
    margin-top: 4px;
}

.smiles-string {
    display: flex;
    align-items: center;
    gap: 8px;
}

.monospace-text {
    font-family: "Courier New", Consolas, Monaco, monospace;
    font-size: 13px;
    background: #f5f7fa;
    padding: 2px 6px;
    border-radius: 4px;
    word-break: break-all;
}

.copy-btn {
    min-width: auto;
    padding: 4px;
}

.molecular-formula {
    font-family: "Times New Roman", serif;
    font-size: 14px;
    font-weight: 500;
}

.monospace-input :deep(.el-input__inner) {
    font-family: "Courier New", Consolas, Monaco, monospace;
}

.dialog-footer {
    text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .smiles-config {
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
        max-width: 400px;
    }
}
</style>
