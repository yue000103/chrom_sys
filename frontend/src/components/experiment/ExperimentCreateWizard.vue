<template>
    <div class="experiment-create-wizard">
        <el-steps :active="currentStep" align-center>
            <el-step title="基本信息" />
            <el-step title="方法选择" />
            <el-step title="预处理配置" />
            <el-step title="确认创建" />
        </el-steps>

        <div class="wizard-content">
            <!-- 步骤1: 基本信息 -->
            <div v-if="currentStep === 0" class="step-content">
                <h3>实验基本信息</h3>
                <el-form :model="experimentData" label-width="120px">
                    <el-form-item label="实验名称" required>
                        <el-input
                            v-model="experimentData.name"
                            placeholder="请输入实验名称"
                        />
                    </el-form-item>

                    <el-form-item label="实验描述">
                        <el-input
                            v-model="experimentData.description"
                            type="textarea"
                            :rows="2"
                            placeholder="请输入实验描述（简要描述）"
                        />
                    </el-form-item>

                    <el-form-item label="操作员">
                        <el-input
                            v-model="experimentData.operator"
                            placeholder="操作员姓名"
                        />
                    </el-form-item>

                    <el-form-item label="是否峰驱动">
                        <el-switch v-model="experimentData.isPeakDriven" />
                        <div style="margin-top: 8px">
                            <el-text type="info" size="small">
                                <el-icon><InfoFilled /></el-icon>
                                峰驱动模式将根据检测到的峰自动收集，否则按体积收集
                            </el-text>
                        </div>
                    </el-form-item>

                    <el-form-item label="收集体积 (mL)" required>
                        <el-input-number
                            v-model="experimentData.collectionVolume"
                            :min="0.1"
                            :max="50"
                            :step="1"
                            placeholder="请输入收集体积"
                        />
                    </el-form-item>

                    <el-form-item label="清洗体积 (mL)" required>
                        <el-input-number
                            v-model="experimentData.washVolume"
                            :min="0.1"
                            :max="20"
                            :step="1"
                            placeholder="请输入清洗体积"
                        />
                    </el-form-item>

                    <el-form-item label="清洗次数" required>
                        <el-input-number
                            v-model="experimentData.washCycles"
                            :min="1"
                            :max="10"
                            placeholder="请输入清洗次数"
                        />
                    </el-form-item>

                    <el-form-item label="预计开始时间">
                        <el-date-picker
                            v-model="experimentData.scheduledTime"
                            type="datetime"
                            placeholder="选择开始时间"
                            format="YYYY/MM/DD HH:mm"
                            value-format="YYYY-MM-DD HH:mm:ss"
                        />
                    </el-form-item>
                </el-form>
            </div>

            <!-- 步骤2: 方法选择 -->
            <div v-if="currentStep === 1" class="step-content">
                <h3>选择分析方法</h3>
                <div class="method-selection">
                    <div v-if="isEditMode" class="edit-mode-notice">
                        <el-alert
                            title="编辑模式说明"
                            type="info"
                            description="编辑模式下不允许修改分析方法，如需更改方法请创建新实验。"
                            show-icon
                            :closable="false"
                        />
                        <div class="current-method-display">
                            <h4>当前方法</h4>
                            <p>{{ experimentData.methodId || "未指定方法" }}</p>
                        </div>
                    </div>
                    <el-table
                        v-else
                        :data="paginatedMethods"
                        @row-click="selectMethod"
                        highlight-current-row
                        :row-class-name="getRowClassName"
                        stripe
                        style="width: 100%"
                    >

                        <el-table-column
                            prop="name"
                            label="方法名称"
                            width="200"
                            show-overflow-tooltip
                        >
                            <template #default="scope">
                                <div class="method-name">
                                    <span>{{ scope.row.name }}</span>
                                    <el-tag
                                        v-if="scope.row.isFavorite"
                                        type="warning"
                                        size="small"
                                        style="margin-left: 8px"
                                    >
                                        常用
                                    </el-tag>
                                </div>
                            </template>
                        </el-table-column>

                        <el-table-column
                            prop="channelA"
                            label="A通道波长"
                            width="120"
                            align="center"
                        >
                            <template #default="scope">
                                <el-tag type="primary" size="small">
                                    {{ scope.row.channelA || 254 }}nm
                                </el-tag>
                            </template>
                        </el-table-column>

                        <el-table-column
                            prop="channelB"
                            label="B通道波长"
                            width="120"
                            align="center"
                        >
                            <template #default="scope">
                                <el-tag type="success" size="small">
                                    {{ scope.row.channelB || 280 }}nm
                                </el-tag>
                            </template>
                        </el-table-column>

                        <el-table-column
                            prop="smiles"
                            label="SMILES"
                            width="150"
                            show-overflow-tooltip
                        >
                            <template #default="scope">
                                <el-text
                                    class="smiles-text"
                                    v-if="scope.row.smiles"
                                >
                                    {{ scope.row.smiles }}
                                </el-text>
                                <span v-else class="no-data">-</span>
                            </template>
                        </el-table-column>

                        <el-table-column
                            prop="collectionVolume"
                            label="收集体积"
                            width="120"
                            align="center"
                        >
                            <template #default="scope">
                                <span
                                    >{{
                                        scope.row.collectionVolume || 5.0
                                    }}
                                    mL</span
                                >
                            </template>
                        </el-table-column>

                        <el-table-column label="其他参数" min-width="200">
                            <template #default="scope">
                                <div class="method-params">
                                    <span class="param-item"
                                        >流速:
                                        {{ scope.row.flowRate }}mL/min</span
                                    >
                                    <span class="param-item"
                                        >时间: {{ scope.row.runTime }}min</span
                                    >
                                    <span class="param-item"
                                        >梯度:
                                        {{
                                            scope.row.gradientMode || "自动"
                                        }}</span
                                    >
                                </div>
                            </template>
                        </el-table-column>
                    </el-table>

                    <!-- 分页控件 -->
                    <div class="pagination-wrapper">
                        <el-pagination
                            v-model:current-page="currentPage"
                            :page-size="pageSize"
                            :total="availableMethods.length"
                            layout="prev, pager, next"
                            @current-change="handlePageChange"
                            background
                            small
                        />
                    </div>

                    <div v-if="selectedMethodInfo" class="selected-method-info">
                        <el-alert
                            :title="`已选择方法: ${selectedMethodInfo.name}`"
                            type="success"
                            :description="`A通道: ${
                                selectedMethodInfo.channelA || 254
                            }nm, B通道: ${
                                selectedMethodInfo.channelB || 280
                            }nm, SMILES: ${
                                selectedMethodInfo.smiles || '未设置'
                            }`"
                            :closable="false"
                            show-icon
                        />
                    </div>
                </div>
            </div>

            <!-- 步骤3: 预处理配置 -->
            <div v-if="currentStep === 2" class="step-content">
                <h3>预处理配置</h3>
                <el-form :model="experimentData" label-width="120px">
                    <el-form-item label="吹扫系统">
                        <el-switch
                            v-model="experimentData.pretreatment.purgeSystem"
                        />
                    </el-form-item>
                    <el-form-item label="吹扫柱子">
                        <el-switch
                            v-model="experimentData.pretreatment.purgeColumn"
                        />
                    </el-form-item>
                    <el-form-item
                        v-if="experimentData.pretreatment.purgeColumn"
                        label="吹扫时长 (min)"
                    >
                        <el-input-number
                            v-model="experimentData.pretreatment.purgeTime"
                            :min="1"
                            :max="60"
                        />
                    </el-form-item>
                    <el-form-item label="柱平衡">
                        <el-switch
                            v-model="experimentData.pretreatment.columnBalance"
                        />
                    </el-form-item>
                    <el-form-item
                        v-if="experimentData.pretreatment.columnBalance"
                        label="平衡时长 (min)"
                    >
                        <el-input-number
                            v-model="experimentData.pretreatment.balanceTime"
                            :min="1"
                            :max="60"
                        />
                    </el-form-item>
                    <el-form-item
                        v-if="experimentData.pretreatment.columnBalance"
                        label="润柱溶液"
                    >
                        <el-select
                            v-model="
                                experimentData.pretreatment.conditioningSolution
                            "
                            placeholder="选择润柱溶液"
                            style="width: 100%"
                        >
                            <el-option label="溶液A" :value="1" />
                            <el-option label="溶液B" :value="2" />
                            <el-option label="溶液C" :value="3" />
                            <el-option label="溶液D" :value="4" />
                        </el-select>
                    </el-form-item>
                </el-form>
            </div>

            <!-- 步骤4: 确认创建 -->
            <div v-if="currentStep === 3" class="step-content">
                <h3>{{ isEditMode ? "确认修改信息" : "确认实验信息" }}</h3>
                <div class="experiment-summary">
                    <el-card>
                        <h4>{{ experimentData.name }}</h4>
                        <p>{{ experimentData.description }}</p>
                        <el-divider />

                        <div class="summary-section">
                            <h5>基本信息</h5>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <label>操作员:</label>
                                    <span>{{ experimentData.operator }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>使用方法:</label>
                                    <span>{{ getSelectedMethodName() }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>峰驱动模式:</label>
                                    <span
                                        class="peak-driven-status"
                                        :class="
                                            experimentData.isPeakDriven
                                                ? 'enabled'
                                                : 'disabled'
                                        "
                                    >
                                        {{
                                            experimentData.isPeakDriven
                                                ? "已启用"
                                                : "已关闭"
                                        }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div class="summary-section">
                            <h5>预处理配置</h5>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <label>吹扫系统:</label>
                                    <span>{{
                                        experimentData.pretreatment.purgeSystem
                                            ? "开启"
                                            : "关闭"
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>吹扫柱子:</label>
                                    <span>{{
                                        experimentData.pretreatment.purgeColumn
                                            ? "开启"
                                            : "关闭"
                                    }}</span>
                                </div>
                                <div
                                    class="summary-item"
                                    v-if="
                                        experimentData.pretreatment.purgeColumn
                                    "
                                >
                                    <label>吹扫时长:</label>
                                    <span
                                        >{{
                                            experimentData.pretreatment
                                                .purgeTime
                                        }}
                                        分钟</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>柱平衡:</label>
                                    <span>{{
                                        experimentData.pretreatment
                                            .columnBalance
                                            ? "开启"
                                            : "关闭"
                                    }}</span>
                                </div>
                                <div
                                    class="summary-item"
                                    v-if="
                                        experimentData.pretreatment
                                            .columnBalance
                                    "
                                >
                                    <label>平衡时长:</label>
                                    <span
                                        >{{
                                            experimentData.pretreatment
                                                .balanceTime
                                        }}
                                        分钟</span
                                    >
                                </div>
                            </div>
                        </div>

                        <div class="summary-section">
                            <h5>参数设置</h5>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <label>收集体积:</label>
                                    <span
                                        >{{
                                            experimentData.collectionVolume
                                        }}
                                        mL</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>清洗体积:</label>
                                    <span
                                        >{{
                                            experimentData.washVolume
                                        }}
                                        mL</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>清洗次数:</label>
                                    <span
                                        >{{
                                            experimentData.washCycles
                                        }}
                                        次</span
                                    >
                                </div>
                                <div
                                    class="summary-item"
                                    v-if="experimentData.scheduledTime"
                                >
                                    <label>预计开始:</label>
                                    <span>{{
                                        experimentData.scheduledTime
                                    }}</span>
                                </div>
                            </div>
                        </div>

                        <div class="summary-section">
                            <h5>预计消耗</h5>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <label>预计运行时间:</label>
                                    <span>{{ estimatedRunTime }} 分钟</span>
                                </div>
                                <div class="summary-item">
                                    <label>预计试管使用:</label>
                                    <span>{{ estimatedTubes }} 支</span>
                                </div>
                                <div class="summary-item">
                                    <label>预计溶剂消耗:</label>
                                    <span>{{ estimatedSolvent }} mL</span>
                                </div>
                            </div>
                        </div>
                    </el-card>
                </div>
            </div>
        </div>

        <div class="wizard-footer">
            <el-button @click="previousStep" :disabled="currentStep === 0"
                >上一步</el-button
            >
            <el-button v-if="currentStep < 3" type="primary" @click="nextStep"
                >下一步</el-button
            >
            <el-button
                v-if="currentStep === 3"
                type="success"
                @click="saveExperiment"
            >
                {{ isEditMode ? "保存修改" : "创建实验" }}
            </el-button>
            <el-button @click="$emit('cancel')">取消</el-button>
        </div>
    </div>
</template>

<script>
import { ref, computed } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";

export default {
    name: "ExperimentCreateWizard",
    components: {
        InfoFilled,
    },
    props: {
        isEditMode: {
            type: Boolean,
            default: false,
        },
        experimentData: {
            type: Object,
            default: null,
        },
    },
    emits: ["save", "cancel"],
    setup(props, { emit }) {
        const currentStep = ref(0);

        // 初始化实验数据
        const initializeExperimentData = () => {
            if (props.isEditMode && props.experimentData) {
                // 编辑模式：使用传入的实验数据
                return {
                    name: props.experimentData.experiment_name || "",
                    description: props.experimentData.description || "",
                    experimentDescription:
                        props.experimentData.experiment_description || "",
                    operator: props.experimentData.operator || "当前用户",
                    methodId: props.experimentData.method_id || null,
                    type: props.experimentData.experiment_type || "standard",
                    pretreatment: {
                        purgeSystem: Boolean(props.experimentData.purge_system),
                        purgeColumn: Boolean(props.experimentData.purge_column),
                        purgeTime:
                            props.experimentData.purge_column_time_min || 5,
                        columnBalance: Boolean(
                            props.experimentData.column_balance
                        ),
                        balanceTime:
                            props.experimentData.column_balance_time_min || 10,
                        conditioningSolution:
                            props.experimentData.column_conditioning_solution ||
                            1,
                    },
                    isPeakDriven: Boolean(props.experimentData.is_peak_driven),
                    collectionVolume:
                        props.experimentData.collection_volume_ml || 5.0,
                    washVolume: props.experimentData.wash_volume_ml || 2.0,
                    washCycles: props.experimentData.wash_cycles || 1,
                    scheduledTime:
                        props.experimentData.scheduled_start_time || null,
                };
            } else {
                // 创建模式：使用默认数据
                return {
                    name: `实验-${new Date()
                        .toISOString()
                        .slice(0, 19)
                        .replace(/[-:]/g, "")
                        .replace("T", "-")}`,
                    description: "",
                    experimentDescription: "",
                    operator: "当前用户",
                    methodId: null,
                    type: "standard",
                    pretreatment: {
                        purgeSystem: false,
                        purgeColumn: true,
                        purgeTime: 5,
                        columnBalance: true,
                        balanceTime: 10,
                        conditioningSolution: 1,
                    },
                    isPeakDriven: true,
                    collectionVolume: 5.0,
                    washVolume: 2.0,
                    washCycles: 1,
                    scheduledTime: null,
                };
            }
        };

        const experimentData = ref(initializeExperimentData());

        // 可用方法列表
        const availableMethods = ref([
            {
                id: 1,
                name: "标准分析方法-01",
                description: "用于蛋白质分离的标准方法",
                isFavorite: true,
                flowRate: 1.0,
                runTime: 30,
                channelA: 254,
                channelB: 280,
                smiles: "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                collectionVolume: 5.0,
                gradientMode: "自动",
            },
            {
                id: 2,
                name: "快速检测方法",
                description: "用于快速样品筛选",
                isFavorite: false,
                flowRate: 1.5,
                runTime: 15,
                channelA: 280,
                channelB: 254,
                smiles: "C1=CC=C(C=C1)C(=O)O",
                collectionVolume: 3.0,
                gradientMode: "手动",
            },
            {
                id: 3,
                name: "高分辨分离方法",
                description: "用于复杂样品的高分辨分离",
                isFavorite: true,
                flowRate: 0.8,
                runTime: 60,
                channelA: 254,
                channelB: 280,
                smiles: "C1=CC=C(C(=C1)C(=O)O)O",
                collectionVolume: 8.0,
                gradientMode: "自动",
            },
            {
                id: 4,
                name: "维生素C分析方法",
                description: "专用于维生素C检测",
                isFavorite: false,
                flowRate: 1.2,
                runTime: 25,
                channelA: 245,
                channelB: 280,
                smiles: "C(C(C(C(=C(C(=O)O)O)O)O)O)O",
                collectionVolume: 4.0,
                gradientMode: "自动",
            },
            {
                id: 5,
                name: "苯酚类分析方法",
                description: "适用于苯酚类化合物分离",
                isFavorite: true,
                flowRate: 1.1,
                runTime: 40,
                channelA: 270,
                channelB: 254,
                smiles: "C1=CC=C(C=C1)O",
                collectionVolume: 6.0,
                gradientMode: "自动",
            },
        ]);

        const selectedMethodInfo = ref(null);

        // 分页相关
        const currentPage = ref(1);
        const pageSize = ref(4);

        // 分页数据
        const paginatedMethods = computed(() => {
            const start = (currentPage.value - 1) * pageSize.value;
            const end = start + pageSize.value;
            return availableMethods.value.slice(start, end);
        });

        const selectedMethod = computed(() => {
            return availableMethods.value.find(
                (method) => method.id === experimentData.value.methodId
            );
        });

        const estimatedRunTime = computed(() => {
            if (selectedMethod.value) {
                const baseTime = selectedMethod.value.runTime;
                const washTime = experimentData.value.washCycles * 2; // 假设每次清洗2分钟
                return baseTime + washTime;
            }
            return 0;
        });

        const estimatedTubes = computed(() => {
            if (selectedMethod.value) {
                if (experimentData.value.collectionStrategy === "volume") {
                    const totalVolume =
                        selectedMethod.value.flowRate *
                        selectedMethod.value.runTime;
                    return Math.ceil(
                        totalVolume / experimentData.value.collectionVolume
                    );
                }
                return Math.ceil(selectedMethod.value.runTime / 5); // 假设平均每5分钟一个峰
            }
            return 0;
        });

        const estimatedSolvent = computed(() => {
            if (selectedMethod.value) {
                const runVolume =
                    selectedMethod.value.flowRate *
                    selectedMethod.value.runTime;
                const washVolume =
                    experimentData.value.washVolume *
                    experimentData.value.washCycles;
                return Math.round((runVolume + washVolume) * 10) / 10;
            }
            return 0;
        });

        const nextStep = () => {
            if (currentStep.value < 3) {
                currentStep.value++;
            }
        };

        const previousStep = () => {
            if (currentStep.value > 0) {
                currentStep.value--;
            }
        };

        const getSelectedMethodName = () => {
            return selectedMethod.value ? selectedMethod.value.name : "未选择";
        };


        const selectMethod = (row) => {
            experimentData.value.methodId = row.id;
            selectedMethodInfo.value = row;
        };

        const getRowClassName = ({ row }) => {
            return row.id === experimentData.value.methodId
                ? "selected-row"
                : "";
        };

        const handlePageChange = (page) => {
            currentPage.value = page;
        };

        const saveExperiment = () => {
            const experimentToSave = {
                ...experimentData.value,
                method: selectedMethod.value?.name || "",
                estimatedTime: `${estimatedRunTime.value}分钟`,
                // 添加预处理配置的扁平化字段
                purgeSystem: experimentData.value.pretreatment.purgeSystem,
                purgeColumn: experimentData.value.pretreatment.purgeColumn,
                purgeColumnTime: experimentData.value.pretreatment.purgeTime,
                columnBalance: experimentData.value.pretreatment.columnBalance,
                columnBalanceTime:
                    experimentData.value.pretreatment.balanceTime,
                columnConditioningSolution:
                    experimentData.value.pretreatment.conditioningSolution,
                // 添加时间字段的映射
                scheduledStartTime: experimentData.value.scheduledTime,
            };
            emit("save", experimentToSave);
        };

        return {
            currentStep,
            experimentData,
            availableMethods,
            selectedMethodInfo,
            selectedMethod,
            currentPage,
            pageSize,
            paginatedMethods,
            estimatedRunTime,
            estimatedTubes,
            estimatedSolvent,
            nextStep,
            previousStep,
            selectMethod,
            getRowClassName,
            handlePageChange,
            getSelectedMethodName,
            saveExperiment,
            isEditMode: props.isEditMode,
        };
    },
};
</script>

<style scoped>
.experiment-create-wizard {
    padding: 20px;
}

.wizard-content {
    margin: 30px 0;
    min-height: 500px;
}

.step-content {
    padding: 20px;
}

.step-content h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.method-selection {
    margin-bottom: 20px;
}

.method-name {
    display: flex;
    align-items: center;
}

.smiles-text {
    font-family: "Courier New", Consolas, Monaco, monospace;
    font-size: 12px;
    background: #f5f7fa;
    padding: 2px 4px;
    border-radius: 3px;
}

.no-data {
    color: #c0c4cc;
    font-style: italic;
}

.method-params {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.param-item {
    font-size: 12px;
    color: #666;
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    display: inline-block;
    margin-right: 4px;
    margin-bottom: 2px;
}

.selected-method-info {
    margin-top: 16px;
}

.pagination-wrapper {
    display: flex;
    justify-content: center;
    margin: 20px 0;
}

:deep(.el-table .selected-row) {
    background-color: #e6f7ff !important;
}

:deep(.el-table .selected-row td) {
    background-color: #e6f7ff !important;
}

:deep(.el-table__row) {
    cursor: pointer;
}

:deep(.el-table__row:hover) {
    background-color: #f5f7fa;
}

.experiment-summary {
    max-height: 500px;
    overflow-y: auto;
}

.summary-section {
    margin-bottom: 20px;
}

.summary-section h5 {
    margin: 0 0 12px 0;
    color: #666;
    font-size: 14px;
    border-bottom: 1px solid #ebeef5;
    padding-bottom: 4px;
}

.summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.summary-item label {
    color: #666;
    font-weight: 500;
}

.wizard-footer {
    display: flex;
    justify-content: center;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
}

.peak-driven-status.enabled {
    color: #67c23a;
    font-weight: 600;
}

.peak-driven-status.disabled {
    color: #f56c6c;
    font-weight: 600;
}

.edit-mode-notice {
    margin-bottom: 20px;
}

.current-method-display {
    margin-top: 16px;
    padding: 16px;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    background-color: #f8f9fa;
}

.current-method-display h4 {
    margin: 0 0 8px 0;
    color: #303133;
    font-size: 16px;
}

.current-method-display p {
    margin: 0;
    color: #606266;
    font-size: 14px;
}
</style>
