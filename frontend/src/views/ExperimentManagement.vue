<template>
    <div class="experiment-management">
        <!-- 实验状态概览 -->
        <el-row :gutter="20" class="status-overview">
            <el-col :span="6">
                <el-card class="status-card">
                    <div class="status-item">
                        <el-icon class="status-icon running"
                            ><VideoPlay
                        /></el-icon>
                        <div class="status-info">
                            <h3>当前实验</h3>
                            <p>
                                {{
                                    currentExperiment
                                        ? currentExperiment.experiment_name
                                        : "无"
                                }}
                            </p>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="status-card">
                    <div class="status-item">
                        <el-icon class="status-icon pending"><Clock /></el-icon>
                        <div class="status-info">
                            <h3>排队实验</h3>
                            <p>{{ queuedExperiments.length }} 个</p>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="status-card">
                    <div class="status-item">
                        <el-icon class="status-icon progress"
                            ><TrendCharts
                        /></el-icon>
                        <div class="status-info">
                            <h3>进度</h3>
                            <p>{{ currentProgress }}%</p>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="status-card">
                    <div class="status-item">
                        <el-icon class="status-icon time"><Timer /></el-icon>
                        <div class="status-info">
                            <h3>剩余时间</h3>
                            <p>{{ remainingTime }}</p>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20">
            <!-- 左侧：实验队列 -->
            <el-col :span="12">
                <!-- 实验列表 -->
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>实验列表</span>
                            <div class="header-buttons">
                                <el-button
                                    type="primary"
                                    @click="
                                        () => {
                                            isEditMode = false;
                                            editingExperiment = null;
                                            showCreateWizard = true;
                                        }
                                    "
                                >
                                    <el-icon><Plus /></el-icon>
                                    创建实验
                                </el-button>
                                <el-button
                                    @click="clearQueue"
                                    :disabled="totalExperiments === 0"
                                    :loading="loading"
                                >
                                    清空队列
                                </el-button>
                                <el-button
                                    @click="fetchAllExperiments"
                                    :loading="loading"
                                    icon="Refresh"
                                >
                                    刷新
                                </el-button>
                            </div>
                        </div>
                    </template>

                    <div class="experiment-queue" v-loading="loading">
                        <div
                            v-if="totalExperiments === 0 && !loading"
                            class="empty-queue"
                        >
                            <el-empty description="暂无实验" />
                        </div>
                        <div v-else>
                            <div
                                v-for="(
                                    experiment, index
                                ) in paginatedExperiments"
                                :key="experiment.experiment_id"
                                class="queue-item"
                                :class="{
                                    'queue-active':
                                        index === 0 && currentPage === 1,
                                    selected:
                                        selectedExperiment?.experiment_id ===
                                        experiment.experiment_id,
                                }"
                                @click="selectExperiment(experiment)"
                            >
                                <div class="queue-info">
                                    <h4>{{ experiment.experiment_name }}</h4>
                                    <p>
                                        方法:
                                        {{ experiment.method_id || "未指定" }}
                                    </p>
                                    <p>
                                        操作员:
                                        {{ experiment.operator || "未指定" }}
                                    </p>
                                    <p>
                                        状态:
                                        <el-tag
                                            :type="
                                                getExperimentStatusType(
                                                    experiment.status
                                                )
                                            "
                                            size="small"
                                        >
                                            {{
                                                getExperimentStatusText(
                                                    experiment.status
                                                )
                                            }}
                                        </el-tag>
                                    </p>
                                    <p>
                                        创建时间:
                                        {{ formatDate(experiment.created_at) }}
                                    </p>
                                </div>
                                <div class="queue-actions">
                                    <el-button
                                        size="small"
                                        @click.stop="
                                            editQueuedExperiment(experiment)
                                        "
                                    >
                                        <el-icon><Edit /></el-icon>
                                    </el-button>
                                    <el-button
                                        size="small"
                                        @click.stop="moveUp(index)"
                                        :disabled="index === 0"
                                    >
                                        <el-icon><Top /></el-icon>
                                    </el-button>
                                    <el-button
                                        size="small"
                                        @click.stop="moveDown(index)"
                                        :disabled="
                                            index ===
                                            queuedExperiments.length - 1
                                        "
                                    >
                                        <el-icon><Bottom /></el-icon>
                                    </el-button>
                                    <el-button
                                        size="small"
                                        type="danger"
                                        @click.stop="
                                            removeFromQueue(experiment)
                                        "
                                    >
                                        <el-icon><Delete /></el-icon>
                                    </el-button>
                                </div>
                            </div>

                            <!-- 分页组件 -->
                            <div
                                class="pagination-container"
                                v-if="totalExperiments > 0"
                            >
                                <el-pagination
                                    v-model:current-page="currentPage"
                                    v-model:page-size="pageSize"
                                    :page-sizes="[4, 8, 12, 20]"
                                    :small="true"
                                    :total="totalExperiments"
                                    layout="total, sizes, prev, pager, next, jumper"
                                    @size-change="handlePageSizeChange"
                                    @current-change="handlePageChange"
                                />
                            </div>
                        </div>
                    </div>
                </el-card>
            </el-col>

            <!-- 右侧：实验监控 -->
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <span>实验监控</span>
                    </template>

                    <div v-if="selectedExperiment" class="experiment-monitor">
                        <!-- 实验信息 -->
                        <div class="experiment-info">
                            <h3>{{ selectedExperiment.experiment_name }}</h3>
                            <p>
                                实验类型:
                                {{
                                    selectedExperiment.experiment_type || "标准"
                                }}
                            </p>
                            <p>
                                方法:
                                {{ selectedExperiment.method_id || "未指定" }}
                            </p>
                            <p>
                                操作员:
                                {{ selectedExperiment.operator || "未指定" }}
                            </p>
                            <p>
                                状态:
                                <el-tag
                                    :type="
                                        getExperimentStatusType(
                                            selectedExperiment.status
                                        )
                                    "
                                >
                                    {{
                                        getExperimentStatusText(
                                            selectedExperiment.status
                                        )
                                    }}
                                </el-tag>
                            </p>
                            <p>
                                优先级: {{ selectedExperiment.priority || 1 }}
                            </p>
                        </div>

                        <!-- 简要参数信息 -->
                        <div class="experiment-params">
                            <el-divider content-position="left"
                                >实验参数</el-divider
                            >
                            <el-row :gutter="10">
                                <el-col :span="12">
                                    <div class="param-item">
                                        <label>峰驱动:</label>
                                        <span>{{
                                            selectedExperiment.is_peak_driven
                                                ? "是"
                                                : "否"
                                        }}</span>
                                    </div>
                                </el-col>
                                <el-col :span="12">
                                    <div class="param-item">
                                        <label>收集体积:</label>
                                        <span
                                            >{{
                                                selectedExperiment.collection_volume_ml ||
                                                0
                                            }}
                                            ml</span
                                        >
                                    </div>
                                </el-col>
                                <el-col :span="12">
                                    <div class="param-item">
                                        <label>清洗体积:</label>
                                        <span
                                            >{{
                                                selectedExperiment.wash_volume_ml ||
                                                0
                                            }}
                                            ml</span
                                        >
                                    </div>
                                </el-col>
                                <el-col :span="12">
                                    <div class="param-item">
                                        <label>清洗次数:</label>
                                        <span>{{
                                            selectedExperiment.wash_cycles || 0
                                        }}</span>
                                    </div>
                                </el-col>
                            </el-row>
                        </div>

                        <!-- 预处理步骤进度 -->
                        <div
                            v-if="showPretreatmentProgress"
                            class="pretreatment-progress"
                        >
                            <el-divider content-position="left"
                                >预处理进度</el-divider
                            >

                            <!-- MQTT连接状态指示 -->
                            <div class="mqtt-status">
                                <el-tag
                                    :type="
                                        mqttConnected ? 'success' : 'warning'
                                    "
                                    size="small"
                                >
                                    {{
                                        mqttConnected
                                            ? "MQTT已连接"
                                            : "MQTT未连接"
                                    }}
                                </el-tag>
                            </div>

                            <!-- 当前步骤状态显示 -->
                            <div class="current-step-display">
                                <el-card class="step-card">
                                    <div class="step-details">
                                        <h4>
                                            <el-icon
                                                v-if="
                                                    preprocessingStatus ===
                                                    'started'
                                                "
                                                class="running-icon"
                                            >
                                                <Loading />
                                            </el-icon>
                                            <el-icon
                                                v-else-if="
                                                    preprocessingStatus ===
                                                    'completed'
                                                "
                                                class="completed-icon"
                                            >
                                                <Check />
                                            </el-icon>
                                            {{ getStepDisplayTitle() }}
                                        </h4>
                                        <p>{{ getStepDisplayDescription() }}</p>

                                        <!-- 状态指示器 -->
                                        <div class="status-indicator">
                                            <el-tag
                                                :type="getStatusTagType()"
                                                :effect="
                                                    preprocessingStatus ===
                                                    'started'
                                                        ? 'dark'
                                                        : 'plain'
                                                "
                                            >
                                                {{ getStatusDisplayText() }}
                                            </el-tag>
                                        </div>

                                        <!-- 预处理步骤列表 -->
                                        <div class="step-checklist">
                                            <div
                                                v-if="
                                                    selectedExperiment.purge_column
                                                "
                                                class="step-item"
                                                :class="
                                                    getStepItemClass(
                                                        'purge_column'
                                                    )
                                                "
                                            >
                                                <el-icon
                                                    ><CircleCheck
                                                /></el-icon>
                                                <span
                                                    >吹扫柱子 ({{
                                                        selectedExperiment.purge_column_time_min ||
                                                        5
                                                    }}分钟)</span
                                                >
                                            </div>
                                            <div
                                                v-if="
                                                    selectedExperiment.purge_system
                                                "
                                                class="step-item"
                                                :class="
                                                    getStepItemClass(
                                                        'purge_system'
                                                    )
                                                "
                                            >
                                                <el-icon
                                                    ><CircleCheck
                                                /></el-icon>
                                                <span>吹扫系统 (2分钟)</span>
                                            </div>
                                            <div
                                                v-if="
                                                    selectedExperiment.column_balance
                                                "
                                                class="step-item"
                                                :class="
                                                    getStepItemClass(
                                                        'column_equilibration'
                                                    )
                                                "
                                            >
                                                <el-icon
                                                    ><CircleCheck
                                                /></el-icon>
                                                <span
                                                    >柱平衡 - 溶液{{
                                                        getSolutionName(
                                                            selectedExperiment.column_conditioning_solution
                                                        )
                                                    }}
                                                    ({{
                                                        selectedExperiment.column_balance_time_min ||
                                                        10
                                                    }}分钟)</span
                                                >
                                            </div>
                                        </div>
                                    </div>
                                </el-card>
                            </div>
                        </div>

                        <!-- 实验步骤流程图 -->
                        <div
                            v-if="
                                selectedExperiment && experimentSteps.length > 0
                            "
                            class="experiment-steps-flowchart"
                        >
                            <h4 class="flowchart-title">实验流程</h4>
                            <div class="steps-container">
                                <div
                                    v-for="(step, index) in experimentSteps"
                                    :key="step"
                                    class="step-item"
                                    :class="{
                                        active: currentStepIndex === index,
                                        completed: index < currentStepIndex,
                                    }"
                                >
                                    <div class="step-icon">
                                        <el-icon v-if="index < currentStepIndex"
                                            ><Check
                                        /></el-icon>
                                        <el-icon
                                            v-else-if="
                                                currentStepIndex === index
                                            "
                                            ><Timer
                                        /></el-icon>
                                        <span v-else>{{ index + 1 }}</span>
                                    </div>
                                    <div class="step-label">
                                        {{ getStepDisplayName(step) }}
                                    </div>
                                    <div
                                        v-if="
                                            index < experimentSteps.length - 1
                                        "
                                        class="step-connector"
                                    >
                                        <div
                                            class="connector-line"
                                            :class="{
                                                active:
                                                    index < currentStepIndex,
                                            }"
                                        ></div>
                                        <el-icon class="connector-arrow"
                                            ><ArrowRight
                                        /></el-icon>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 控制按钮 -->
                        <div class="control-buttons">
                            <!-- 实验未开始状态 -->
                            <el-button
                                v-if="selectedExperiment.status === 'pending'"
                                type="primary"
                                size="large"
                                @click="startExperiment(selectedExperiment)"
                            >
                                <el-icon><VideoPlay /></el-icon>
                                开始实验
                            </el-button>

                            <!-- 实验进行中状态 -->
                            <template
                                v-if="
                                    ['running', 'pretreatment'].includes(
                                        selectedExperiment.status
                                    )
                                "
                            >
                                <!-- 暂停/继续按钮 -->
                                <el-button
                                    v-if="!experimentPaused"
                                    type="warning"
                                    size="large"
                                    @click="pauseExperiment(selectedExperiment)"
                                >
                                    <el-icon><VideoPause /></el-icon>
                                    暂停
                                </el-button>
                                <el-button
                                    v-else
                                    type="success"
                                    size="large"
                                    @click="
                                        resumeExperiment(selectedExperiment)
                                    "
                                >
                                    <el-icon><VideoPlay /></el-icon>
                                    继续
                                </el-button>

                                <!-- 终止按钮 -->
                                <el-button
                                    type="danger"
                                    size="large"
                                    @click="
                                        terminateExperiment(selectedExperiment)
                                    "
                                >
                                    <el-icon><CircleClose /></el-icon>
                                    终止
                                </el-button>

                                <!-- 跳转到实时监控按钮
                                <el-button
                                    type="info"
                                    size="large"
                                    @click="goToRealtimeMonitoring"
                                >
                                    <el-icon><Monitor /></el-icon>
                                    实时监控
                                </el-button> -->
                            </template>

                            <!-- 实验暂停状态 -->
                            <template
                                v-if="selectedExperiment.status === 'paused'"
                            >
                                <el-button
                                    type="success"
                                    size="large"
                                    @click="
                                        resumeExperiment(selectedExperiment)
                                    "
                                >
                                    <el-icon><VideoPlay /></el-icon>
                                    继续
                                </el-button>
                                <el-button
                                    type="danger"
                                    size="large"
                                    @click="
                                        terminateExperiment(selectedExperiment)
                                    "
                                >
                                    <el-icon><CircleClose /></el-icon>
                                    终止
                                </el-button>
                            </template>
                        </div>

                        <!-- 运行状态显示 -->
                        <div
                            v-if="selectedExperiment.status === 'running'"
                            class="running-status"
                        >
                            <el-divider content-position="left"
                                >运行状态</el-divider
                            >
                            <div class="progress-section">
                                <el-progress
                                    :percentage="
                                        getExperimentProgress(
                                            selectedExperiment
                                        )
                                    "
                                    :status="progressStatus"
                                    stroke-width="12"
                                />
                                <div class="time-info">
                                    <span
                                        >已运行:
                                        {{
                                            getElapsedTime(selectedExperiment)
                                        }}</span
                                    >
                                    <span
                                        >剩余:
                                        {{
                                            getRemainingTime(selectedExperiment)
                                        }}</span
                                    >
                                </div>
                            </div>

                            <div class="current-status">
                                <el-row :gutter="10">
                                    <el-col :span="12">
                                        <div class="status-item-small">
                                            <label>当前试管:</label>
                                            <span class="status-value">{{
                                                selectedExperiment.currentTube ||
                                                1
                                            }}</span>
                                        </div>
                                    </el-col>
                                    <el-col :span="12">
                                        <div class="status-item-small">
                                            <label>检测峰数:</label>
                                            <span class="status-value">{{
                                                selectedExperiment.peakCount ||
                                                0
                                            }}</span>
                                        </div>
                                    </el-col>
                                </el-row>
                            </div>
                        </div>
                    </div>

                    <div v-else class="no-selection">
                        <el-empty description="请选择实验查看详情" />
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 实验创建向导对话框 -->
        <el-dialog
            v-model="showCreateWizard"
            :title="isEditMode ? '编辑实验' : '创建新实验'"
            width="80%"
            :before-close="handleCloseWizard"
        >
            <ExperimentCreateWizard
                :is-edit-mode="isEditMode"
                :experiment-data="editingExperiment"
                @save="handleSaveExperiment"
                @cancel="
                    () => {
                        showCreateWizard = false;
                        isEditMode = false;
                        editingExperiment = null;
                    }
                "
            />
        </el-dialog>

        <!-- 预处理对话框 -->
        <el-dialog v-model="showPretreatment" title="系统预处理" width="60%">
            <PretreatmentPanel
                @start="handleStartPretreatment"
                @complete="handlePretreatmentComplete"
            />
        </el-dialog>

        <!-- 实验结束处理对话框 -->
        <el-dialog v-model="showEndProcessing" title="实验结束处理" width="70%">
            <ExperimentEndProcessing
                :experiment="currentExperiment"
                @save="handleSaveExperimentData"
                @merge="handleMergeCollections"
                @clean="handleCleanTubes"
            />
        </el-dialog>
    </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, inject } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Check, Timer, ArrowRight } from "@element-plus/icons-vue";
