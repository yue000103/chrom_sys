<template>
    <div class="method-create-wizard">
        <el-steps :active="currentStep" align-center>
            <el-step title="基本信息" />
            <el-step title="色谱参数" />
            <el-step title="梯度设置" />
            <el-step title="确认创建" />
        </el-steps>

        <div class="wizard-content">
            <!-- 步骤1: 基本信息 -->
            <div v-if="currentStep === 0" class="step-content">
                <h3>基本信息</h3>
                <el-form :model="methodData" label-width="120px">
                    <el-form-item label="方法名称" required>
                        <el-input
                            v-model="methodData.name"
                            placeholder="请输入方法名称"
                        />
                    </el-form-item>
                    <el-form-item label="Smlies" required>
                        <el-select
                            v-model="methodData.smlies"
                            placeholder="请选择或输入Smlies"
                            filterable
                            allow-create
                            default-first-option
                            :reserve-keyword="false"
                            style="width: 100%"
                            @change="handleSmliesChange"
                        >
                            <el-option
                                v-for="item in filteredSmliesList"
                                :key="item"
                                :label="item"
                                :value="item"
                            />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="方法类型">
                        <el-radio-group v-model="methodData.type">
                            <el-radio label="user">制备方法</el-radio>
                            <el-radio label="template">分析方法</el-radio>
                        </el-radio-group>
                    </el-form-item>
                </el-form>
            </div>

            <!-- 步骤2: 色谱参数 -->
            <div v-if="currentStep === 1" class="step-content">
                <h3>色谱参数</h3>
                <el-form :model="methodData" label-width="200px">
                    <el-form-item label="色谱柱" required>
                        <el-select
                            v-model="methodData.column_id"
                            placeholder="请选择色谱柱"
                            style="width: 100%"
                            :loading="columnsLoading"
                            filterable
                        >
                            <el-option
                                v-for="column in columns"
                                :key="column.column_id"
                                :label="`${column.column_code} (${column.specification_g}g, ${column.column_volume_cv_ml}mL)`"
                                :value="column.column_id"
                            >
                                <div class="column-option">
                                    <span class="column-code">{{ column.column_code }}</span>
                                    <span class="column-spec">{{ column.specification_g }}g | {{ column.column_volume_cv_ml }}mL</span>
                                </div>
                            </el-option>
                        </el-select>
                        <div class="form-help-text" v-if="selectedColumn">
                            <el-text type="info" size="small">
                                最大压力: {{ selectedColumn.max_pressure_bar }}bar |
                                推荐流速: {{ selectedColumn.flow_rate_ml_min }}mL/min |
                                样品载量: {{ selectedColumn.sample_load_amount }}
                            </el-text>
                        </div>
                    </el-form-item>
                    <el-form-item label="流速 (mL/min)" required>
                        <el-input-number
                            v-model="methodData.flowRate"
                            :min="0"
                            :max="200"
                            :step="1"
                        />
                    </el-form-item>
                    <el-form-item label="运行时间 (min)" required>
                        <el-input-number
                            v-model="methodData.runTime"
                            :min="1"
                            :max="999"
                        />
                    </el-form-item>
                    <el-form-item label="A通道波长 (nm)" required>
                        <el-input-number
                            v-model="methodData.wavelengthA"
                            :min="190"
                            :max="800"
                            placeholder="请输入A通道检测波长"
                        />
                    </el-form-item>
                    <el-form-item label="B通道波长 (nm)" required>
                        <el-input-number
                            v-model="methodData.wavelengthB"
                            :min="190"
                            :max="800"
                            placeholder="请输入B通道检测波长"
                        />
                    </el-form-item>
                </el-form>
            </div>

            <!-- 步骤3: 梯度设置 -->
            <div v-if="currentStep === 2" class="step-content">
                <h3>梯度设置</h3>
                <el-form :model="methodData" label-width="120px">
                    <el-form-item label="梯度模式" required>
                        <el-radio-group v-model="methodData.gradientMode">
                            <el-radio label="auto">自动梯度</el-radio>
                            <el-radio label="manual">手动梯度</el-radio>
                        </el-radio-group>
                    </el-form-item>

                    <!-- 自动梯度参数 -->
                    <div v-if="methodData.gradientMode === 'auto'">
                        <div class="param-section-header">
                            <h4>自动梯度参数</h4>
                            <el-button
                                size="small"
                                type="info"
                                @click="showParamHelp = true"
                                icon="QuestionFilled"
                            >
                                参数说明
                            </el-button>
                        </div>

                        <el-row :gutter="20">
                            <el-col :span="12">
                                <el-form-item label="起始比例 (%)">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.startRatio
                                        "
                                        :min="0"
                                        :max="100"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <el-form-item label="结束比例 (%)">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.endRatio
                                        "
                                        :min="0"
                                        :max="100"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="12">
                                <el-form-item label="N1柱体积数">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.n1Volumes
                                        "
                                        :min="0.1"
                                        :max="20"
                                        :step="0.1"
                                        :precision="1"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <el-form-item label="梯度速率">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.gradientRate
                                        "
                                        :min="0.1"
                                        :max="10"
                                        :step="0.1"
                                        :precision="1"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="12">
                                <el-form-item label="峰阈值">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient
                                                .peakThreshold
                                        "
                                        :min="0.001"
                                        :max="1"
                                        :step="0.001"
                                        :precision="3"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <el-form-item label="柱体积 (mL)">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.columnVolume
                                        "
                                        :min="1"
                                        :max="200"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="12">
                                <el-form-item label="SG滤波窗口">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.sgWindow
                                        "
                                        :min="3"
                                        :max="21"
                                        :step="2"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <el-form-item label="SG滤波阶数">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.sgOrder
                                        "
                                        :min="1"
                                        :max="5"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="12">
                                <el-form-item label="基线窗口">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient
                                                .baselineWindow
                                        "
                                        :min="5"
                                        :max="50"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <el-form-item label="K因子">
                                    <el-input-number
                                        v-model="
                                            methodData.autoGradient.kFactor
                                        "
                                        :min="0.1"
                                        :max="10"
                                        :step="0.1"
                                        :precision="1"
                                        style="width: 100%"
                                    />
                                </el-form-item>
                            </el-col>
                        </el-row>
                    </div>

                    <!-- 手动梯度参数 -->
                    <div v-if="methodData.gradientMode === 'manual'">
                        <div class="param-section-header">
                            <h4>手动梯度时间表</h4>
                            <div class="gradient-validation-info">
                                <el-text type="info" size="small">
                                    <el-icon><InfoFilled /></el-icon>
                                    注意：每行原液A+B+C+D的总和必须等于100%
                                </el-text>
                            </div>
                        </div>

                        <el-form-item>
                            <el-table
                                :data="methodData.manualGradient"
                                style="width: 100%"
                                :row-class-name="getRowClassName"
                            >
                                <el-table-column
                                    prop="time"
                                    label="时间(min)"
                                    width="110"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.time"
                                            :min="0"
                                            size="small"
                                            style="width: 100%"
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="solutionA"
                                    label="原液A(%)"
                                    width="100"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.solutionA"
                                            :min="0"
                                            :max="100"
                                            size="small"
                                            style="width: 100%"
                                            @change="
                                                validateGradientRow(
                                                    scope.$index
                                                )
                                            "
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="solutionB"
                                    label="原液B(%)"
                                    width="100"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.solutionB"
                                            :min="0"
                                            :max="100"
                                            size="small"
                                            style="width: 100%"
                                            @change="
                                                validateGradientRow(
                                                    scope.$index
                                                )
                                            "
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="solutionC"
                                    label="原液C(%)"
                                    width="100"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.solutionC"
                                            :min="0"
                                            :max="100"
                                            size="small"
                                            style="width: 100%"
                                            @change="
                                                validateGradientRow(
                                                    scope.$index
                                                )
                                            "
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="solutionD"
                                    label="原液D(%)"
                                    width="100"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.solutionD"
                                            :min="0"
                                            :max="100"
                                            size="small"
                                            style="width: 100%"
                                            @change="
                                                validateGradientRow(
                                                    scope.$index
                                                )
                                            "
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="flowRate"
                                    label="流速"
                                    width="100"
                                >
                                    <template #default="scope">
                                        <el-input-number
                                            v-model="scope.row.flowRate"
                                            :min="0.01"
                                            :max="10"
                                            size="small"
                                            style="width: 100%"
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column label="总和" width="70">
                                    <template #default="scope">
                                        <el-text
                                            :type="
                                                getGradientSumType(scope.row)
                                            "
                                            style="font-weight: 600"
                                        >
                                            {{ getGradientSum(scope.row) }}%
                                        </el-text>
                                    </template>
                                </el-table-column>
                                <el-table-column label="操作" width="80">
                                    <template #default="scope">
                                        <el-button
                                            size="small"
                                            type="danger"
                                            @click="
                                                removeGradientStep(scope.$index)
                                            "
                                            >删除</el-button
                                        >
                                    </template>
                                </el-table-column>
                            </el-table>
                            <el-button
                                @click="addGradientStep"
                                style="margin-top: 10px"
                                >添加步骤</el-button
                            >
                        </el-form-item>
                    </div>
                </el-form>
            </div>

            <!-- 步骤4: 确认创建 -->
            <div v-if="currentStep === 3" class="step-content">
                <h3>确认方法信息</h3>
                <div class="method-summary">
                    <el-card>
                        <h4>{{ methodData.name }}</h4>
                        <p v-if="methodData.smlies">
                            Smlies: {{ methodData.smlies }}
                        </p>
                        <el-divider />
                        <div class="summary-grid">
                            <div class="summary-item">
                                <label>色谱柱:</label>
                                <span>{{ getColumnDisplayName(methodData.column_id) }}</span>
                            </div>
                            <div class="summary-item">
                                <label>流速(mL/min):</label>
                                <span>{{ methodData.flowRate }}</span>
                            </div>
                            <div class="summary-item">
                                <label>运行时间(min):</label>
                                <span>{{ methodData.runTime }}</span>
                            </div>
                            <div class="summary-item">
                                <label>A通道波长(nm):</label>
                                <span>{{ methodData.wavelengthA }}</span>
                            </div>
                            <div class="summary-item">
                                <label>B通道波长(nm):</label>
                                <span>{{ methodData.wavelengthB }}</span>
                            </div>
                            <div class="summary-item">
                                <label>梯度模式:</label>
                                <span>{{
                                    methodData.gradientMode === "auto"
                                        ? "自动梯度"
                                        : "手动梯度"
                                }}</span>
                            </div>
                        </div>

                        <!-- 自动梯度参数详情 -->
                        <div
                            v-if="methodData.gradientMode === 'auto'"
                            class="gradient-details"
                        >
                            <el-divider content-position="left"
                                >自动梯度参数</el-divider
                            >
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <label>起始比例:</label>
                                    <span
                                        >{{
                                            methodData.autoGradient.startRatio
                                        }}%</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>结束比例:</label>
                                    <span
                                        >{{
                                            methodData.autoGradient.endRatio
                                        }}%</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>N1柱体积数:</label>
                                    <span>{{
                                        methodData.autoGradient.n1Volumes
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>梯度速率:</label>
                                    <span>{{
                                        methodData.autoGradient.gradientRate
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>峰阈值:</label>
                                    <span>{{
                                        methodData.autoGradient.peakThreshold
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>柱体积:</label>
                                    <span
                                        >{{
                                            methodData.autoGradient.columnVolume
                                        }}
                                        mL</span
                                    >
                                </div>
                                <div class="summary-item">
                                    <label>SG滤波窗口:</label>
                                    <span>{{
                                        methodData.autoGradient.sgWindow
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>SG滤波阶数:</label>
                                    <span>{{
                                        methodData.autoGradient.sgOrder
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>基线窗口:</label>
                                    <span>{{
                                        methodData.autoGradient.baselineWindow
                                    }}</span>
                                </div>
                                <div class="summary-item">
                                    <label>K因子:</label>
                                    <span>{{
                                        methodData.autoGradient.kFactor
                                    }}</span>
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
                @click="saveMethod"
                >保存方法</el-button
            >
            <el-button @click="$emit('cancel')">取消</el-button>
        </div>

        <!-- 参数解释弹窗 -->
        <el-dialog
            v-model="showParamHelp"
            title="自动梯度参数说明"
            width="70%"
            class="param-help-dialog"
        >
            <div class="param-help-content">
                <div
                    v-for="(param, key) in paramHelp"
                    :key="key"
                    class="param-help-item"
                >
                    <div class="param-title">
                        <el-icon class="param-icon"><InfoFilled /></el-icon>
                        {{ param.title }}
                    </div>
                    <div class="param-description">
                        {{ param.description }}
                    </div>
                </div>
            </div>
            <template #footer>
                <el-button @click="showParamHelp = false" type="primary">
                    我知道了
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";

export default {
    name: "MethodCreateWizard",
    emits: ["save", "cancel"],
    setup(props, { emit }) {
        const currentStep = ref(0);

        // 生成默认方法名称：方法-时间戳
        const generateDefaultMethodName = () => {
            const timestamp = new Date()
                .toISOString()
                .slice(0, 19)
                .replace(/[T:-]/g, "")
                .slice(0, 14);
            return `方法-${timestamp}`;
        };

        // 模拟Smlies数据列表，实际应从后端获取
        const smliesList = ref([
            "CCO",
            "CC(=O)O",
            "CC(C)O",
            "CCC(=O)O",
            "CC(C)(C)O",
            "CCCO",
            "CC(C)CO",
            "CCCCO",
            "CC(C)CCO",
            "CCCCCO",
            "C1CCC(CC1)O",
            "C1CCCCC1O",
            "C1=CC=CC=C1O",
            "CC1=CC=CC=C1O",
            "CC(C)(C)C1=CC=C(C=C1)O",
            "C1=CC=C(C=C1)CO",
            "CC1=CC=C(C=C1)CO",
            "C1=CC=C(C=C1)CCO",
        ]);

        // 过滤后的Smlies列表，支持模糊查询
        const filteredSmliesList = computed(() => {
            if (!methodData.value.smlies) {
                return smliesList.value;
            }
            return smliesList.value.filter((item) =>
                item
                    .toLowerCase()
                    .includes(methodData.value.smlies.toLowerCase())
            );
        });

        // 参数解释弹窗状态
        const showParamHelp = ref(false);
        const columns = ref([]);
        const columnsLoading = ref(false);

        // 参数解释数据
        const paramHelp = {
            startRatio: {
                title: "起始比例 (%)",
                description:
                    "自动梯度开始时有机相的初始百分比，通常设置较高的有机相比例以保证样品的初始溶解性。",
            },
            endRatio: {
                title: "结束比例 (%)",
                description:
                    "自动梯度结束时有机相的最终百分比，通常设置较低的有机相比例以实现完全洗脱。",
            },
            n1Volumes: {
                title: "N1柱体积数",
                description:
                    "用于计算梯度时间的柱体积倍数，影响梯度变化的速度和分离效果。",
            },
            gradientRate: {
                title: "梯度速率",
                description:
                    "梯度变化的速度参数，控制有机相浓度随时间变化的快慢，影响峰的分离度。",
            },
            peakThreshold: {
                title: "峰阈值",
                description:
                    "用于峰检测的最小信号阈值，低于此值的信号将被忽略，有助于过滤噪声。",
            },
            columnVolume: {
                title: "柱体积 (mL)",
                description:
                    "色谱柱的体积，用于计算死时间和优化梯度参数，影响分离效果。",
            },
            sgWindow: {
                title: "SG滤波窗口",
                description:
                    "Savitzky-Golay滤波器的窗口大小，用于数据平滑处理，减少基线噪声。",
            },
            sgOrder: {
                title: "SG滤波阶数",
                description:
                    "Savitzky-Golay滤波器的多项式阶数，影响数据平滑的效果和细节保留程度。",
            },
            baselineWindow: {
                title: "基线窗口",
                description:
                    "基线校正的窗口大小，用于消除基线漂移，提高峰识别的准确性。",
            },
            kFactor: {
                title: "K因子",
                description:
                    "容量因子，表示化合物在固定相和流动相之间的分配比，影响保留时间和分离度。",
            },
        };

        const methodData = ref({
            name: generateDefaultMethodName(),
            smlies: "",
            type: "user",
            column_id: null,
            flowRate: 1.0,
            runTime: 30,
            wavelengthA: 254,
            wavelengthB: 280,
            gradientMode: "auto",
            autoGradient: {
                startRatio: 80,
                endRatio: 20,
                n1Volumes: 5.0,
                gradientRate: 1.0,
                peakThreshold: 0.01,
                columnVolume: 57,
                sgWindow: 5,
                sgOrder: 2,
                baselineWindow: 10,
                kFactor: 1.5,
            },
            manualGradient: [
                {
                    time: 0,
                    solutionA: 80,
                    solutionB: 20,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
                {
                    time: 30,
                    solutionA: 20,
                    solutionB: 80,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
            ],
        });

        const nextStep = () => {
            // 在第3步（梯度设置）时进行校验
            if (
                currentStep.value === 2 &&
                methodData.value.gradientMode === "manual"
            ) {
                const validation = validateAllGradientRows();
                if (!validation.isValid) {
                    ElMessage.error({
                        message:
                            "梯度配置有误：" + validation.errors.join("；"),
                        duration: 5000,
                        showClose: true,
                    });
                    return; // 阻止进入下一步
                }
            }

            if (currentStep.value < 3) {
                currentStep.value++;
            }
        };

        const previousStep = () => {
            if (currentStep.value > 0) {
                currentStep.value--;
            }
        };

        const addGradientStep = () => {
            const lastStep =
                methodData.value.manualGradient[
                    methodData.value.manualGradient.length - 1
                ];
            methodData.value.manualGradient.push({
                time: lastStep.time + 10,
                solutionA: 50,
                solutionB: 50,
                solutionC: 0,
                solutionD: 0,
                flowRate: 1.0,
            });
        };

        // 计算原液总和
        const getGradientSum = (row) => {
            const sum =
                (row.solutionA || 0) +
                (row.solutionB || 0) +
                (row.solutionC || 0) +
                (row.solutionD || 0);
            return Math.round(sum * 100) / 100; // 保留2位小数
        };

        // 获取总和文本类型（用于颜色显示）
        const getGradientSumType = (row) => {
            const sum = getGradientSum(row);
            return sum === 100 ? "success" : "danger";
        };

        // 获取行样式类名
        const getRowClassName = ({ row, rowIndex }) => {
            const sum = getGradientSum(row);
            return sum !== 100 ? "gradient-error-row" : "";
        };

        // 校验单行梯度数据
        const validateGradientRow = (index) => {
            const row = methodData.value.manualGradient[index];
            const sum = getGradientSum(row);
            if (sum !== 100) {
                console.warn(`第${index + 1}行原液总和为${sum}%，应为100%`);
            }
        };

        // 校验所有梯度数据
        const validateAllGradientRows = () => {
            if (methodData.value.gradientMode !== "manual") return true;

            const errors = [];
            methodData.value.manualGradient.forEach((row, index) => {
                const sum = getGradientSum(row);
                if (sum !== 100) {
                    errors.push(`第${index + 1}行原液总和为${sum}%，应为100%`);
                }
            });

            return {
                isValid: errors.length === 0,
                errors: errors,
            };
        };

        const removeGradientStep = (index) => {
            if (methodData.value.manualGradient.length > 1) {
                methodData.value.manualGradient.splice(index, 1);
            }
        };

        // 处理Smlies选择变化，自动添加新值到列表
        const handleSmliesChange = (value) => {
            if (value && !smliesList.value.includes(value)) {
                smliesList.value.push(value);
                console.log(`新增Smlies: ${value}`);
            }
        };

        // 获取Smlies列表（模拟从后端获取）
        const fetchSmliesList = async () => {
            // 这里应该是实际的API调用
            // const response = await api.getSmliesList();
            // smliesList.value = response.data;
            console.log("已加载Smlies列表", smliesList.value.length, "项");
        };

        // 获取色谱柱列表
        const fetchColumns = async () => {
            columnsLoading.value = true;
            try {
                const response = await fetch('http://localhost:8008/api/columns/');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                if (data.success && data.columns) {
                    columns.value = data.columns;
                    console.log('获取色谱柱列表成功:', columns.value.length);
                } else {
                    throw new Error(data.message || '获取色谱柱列表失败');
                }
            } catch (error) {
                console.error('获取色谱柱列表失败:', error);
                ElMessage.error({
                    message: `获取色谱柱列表失败: ${error.message}`,
                    duration: 5000
                });
            } finally {
                columnsLoading.value = false;
            }
        };

        // 计算选中的色谱柱信息
        const selectedColumn = computed(() => {
            if (!methodData.value.column_id || !columns.value.length) return null;
            return columns.value.find(col => col.column_id === methodData.value.column_id);
        });

        // 获取色谱柱显示名称
        const getColumnDisplayName = (columnId) => {
            if (!columnId || !columns.value.length) return '未选择';
            const column = columns.value.find(col => col.column_id === columnId);
            return column ? `${column.column_code} (${column.specification_g}g)` : `ID: ${columnId}`;
        };

        const saveMethod = () => {
            // 保存前确保新输入的Smlies已添加到列表
            if (
                methodData.value.smlies &&
                !smliesList.value.includes(methodData.value.smlies)
            ) {
                handleSmliesChange(methodData.value.smlies);
            }
            emit("save", methodData.value);
        };

        // 组件挂载时获取数据
        onMounted(() => {
            fetchSmliesList();
            fetchColumns();
        });

        return {
            currentStep,
            methodData,
            smliesList,
            filteredSmliesList,
            showParamHelp,
            paramHelp,
            columns,
            columnsLoading,
            selectedColumn,
            getColumnDisplayName,
            nextStep,
            previousStep,
            addGradientStep,
            removeGradientStep,
            getGradientSum,
            getGradientSumType,
            getRowClassName,
            validateGradientRow,
            validateAllGradientRows,
            handleSmliesChange,
            fetchSmliesList,
            saveMethod,
        };
    },
};
</script>

<style scoped>
.method-create-wizard {
    padding: 20px;
}

.wizard-content {
    margin: 30px 0;
    min-height: 400px;
}

.step-content {
    padding: 20px;
}

.step-content h3 {
    margin: 0 0 20px 0;
    color: #333;
}

.summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
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

/* 参数区域样式 */
.param-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 20px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #ebeef5;
}

.param-section-header h4 {
    margin: 0;
    color: #333;
    font-size: 16px;
    font-weight: 600;
}

/* 参数解释弹窗样式 */
.param-help-content {
    max-height: 60vh;
    overflow-y: auto;
}

.param-help-item {
    margin-bottom: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #409eff;
}

.param-title {
    display: flex;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
}

.param-icon {
    margin-right: 8px;
    color: #409eff;
}

.param-description {
    font-size: 14px;
    line-height: 1.6;
    color: #666;
    text-indent: 2em;
}

/* 梯度详情样式 */
.gradient-details {
    margin-top: 16px;
}

.gradient-details .summary-grid {
    margin-top: 12px;
}

/* 参数解释弹窗样式调整 */
:deep(.param-help-dialog .el-dialog__body) {
    padding: 20px;
}

:deep(.param-help-dialog .el-dialog__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px 20px;
}

:deep(.param-help-dialog .el-dialog__title) {
    color: white;
    font-weight: 600;
}

/* 手动梯度校验样式 */
.gradient-validation-info {
    display: flex;
    align-items: center;
    gap: 8px;
}

:deep(.gradient-error-row) {
    background-color: #fef2f2 !important;
}

:deep(.gradient-error-row:hover) {
    background-color: #fee2e2 !important;
}

/* 梯度表格样式优化 */
:deep(.el-table .el-input-number) {
    width: 100%;
}

:deep(.el-table .el-input-number .el-input__inner) {
    text-align: center;
}

/* 总和列样式 */
:deep(.el-table td) {
    padding: 8px 0;
}

.param-section-header .gradient-validation-info .el-text {
    font-size: 13px;
}

/* 色谱柱选项样式 */
.column-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.column-code {
    font-weight: 600;
    color: #333;
}

.column-spec {
    font-size: 12px;
    color: #999;
}

.form-help-text {
    margin-top: 4px;
}

</style>