import ExperimentCreateWizard from "../components/experiment/ExperimentCreateWizard.vue";
import PretreatmentPanel from "../components/experiment/PretreatmentPanel.vue";
import ExperimentEndProcessing from "../components/experiment/ExperimentEndProcessing.vue";
import mqttService from "../services/mqtt-service.js";

export default {
    name: "ExperimentManagement",
    components: {
        ExperimentCreateWizard,
        PretreatmentPanel,
        ExperimentEndProcessing,
    },
    setup() {
        const $router = inject("$router") || {
            push: (path) => {
                window.location.href = path;
            },
        };

        const showCreateWizard = ref(false);
        const showPretreatment = ref(false);
        const showEndProcessing = ref(false);
        const selectedTube = ref("");
        const isWasteMode = ref(false);
        const selectedExperiment = ref(null);
        const loading = ref(false);
        const isEditMode = ref(false);
        const editingExperiment = ref(null);

        // 实验步骤相关
        const experimentSteps = ref([]);
        const currentStepIndex = ref(0);

        // 预处理相关状态
        const showPretreatmentProgress = ref(false);
        const currentPretreatmentStep = ref("");
        const preprocessingStatus = ref("");
        const experimentPaused = ref(false);
        const mqttConnected = ref(false);

        // 当前实验
        const currentExperiment = ref(null);

        // 实验列表
        const queuedExperiments = ref([]);
        const allExperiments = ref([]);

        // 分页相关状态
        const currentPage = ref(1);
        const pageSize = ref(4);
        const totalExperiments = ref(0);
        const paginatedExperiments = ref([]);

        // 快速方法
        const quickMethods = ref([
            { id: 1, name: "标准分析" },
            { id: 2, name: "快速检测" },
            { id: 3, name: "高分辨分离" },
        ]);

        // 可用试管
        const availableTubes = computed(() => {
            return Array.from({ length: 40 }, (_, i) => i + 1);
        });

        // 当前进度
        const currentProgress = computed(() => {
            if (!currentExperiment.value) return 0;
            const elapsed =
                Date.now() - currentExperiment.value.startTime.getTime();
            const total = currentExperiment.value.estimatedDuration * 60 * 1000;
            return Math.min(Math.round((elapsed / total) * 100), 100);
        });

        // 进度状态
        const progressStatus = computed(() => {
            if (currentExperiment.value?.status === "paused") return "warning";
            if (currentExperiment.value?.status === "error") return "exception";
            return "success";
        });

        // 已运行时间
        const elapsedTime = computed(() => {
            if (!currentExperiment.value) return "0分钟";
            const elapsed =
                Date.now() - currentExperiment.value.startTime.getTime();
            const minutes = Math.floor(elapsed / (60 * 1000));
            return `${minutes}分钟`;
        });

        // 剩余时间
        const remainingTime = computed(() => {
            if (!currentExperiment.value) return "0分钟";
            const elapsed =
                Date.now() - currentExperiment.value.startTime.getTime();
            const total = currentExperiment.value.estimatedDuration * 60 * 1000;
            const remaining = Math.max(0, total - elapsed);
            const minutes = Math.floor(remaining / (60 * 1000));
            return `${minutes}分钟`;
        });

        const getStatusType = (status) => {
            const statusMap = {
                running: "success",
                paused: "warning",
                stopped: "info",
                error: "danger",
            };
            return statusMap[status] || "info";
        };

        const getStatusText = (status) => {
            const statusMap = {
                running: "运行中",
                paused: "已暂停",
                stopped: "已停止",
                error: "异常",
            };
            return statusMap[status] || status;
        };

        const getPressureClass = (pressure) => {
            if (pressure > 350) return "danger";
            if (pressure > 200) return "warning";
            return "normal";
        };

        const getExperimentStatusType = (status) => {
            const statusMap = {
                pending: "info",
                未结束: "warning",
                running: "success",
                paused: "warning",
                stopped: "info",
                completed: "success",
                error: "danger",
            };
            return statusMap[status] || "info";
        };

        const getExperimentStatusText = (status) => {
            const statusMap = {
                pending: "等待中",
                未结束: "未结束",
                running: "运行中",
                paused: "已暂停",
                stopped: "已停止",
                completed: "已完成",
                error: "异常",
            };
            return statusMap[status] || status;
        };

        const selectExperiment = (experiment) => {
            selectedExperiment.value = experiment;
            // 获取实验步骤
            if (experiment && experiment.experiment_id) {
                fetchExperimentSteps(experiment.experiment_id);
            }
        };

        const getExperimentProgress = (experiment) => {
            if (!experiment.startTime) return 0;
            const elapsed = Date.now() - experiment.startTime.getTime();
            const total = parseInt(experiment.estimatedTime) * 60 * 1000;
            return Math.min(Math.round((elapsed / total) * 100), 100);
        };

        const getElapsedTime = (experiment) => {
            if (!experiment.startTime) return "0分钟";
            const elapsed = Date.now() - experiment.startTime.getTime();
            const minutes = Math.floor(elapsed / (60 * 1000));
            return `${minutes}分钟`;
        };

        const getRemainingTime = (experiment) => {
            if (!experiment.startTime) return experiment.estimatedTime;
            const elapsed = Date.now() - experiment.startTime.getTime();
            const total = parseInt(experiment.estimatedTime) * 60 * 1000;
            const remaining = Math.max(0, total - elapsed);
            const minutes = Math.floor(remaining / (60 * 1000));
            return `${minutes}分钟`;
        };

        const createQuickExperiment = (method) => {
            console.log("快速创建实验:", method.name);
        };

        // 分页相关函数
        const updatePaginatedExperiments = () => {
            totalExperiments.value = queuedExperiments.value.length;
            const start = (currentPage.value - 1) * pageSize.value;
            const end = start + pageSize.value;
            paginatedExperiments.value = queuedExperiments.value.slice(
                start,
                end
            );
        };

        const handlePageChange = (page) => {
            currentPage.value = page;
            updatePaginatedExperiments();
        };

        const handlePageSizeChange = (size) => {
            pageSize.value = size;
            currentPage.value = 1; // 重置到第一页
            updatePaginatedExperiments();
        };

        // 辅助函数：转换优先级
        const convertPriorityToNumber = (priority) => {
            const priorityMap = {
                low: 1,
                normal: 3,
                high: 7,
                urgent: 10,
            };
            return priorityMap[priority] || 1;
        };

        const convertPriorityToString = (priority) => {
            if (priority <= 2) return "low";
            if (priority <= 5) return "normal";
            if (priority <= 8) return "high";
            return "urgent";
        };

        // API调用函数
        const fetchAllExperiments = async () => {
            loading.value = true;
            try {
                const response = await fetch(
                    "http://0.0.0.0:8008/api/experiment_mgmt/?limit=100"
                );
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        allExperiments.value = data.experiments;
                        // 根据状态分类实验
                        queuedExperiments.value = data.experiments.filter(
                            (exp) => ["pending", "未结束"].includes(exp.status)
                        );
                        // 查找当前运行的实验
                        const runningExp = data.experiments.find(
                            (exp) => exp.status === "running"
                        );
                        if (runningExp) {
                            currentExperiment.value = runningExp;
                        }

                        // 更新分页
                        updatePaginatedExperiments();

                        console.log("获取实验列表成功:", data.total_count);
                    } else {
                        throw new Error(data.message || "获取实验列表失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("获取实验列表失败:", error);
                ElMessage.error("获取实验列表失败: " + error.message);
            } finally {
                loading.value = false;
            }
        };

        const createExperiment = async (experimentData) => {
            try {
                // 验证必需字段
                if (!experimentData.name) {
                    throw new Error("实验名称不能为空");
                }
                if (!experimentData.methodId && !experimentData.method) {
                    throw new Error("必须选择分析方法");
                }

                const requestData = {
                    experiment_name: experimentData.name,
                    experiment_type: experimentData.type || "standard",
                    method_id: experimentData.methodId || experimentData.method,
                    operator: experimentData.operator || "unknown",
                    purge_system: experimentData.purgeSystem || false,
                    purge_column: experimentData.purgeColumn || false,
                    purge_column_time_min: experimentData.purgeColumnTime || 0,
                    column_balance: experimentData.columnBalance || false,
                    column_balance_time_min:
                        experimentData.columnBalanceTime || 0,
                    column_conditioning_solution:
                        experimentData.columnConditioningSolution || null,
                    is_peak_driven: experimentData.isPeakDriven || false,
                    collection_volume_ml:
                        experimentData.collectionVolume || 0.0,
                    wash_volume_ml: experimentData.washVolume || 0.0,
                    wash_cycles: experimentData.washCycles || 0,
                    scheduled_start_time:
                        experimentData.scheduledStartTime || null,
                    priority: convertPriorityToNumber(experimentData.priority),
                    description: experimentData.description,
                    experiment_description:
                        experimentData.experimentDescription || null,
                };

                const response = await fetch(
                    "http://0.0.0.0:8008/api/experiment_mgmt/",
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
                    if (data.success) {
                        ElMessage.success("实验创建成功");
                        await fetchAllExperiments(); // 刷新列表
                        return data.experiment;
                    } else {
                        throw new Error(data.message || "创建实验失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("创建实验失败:", error);
                ElMessage.error("创建实验失败: " + error.message);
                throw error;
            }
        };

        const updateExperiment = async (experimentId, updateData) => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/experiment_mgmt/${experimentId}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(updateData),
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success("实验更新成功");
                        await fetchAllExperiments(); // 刷新列表
                        return data.experiment;
                    } else {
                        throw new Error(data.message || "更新实验失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("更新实验失败:", error);
                ElMessage.error("更新实验失败: " + error.message);
                throw error;
            }
        };

        const deleteExperiment = async (experimentId) => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/experiment_mgmt/${experimentId}`,
                    {
                        method: "DELETE",
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        ElMessage.success("实验删除成功");
                        await fetchAllExperiments(); // 刷新列表
                        return true;
                    } else {
                        throw new Error(data.message || "删除实验失败");
                    }
                } else {
                    throw new Error("API请求失败");
                }
            } catch (error) {
                console.error("删除实验失败:", error);
                ElMessage.error("删除实验失败: " + error.message);
                return false;
            }
        };

        const clearQueue = async () => {
            try {
                await ElMessageBox.confirm(
                    "确定要清空所有等待中的实验吗？此操作不可撤销。",
                    "清空队列",
                    {
                        confirmButtonText: "确定",
                        cancelButtonText: "取消",
                        type: "warning",
                    }
                );

                // 删除所有pending状态的实验
                const pendingExperiments = queuedExperiments.value.filter(
                    (exp) => ["pending", "未结束"].includes(exp.status)
                );

                for (const experiment of pendingExperiments) {
                    await deleteExperiment(experiment.experiment_id);
                }
            } catch (error) {
                // 用户取消或删除失败
                console.log("清空队列操作取消或失败");
            }
        };

        const editQueuedExperiment = (experiment) => {
            // 设置为编辑模式并传入实验数据
            isEditMode.value = true;
            editingExperiment.value = experiment;
            showCreateWizard.value = true;
            console.log("编辑排队实验:", experiment.experiment_name);
        };

        const moveUp = (index) => {
            if (index > 0) {
                const item = queuedExperiments.value.splice(index, 1)[0];
                queuedExperiments.value.splice(index - 1, 0, item);
            }
        };

        const moveDown = (index) => {
            if (index < queuedExperiments.value.length - 1) {
                const item = queuedExperiments.value.splice(index, 1)[0];
                queuedExperiments.value.splice(index + 1, 0, item);
            }
        };

        const removeFromQueue = async (experiment) => {
            try {
                await ElMessageBox.confirm(
                    `确定要删除实验 "${experiment.experiment_name}" 吗？`,
                    "删除实验",
                    {
                        confirmButtonText: "确定",
                        cancelButtonText: "取消",
                        type: "warning",
                    }
                );

                await deleteExperiment(experiment.experiment_id);
            } catch (error) {
                // 用户取消或删除失败
                console.log("删除实验操作取消或失败");
            }
        };

        const startExperiment = async (experiment) => {
            try {
                // 保存选择的实验数据到localStorage
                localStorage.setItem(
                    "currentExperiment",
                    JSON.stringify(experiment)
                );

                // 获取实验步骤
                await fetchExperimentSteps(experiment.experiment_id);

                // 检查是否需要预处理
                const needsPretreatment =
                    experiment.purge_system ||
                    experiment.purge_column ||
                    experiment.column_balance;

                if (needsPretreatment) {
                    // 设置实验状态为等待预处理开始
                    experiment.status = "pretreatment";
                    showPretreatmentProgress.value = true;

                    // 发送开始实验请求到后端（后端会开始MQTT消息序列）
                    await startExperimentAPI(experiment.experiment_id);

                    console.log(
                        "已请求开始实验预处理阶段:",
                        experiment.experiment_name
                    );
                    ElMessage.success("实验启动请求已发送，等待预处理开始...");
                } else {
                    // 直接开始实验（无预处理）
                    experiment.status = "running";
                    await startExperimentAPI(experiment.experiment_id);
                    $router.push("/realtime-monitoring");
                    console.log(
                        "开始实验，跳转到实时监控界面:",
                        experiment.experiment_name
                    );
                }
            } catch (error) {
                console.error("启动实验失败:", error);
                ElMessage.error("启动实验失败: " + error.message);
            }
        };

        // 调用后端API开始实验
        const startExperimentAPI = async (experimentId) => {
            const response = await fetch(
                `http://0.0.0.0:8008/api/experiments/data/collection/start?experiment_id=${experimentId}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error("启动实验API调用失败");
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || "启动实验失败");
            }

            return result;
        };

        // 获取实验步骤
        const fetchExperimentSteps = async (experimentId) => {
            console.log("开始获取实验步骤, experimentId:", experimentId);
            try {
                const url = `http://0.0.0.0:8008/api/v1/experiment_mgmt/${experimentId}/steps`;
                console.log("请求URL:", url);

                const response = await fetch(url, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                console.log("响应状态:", response.status);

                if (!response.ok) {
                    throw new Error(`获取实验步骤失败: ${response.status}`);
                }

                const result = await response.json();
                console.log("API响应结果:", result);

                if (result.success) {
                    experimentSteps.value = result.steps || [];
                    currentStepIndex.value = 0;
                    console.log("实验步骤设置成功:", experimentSteps.value);
                } else {
                    console.warn("获取实验步骤失败:", result.message);
                    experimentSteps.value = [];
                }
            } catch (error) {
                console.error("获取实验步骤API调用失败:", error);

                // 如果API失败，提供默认步骤用于测试
                console.log("使用默认步骤进行测试");
                experimentSteps.value = [
                    "purge_column",
                    "purge_system",
                    "column_equilibration",
                    "collect",
                    "post_processing",
                ];
                currentStepIndex.value = 0;
            }
        };

        // 获取步骤显示名称
        const getStepDisplayName = (step) => {
            const stepNames = {
                purge_column: "吹扫柱子",
                purge_system: "吹扫系统",
                column_equilibration: "润柱",
                collect: "收集",
                post_processing: "后处理",
            };
            return stepNames[step] || step;
        };

        const pauseExperiment = async (experiment) => {
            try {
                experimentPaused.value = true;
                experiment.experimentPaused = true;

                // 调用后端API暂停实验
                await pauseExperimentAPI(experiment.experiment_id);

                // 更新localStorage
                localStorage.setItem(
                    "currentExperiment",
                    JSON.stringify(experiment)
                );

                console.log("暂停实验:", experiment.experiment_name);
                ElMessage.info("实验已暂停");
            } catch (error) {
                console.error("暂停实验失败:", error);
                ElMessage.error("暂停实验失败: " + error.message);
                experimentPaused.value = false;
                experiment.experimentPaused = false;
            }
        };

        const resumeExperiment = async (experiment) => {
            try {
                experimentPaused.value = false;
                experiment.experimentPaused = false;

                // 调用后端API继续实验
                await resumeExperimentAPI(experiment.experiment_id);

                // 更新localStorage
                localStorage.setItem(
                    "currentExperiment",
                    JSON.stringify(experiment)
                );

                console.log("继续实验:", experiment.experiment_name);
                ElMessage.success("实验已继续");
            } catch (error) {
                console.error("继续实验失败:", error);
                ElMessage.error("继续实验失败: " + error.message);
                experimentPaused.value = true;
                experiment.experimentPaused = true;
            }
        };

        // 后端API调用函数
        const pauseExperimentAPI = async (experimentId) => {
            const response = await fetch(
                `http://0.0.0.0:8008/api/experiments/data/collection/pause?experiment_id=${experimentId}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error("暂停实验API调用失败");
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || "暂停实验失败");
            }

            return result;
        };

        const resumeExperimentAPI = async (experimentId) => {
            const response = await fetch(
                `http://0.0.0.0:8008/api/experiments/data/collection/resume?experiment_id=${experimentId}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error("继续实验API调用失败");
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || "继续实验失败");
            }

            return result;
        };

        const stopExperiment = (experiment) => {
            experiment.status = "stopped";
            showEndProcessing.value = true;
            console.log("停止实验:", experiment.name);
        };

        const switchTube = () => {
            currentExperiment.value.currentTube = selectedTube.value;
            console.log("切换到试管:", selectedTube.value);
        };

        const switchCollectionMode = (value) => {
            currentExperiment.value.collectionMode = value ? "废液" : "收集";
            console.log(
                "切换收集模式:",
                currentExperiment.value.collectionMode
            );
        };

        const startNextExperiment = () => {
            if (queuedExperiments.value.length > 0) {
                currentExperiment.value = {
                    ...queuedExperiments.value[0],
                    status: "running",
                    startTime: new Date(),
                    currentTube: 1,
                    collectionMode: "峰驱动",
                    peakCount: 0,
                    currentPressure: 120,
                };
                queuedExperiments.value.shift();
                showPretreatment.value = true;
            }
        };

        const handleSaveExperiment = async (experimentData) => {
            try {
                if (isEditMode.value && editingExperiment.value) {
                    // 编辑模式：更新存在的实验（不包括method_id）
                    const updateData = {
                        experiment_name: experimentData.name,
                        experiment_type: experimentData.type,
                        operator: experimentData.operator,
                        purge_system: experimentData.purgeSystem,
                        purge_column: experimentData.purgeColumn,
                        purge_column_time_min: experimentData.purgeColumnTime,
                        column_balance: experimentData.columnBalance,
                        column_balance_time_min:
                            experimentData.columnBalanceTime,
                        column_conditioning_solution:
                            experimentData.columnConditioningSolution || null,
                        is_peak_driven: experimentData.isPeakDriven,
                        collection_volume_ml: experimentData.collectionVolume,
                        wash_volume_ml: experimentData.washVolume,
                        wash_cycles: experimentData.washCycles,
                        scheduled_start_time:
                            experimentData.scheduledStartTime || null,
                        priority: convertPriorityToNumber(
                            experimentData.priority
                        ),
                        description: experimentData.description,
                        experiment_description:
                            experimentData.experimentDescription || null,
                    };
                    await updateExperiment(
                        editingExperiment.value.experiment_id,
                        updateData
                    );
                    console.log("更新实验成功:", experimentData);
                } else {
                    // 创建模式：创建新实验
                    await createExperiment(experimentData);
                    console.log("创建实验成功:", experimentData);
                }
                showCreateWizard.value = false;
            } catch (error) {
                // 错误已在对应函数中处理
            }
        };

        const handleCloseWizard = (done) => {
            // 重置编辑状态
            isEditMode.value = false;
            editingExperiment.value = null;
            done();
        };

        const handleStartPretreatment = () => {
            console.log("开始预处理");
        };

        const handlePretreatmentComplete = () => {
            showPretreatment.value = false;
            console.log("预处理完成，开始实验");
        };

        const handleSaveExperimentData = (data) => {
            console.log("保存实验数据:", data);
            showEndProcessing.value = false;
            currentExperiment.value = null;
        };

        const handleMergeCollections = (mergeData) => {
            console.log("合并收集:", mergeData);
        };

        const handleCleanTubes = (cleanData) => {
            console.log("清洗试管:", cleanData);
        };

        // 移除了所有前端计时器相关的预处理方法
        // 现在预处理状态完全由MQTT消息驱动

        const terminateExperiment = (experiment) => {
            ElMessageBox.confirm(
                "确定要终止当前实验吗？这将停止所有正在进行的步骤。",
                "终止实验确认",
                {
                    confirmButtonText: "确定终止",
                    cancelButtonText: "取消",
                    type: "warning",
                }
            )
                .then(async () => {
                    try {
                        // 调用后端API终止实验
                        await terminateExperimentAPI(experiment.experiment_id);

                        experiment.status = "terminated";
                        showPretreatmentProgress.value = false;
                        experimentPaused.value = false;

                        // 清除保存的实验数据
                        localStorage.removeItem("currentExperiment");

                        ElMessage.warning("实验已终止");
                        console.log("终止实验:", experiment.experiment_name);
                    } catch (error) {
                        console.error("终止实验失败:", error);
                        ElMessage.error("终止实验失败: " + error.message);
                    }
                })
                .catch(() => {
                    console.log("终止实验操作取消");
                });
        };

        const terminateExperimentAPI = async (experimentId) => {
            const response = await fetch(
                `http://0.0.0.0:8008/api/experiments/data/collection/terminate?experiment_id=${experimentId}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error("终止实验API调用失败");
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || "终止实验失败");
            }

            return result;
        };

        // const goToRealtimeMonitoring = () => {
        //     $router.push("/realtime-monitoring");
        // };

        // 这些旧的函数已被新的MQTT状态显示函数替代

        const getSolutionName = (solutionId) => {
            const solutions = { 1: "A", 2: "B", 3: "C", 4: "D" };
            return solutions[solutionId] || "A";
        };

        // 新增辅助函数用于MQTT状态显示
        const getStepDisplayTitle = () => {
            if (!currentPretreatmentStep.value) {
                return "等待预处理开始...";
            }

            const titleMap = {
                preprocessing_sequence: "预处理序列",
                purge_column: "吹扫柱子",
                purge_system: "吹扫系统",
                column_equilibration: "柱平衡",
            };

            return (
                titleMap[currentPretreatmentStep.value] ||
                currentPretreatmentStep.value
            );
        };

        const getStepDisplayDescription = () => {
            if (!currentPretreatmentStep.value) {
                return "系统正在准备开始预处理步骤";
            }

            const descriptionMap = {
                preprocessing_sequence:
                    preprocessingStatus.value === "started"
                        ? "预处理序列已开始，正在执行各个步骤"
                        : "预处理序列已完成",
                purge_column: "正在清洗色谱柱，移除残留物质",
                purge_system: "正在清洗系统管路，确保系统洁净",
                column_equilibration: `正在用溶液${getSolutionName(
                    selectedExperiment.value?.column_conditioning_solution
                )}平衡色谱柱`,
            };

            return (
                descriptionMap[currentPretreatmentStep.value] ||
                "正在执行预处理步骤"
            );
        };

        const getStatusTagType = () => {
            if (preprocessingStatus.value === "started") return "primary";
            if (preprocessingStatus.value === "completed") return "success";
            return "info";
        };

        const getStatusDisplayText = () => {
            if (preprocessingStatus.value === "started") return "正在运行";
            if (preprocessingStatus.value === "completed") return "已完成";
            return "等待中";
        };

        const getStepItemClass = (stepAction) => {
            if (currentPretreatmentStep.value === stepAction) {
                if (preprocessingStatus.value === "started")
                    return "step-running";
                if (preprocessingStatus.value === "completed")
                    return "step-completed";
            }
            return "step-pending";
        };

        // 添加日期格式化函数
        const formatDate = (dateString) => {
            if (!dateString) return "-";
            return new Date(dateString).toLocaleString("zh-CN");
        };

        // MQTT连接和订阅管理
        const connectMQTT = async () => {
            try {
                await mqttService.connect();
                mqttConnected.value = true;

                // 订阅预处理状态主题
                await mqttService.subscribe(
                    "system/preprocessing_status",
                    handlePreprocessingMessage
                );

                console.log("MQTT连接成功，已订阅预处理状态");
            } catch (error) {
                console.error("MQTT连接失败:", error);
                mqttConnected.value = false;
            }
        };

        const handlePreprocessingMessage = (data) => {
            try {
                console.log("收到预处理状态消息:", data);

                if (
                    !selectedExperiment.value ||
                    data.experiment_id !==
                        selectedExperiment.value.experiment_id
                ) {
                    return; // 不是当前实验的消息
                }

                const { action, status, timestamp } = data;

                // 更新当前预处理步骤和状态
                currentPretreatmentStep.value = action;
                preprocessingStatus.value = status;

                // 根据不同的action和status更新界面
                switch (action) {
                    case "preprocessing_sequence":
                        if (status === "started") {
                            showPretreatmentProgress.value = true;
                            selectedExperiment.value.status = "pretreatment";
                            ElMessage.success("预处理序列开始");
                        } else if (status === "completed") {
                            showPretreatmentProgress.value = false;
                            selectedExperiment.value.status = "running";
                            ElMessage.success("预处理完成，开始正式实验");
                            // 可以选择自动跳转到实时监控
                            setTimeout(() => {
                                $router.push("/realtime-monitoring");
                            }, 2000);
                        }
                        break;

                    case "purge_column":
                        if (status === "started") {
                            ElMessage.info("开始柱子清洗");
                        } else if (status === "completed") {
                            ElMessage.success("柱子清洗完成");
                        }
                        break;

                    case "purge_system":
                        if (status === "started") {
                            ElMessage.info("开始系统清洗");
                        } else if (status === "completed") {
                            ElMessage.success("系统清洗完成");
                        }
                        break;

                    case "column_equilibration":
                        if (status === "started") {
                            ElMessage.info("开始柱平衡");
                        } else if (status === "completed") {
                            ElMessage.success("柱平衡完成");
                        }
                        break;
                }

                // 更新localStorage
                if (selectedExperiment.value) {
                    selectedExperiment.value.currentPretreatmentStep = action;
                    selectedExperiment.value.preprocessingStatus = status;
                    localStorage.setItem(
                        "currentExperiment",
                        JSON.stringify(selectedExperiment.value)
                    );
                }
            } catch (error) {
                console.error("处理预处理消息失败:", error);
            }
        };

        const disconnectMQTT = async () => {
            try {
                await mqttService.unsubscribe("system/preprocessing_status");
                await mqttService.disconnect();
                mqttConnected.value = false;
                console.log("MQTT已断开连接");
            } catch (error) {
                console.error("MQTT断开连接失败:", error);
            }
        };

        // 从后端同步实验状态
        const syncExperimentStatusFromBackend = async (experimentId) => {
            try {
                const response = await fetch(
                    `http://0.0.0.0:8008/api/experiments/data/collection/status?experiment_id=${experimentId}`
                );

                if (!response.ok) {
                    throw new Error("获取实验状态API调用失败");
                }

                const result = await response.json();
                if (!result.success) {
                    throw new Error(result.message || "获取实验状态失败");
                }

                return {
                    status: result.status,
                    currentStep: result.current_step,
                    stepStatus: result.step_status,
                    isPaused: result.is_paused,
                    timestamp: result.timestamp,
                };
            } catch (error) {
                console.error("从后端同步实验状态失败:", error);
                throw error;
            }
        };

        // 同步运行中实验的状态
        const syncRunningExperimentStatus = async () => {
            const savedExperiment = localStorage.getItem("currentExperiment");
            if (!savedExperiment) return;

            try {
                const experiment = JSON.parse(savedExperiment);
                if (!experiment.experiment_id) return;

                // 只同步可能正在运行的实验状态
                if (
                    ["pretreatment", "running", "paused"].includes(
                        experiment.status
                    )
                ) {
                    console.log(
                        "正在同步运行实验状态:",
                        experiment.experiment_id
                    );

                    const backendStatus = await syncExperimentStatusFromBackend(
                        experiment.experiment_id
                    );

                    // 更新localStorage中的实验状态
                    experiment.status = backendStatus.status;
                    experiment.currentPretreatmentStep =
                        backendStatus.currentStep;
                    experiment.preprocessingStatus = backendStatus.stepStatus;
                    experiment.experimentPaused = backendStatus.isPaused;

                    // 更新组件状态
                    if (
                        selectedExperiment.value &&
                        selectedExperiment.value.experiment_id ===
                            experiment.experiment_id
                    ) {
                        selectedExperiment.value.status = backendStatus.status;

                        if (backendStatus.status === "pretreatment") {
                            showPretreatmentProgress.value = true;
                            currentPretreatmentStep.value =
                                backendStatus.currentStep || "";
                            preprocessingStatus.value =
                                backendStatus.stepStatus || "";
                        } else if (backendStatus.status === "running") {
                            showPretreatmentProgress.value = false;
                        }

                        experimentPaused.value = backendStatus.isPaused;
                    }

                    // 保存更新后的状态
                    localStorage.setItem(
                        "currentExperiment",
                        JSON.stringify(experiment)
                    );

                    console.log("实验状态同步成功:", backendStatus);
                }
            } catch (error) {
                console.error("同步运行实验状态失败:", error);
                // 失败时保持localStorage状态，不做额外处理
            }
        };

        // 恢复保存的实验状态
        const restoreExperimentState = () => {
            try {
                const savedExperiment =
                    localStorage.getItem("currentExperiment");
                if (savedExperiment) {
                    const experiment = JSON.parse(savedExperiment);

                    // 恢复选中的实验
                    selectedExperiment.value = experiment;

                    // 检查实验状态
                    if (experiment.status === "pretreatment") {
                        // 恢复预处理进度状态
                        showPretreatmentProgress.value = true;

                        // 恢复当前步骤位置和状态
                        if (experiment.currentPretreatmentStep) {
                            currentPretreatmentStep.value =
                                experiment.currentPretreatmentStep;
                        }
                        if (experiment.preprocessingStatus) {
                            preprocessingStatus.value =
                                experiment.preprocessingStatus;
                        }

                        // 检查是否在暂停状态
                        if (experiment.experimentPaused) {
                            experimentPaused.value = true;
                        }

                        console.log(
                            "恢复预处理状态实验:",
                            experiment.experiment_name
                        );
                    } else if (
                        ["running", "paused"].includes(experiment.status)
                    ) {
                        // 如果是运行或暂停状态，也需要恢复相关状态
                        if (experiment.status === "paused") {
                            experimentPaused.value = true;
                        }
                        console.log(
                            "恢复运行状态实验:",
                            experiment.experiment_name
                        );
                    }
                }
            } catch (error) {
                console.error("恢复实验状态失败:", error);
                // 清除可能损坏的localStorage数据
                localStorage.removeItem("currentExperiment");
            }
        };

        // 组件挂载时获取数据并恢复状态
        onMounted(async () => {
            // 1. 首先获取所有实验数据
            await fetchAllExperiments();

            // 2. 恢复localStorage中的状态
            restoreExperimentState();

            // 3. 同步后端的实时状态（覆盖localStorage状态）
            await syncRunningExperimentStatus();

            // 4. 如果有currentExperiment，获取实验步骤
            if (
                currentExperiment.value &&
                currentExperiment.value.experiment_id
            ) {
                try {
                    await fetchExperimentSteps(
                        currentExperiment.value.experiment_id
                    );
                    console.log(
                        "页面刷新时自动获取实验步骤:",
                        currentExperiment.value.experiment_id
                    );
                } catch (error) {
                    console.error("获取实验步骤失败:", error);
                }
            }

            // 5. 最后连接MQTT进行实时更新
            await connectMQTT();
        });

        // 组件卸载时断开MQTT连接
        onUnmounted(async () => {
            await disconnectMQTT();
        });

        return {
            showCreateWizard,
            showPretreatment,
            showEndProcessing,
            selectedTube,
            isWasteMode,
            selectedExperiment,
            currentExperiment,
            queuedExperiments,
            allExperiments,
            paginatedExperiments,
            quickMethods,
            // 分页相关
            currentPage,
            pageSize,
            totalExperiments,
            availableTubes,
            loading,
            isEditMode,
            editingExperiment,
            // 预处理相关状态
            showPretreatmentProgress,
            currentPretreatmentStep,
            preprocessingStatus,
            experimentPaused,
            mqttConnected,
            currentProgress,
            progressStatus,
            elapsedTime,
            remainingTime,
            getStatusType,
            getStatusText,
            getPressureClass,
            getExperimentStatusType,
            getExperimentStatusText,
            selectExperiment,
            experimentSteps,
            currentStepIndex,
            getStepDisplayName,
            getExperimentProgress,
            getElapsedTime,
            getRemainingTime,
            createQuickExperiment,
            clearQueue,
            editQueuedExperiment,
            moveUp,
            moveDown,
            removeFromQueue,
            startExperiment,
            pauseExperiment,
            resumeExperiment,
            stopExperiment,
            switchTube,
            switchCollectionMode,
            startNextExperiment,
            handleSaveExperiment,
            handleCloseWizard,
            handleStartPretreatment,
            handlePretreatmentComplete,
            handleSaveExperimentData,
            handleMergeCollections,
            handleCleanTubes,
            fetchAllExperiments,
            createExperiment,
            updateExperiment,
            deleteExperiment,
            // 新的MQTT相关方法
            terminateExperiment,
            getSolutionName,
            getStepDisplayTitle,
            getStepDisplayDescription,
            getStatusTagType,
            getStatusDisplayText,
            getStepItemClass,
            formatDate,
            restoreExperimentState,
            syncExperimentStatusFromBackend,
            syncRunningExperimentStatus,
            connectMQTT,
            disconnectMQTT,
            // 分页相关函数
            updatePaginatedExperiments,
            handlePageChange,
            handlePageSizeChange,
        };
    },
};
</script>

<style scoped>
.experiment-management {
    padding: 20px;
}

.status-overview {
    margin-bottom: 20px;
}

.status-card {
    height: 100px;
}

.status-item {
    display: flex;
    align-items: center;
    height: 100%;
}

.status-icon {
    font-size: 32px;
    margin-right: 16px;
}

.status-icon.running {
    color: #67c23a;
}

.status-icon.pending {
    color: #e6a23c;
}

.status-icon.progress {
    color: #409eff;
}

.status-icon.time {
    color: #909399;
}

.status-info h3 {
    margin: 0 0 4px 0;
    font-size: 14px;
    color: #666;
}

.status-info p {
    margin: 0;
    font-size: 18px;
    font-weight: bold;
    color: #333;
}

.mb-3 {
    margin-bottom: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-buttons {
    display: flex;
    gap: 8px;
}

.pagination-container {
    margin-top: 16px;
    padding: 16px 0;
    display: flex;
    justify-content: center;
    border-top: 1px solid #ebeef5;
}

.experiment-queue {
    min-height: 200px;
}

.empty-queue {
    padding: 40px 0;
}

.queue-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border: 1px solid #ebeef5;
    border-radius: 6px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
}

.queue-item:hover {
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.queue-item.queue-active {
    border-color: #409eff;
    background-color: #f0f9ff;
}

.queue-item.selected {
    border-color: #67c23a;
    background-color: #f0f9ff;
    box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

.queue-item {
    cursor: pointer;
}

.queue-info h4 {
    margin: 0 0 4px 0;
    color: #333;
}

.queue-info p {
    margin: 2px 0;
    font-size: 14px;
    color: #666;
}

.queue-actions {
    display: flex;
    gap: 4px;
}

.experiment-control {
    padding: 16px;
}

.experiment-info {
    margin-bottom: 20px;
}

.experiment-info h3 {
    margin: 0 0 8px 0;
    color: #333;
}

.experiment-info p {
    margin: 4px 0;
    color: #666;
}

.progress-section {
    margin-bottom: 20px;
}

.time-info {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 14px;
    color: #666;
}

.current-status {
    margin-bottom: 20px;
    padding: 16px;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.status-item-small {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.status-item-small label {
    font-size: 14px;
    color: #666;
}

.status-value {
    font-weight: bold;
    color: #333;
}

.status-value.pressure.normal {
    color: #67c23a;
}

.status-value.pressure.warning {
    color: #e6a23c;
}

.status-value.pressure.danger {
    color: #f56c6c;
}

.control-buttons {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.control-buttons .el-button {
    flex: 1;
}

.realtime-controls {
    margin-top: 16px;
}

.control-group {
    margin-bottom: 12px;
}

.control-group label {
    display: block;
    margin-bottom: 4px;
    font-size: 14px;
    color: #666;
}

.control-group .el-select {
    width: 120px;
    margin-right: 8px;
}

.no-experiment {
    padding: 40px 0;
    text-align: center;
}

.experiment-monitor {
    padding: 16px;
}

.experiment-params {
    margin-bottom: 20px;
}

.param-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.param-item label {
    font-size: 14px;
    color: #666;
}

.param-item span {
    font-weight: bold;
    color: #333;
}

.running-status {
    margin-top: 20px;
}

.no-selection {
    padding: 40px 0;
    text-align: center;
}

/* 预处理步骤样式 */
.pretreatment-progress {
    margin: 20px 0;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
}

.pretreatment-progress .el-steps {
    margin-bottom: 20px;
}

.current-step-info {
    margin-top: 16px;
}

.step-card {
    background: white;
    border: 1px solid #e4e7ed;
}

.step-details h4 {
    margin: 0 0 8px 0;
    color: #303133;
    font-size: 16px;
}

.step-details p {
    margin: 0 0 12px 0;
    color: #606266;
    font-size: 14px;
}

.step-timer {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    color: #409eff;
    font-weight: 500;
}

.step-timer .el-icon {
    margin-right: 6px;
}

.control-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}

.control-buttons .el-button {
    flex: 1;
    min-width: 100px;
}

/* MQTT状态相关样式 */
.mqtt-status {
    margin-bottom: 16px;
    text-align: center;
}

.current-step-display {
    margin-top: 16px;
}

.step-details h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 12px 0;
    color: #303133;
    font-size: 16px;
}

.running-icon {
    color: #409eff;
    animation: spin 1s linear infinite;
}

.completed-icon {
    color: #67c23a;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

.status-indicator {
    margin: 12px 0;
    text-align: center;
}

.step-checklist {
    margin-top: 16px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
}

.step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    margin-bottom: 4px;
    border-radius: 4px;
    transition: all 0.3s ease;
}

.step-item.step-pending {
    color: #909399;
}

.step-item.step-running {
    background: #e6f7ff;
    color: #409eff;
    border-left: 3px solid #409eff;
}

.step-item.step-completed {
    background: #f6ffed;
    color: #67c23a;
    border-left: 3px solid #67c23a;
}

.step-item .el-icon {
    font-size: 16px;
}

@media (max-width: 768px) {
    .control-buttons {
        flex-direction: column;
    }

    .control-buttons .el-button {
        width: 100%;
    }

    .pretreatment-progress .el-steps {
        font-size: 12px;
    }

    .step-checklist {
        font-size: 14px;
    }
}

/* 实验步骤流程图样式 */
.experiment-steps-flowchart {
    margin: 20px 0;
    padding: 0px;
    background: #f8f9fa;
    border-radius: 0px;
    border: 0px solid #e9ecef;
}

.flowchart-title {
    margin: 0 0 15px 0;
    color: #333;
    font-size: 16px;
    font-weight: 600;
}

.steps-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    overflow-x: auto;
    padding: 0px 0;
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    min-width: 100px;
    flex: 1;
}

.step-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e9ecef;
    color: #6c757d;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

.step-item.completed .step-icon {
    background: #28a745;
    color: white;
}

.step-item.active .step-icon {
    background: #007bff;
    color: white;
    animation: pulse 2s infinite;
}

.step-label {
    font-size: 12px;
    text-align: center;
    color: #6c757d;
    margin-bottom: 10px;
    line-height: 1.2;
}

.step-item.active .step-label {
    color: #007bff;
    font-weight: 600;
}

.step-item.completed .step-label {
    color: #28a745;
    font-weight: 600;
}

.step-connector {
    position: absolute;
    top: 20px;
    right: -60px;
    width: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.connector-line {
    flex: 1;
    height: 2px;
    background: #e9ecef;
    transition: all 0.3s ease;
}

.connector-line.active {
    background: #28a745;
}

.connector-arrow {
    color: #6c757d;
    margin-left: 5px;
    font-size: 14px;
}

@keyframes pulse {
    0%,
    100% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.4);
    }
    50% {
        transform: scale(1.05);
        box-shadow: 0 0 0 10px rgba(0, 123, 255, 0);
    }
}

/* 响应式调整 */
@media (max-width: 768px) {
    .steps-container {
        flex-wrap: wrap;
        gap: 20px;
    }

    .step-item {
        min-width: 80px;
    }

    .step-connector {
        display: none;
    }
}
</style>
