<template>
    <div class="realtime-monitoring fade-in">
        <!-- 顶部控制面板 -->
        <div class="monitoring-header glass-effect">
            <h2 class="gradient-text">实时监控</h2>
            <div class="status-indicators">
                <div class="status-item">
                    <span class="status-indicator online"></span>
                    <span class="status-text">系统运行中</span>
                </div>
                <div class="status-item">
                    <span class="status-indicator"
                        :class="getExperimentStepIndicatorClass()"></span>
                    <span class="status-text">{{ getExperimentStepDisplayText() }}</span>
                </div>
                <div class="status-item">
                    <span
                        class="status-indicator"
                        :class="isPaused ? 'offline' : 'online'"
                    ></span>
                    <span class="status-text">{{
                        isPaused ? "待机" : "采集中"
                    }}</span>
                </div>
                <div class="status-item peak-info">
                    <span class="peak-stat-inline">
                        <span class="stat-label">检测峰数:</span>
                        <span class="stat-value">{{
                            detectedPeaks.length
                        }}</span>
                    </span>
                    <span class="peak-stat-inline">
                        <span class="stat-label">基线:</span>
                        <span class="stat-value">{{
                            currentBaseline.toFixed(2)
                        }}</span>
                    </span>
                    <span class="peak-stat-inline">
                        <el-tag
                            :type="
                                peakDetectionStatus === 'active'
                                    ? 'success'
                                    : 'info'
                            "
                            size="small"
                        >
                            {{
                                peakDetectionStatus === "active"
                                    ? "检测中"
                                    : "待机"
                            }}
                        </el-tag>
                    </span>
                </div>
                <div class="status-item">
                    <el-button
                        type="text"
                        size="small"
                        @click="showPeakDialog = true"
                        class="view-details-btn"
                    >
                        查看详情
                    </el-button>
                </div>
            </div>
        </div>

        <el-row :gutter="20" class="main-content">
            <!-- 左侧：实时图表区域 -->
            <el-col :span="19">
                <!-- 实时色谱图 -->
                <div
                    class="data-card chart-container-card"
                    :class="{ 'expanded-chart': !isFractionCollectorExpanded }"
                >
                    <div class="data-card-header">
                        <h3 class="data-card-title">实时色谱图</h3>
                        <div class="chart-toolbar-inline">
                            <div class="time-range">
                                <label>时间范围: </label>
                                <el-select
                                    v-model="timeRange"
                                    @change="updateTimeRange"
                                    size="small"
                                    style="min-width: 120px"
                                >
                                    <el-option label="最近5分钟" value="5" />
                                    <el-option label="最近10分钟" value="10" />
                                    <el-option label="最近30分钟" value="30" />
                                    <el-option label="完整运行" value="all" />
                                </el-select>
                            </div>
                            <div class="detector-controls">
                                <el-button-group size="small">
                                    <el-button
                                        v-for="detector in detectors"
                                        :key="detector.name"
                                        :type="detector.active ? 'primary' : ''"
                                        @click="switchDetector(detector.name)"
                                    >
                                        {{ detector.name }}
                                    </el-button>
                                </el-button-group>
                            </div>
                            <div class="chart-controls">
                                <el-button-group size="small">
                                    <el-button @click="resetZoom" icon="ZoomOut"
                                        >重置缩放</el-button
                                    >
                                    <el-button
                                        @click="exportChart"
                                        icon="Download"
                                        >导出</el-button
                                    >
                                </el-button-group>
                            </div>
                        </div>
                    </div>

                    <div class="chart-container">
                        <!-- 图表图例 -->
                        <div class="chart-legend">
                            <div class="legend-checkboxes">
                                <el-checkbox
                                    v-for="series in chartSeries"
                                    :key="series.key"
                                    v-model="series.visible"
                                    @change="toggleSeries(series.key)"
                                    class="legend-checkbox"
                                >
                                    <span
                                        class="legend-color"
                                        :class="series.key"
                                    ></span>
                                    <span class="legend-text">
                                        <template v-if="series.key === 'uv254'">
                                            <span class="legend-label"
                                                >UV{{ wavelengths.uv1 }}:</span
                                            >
                                            <span class="legend-value">{{
                                                currentValues.uv254.toFixed(5)
                                            }}</span>
                                        </template>
                                        <template
                                            v-else-if="series.key === 'uv280'"
                                        >
                                            <span class="legend-label"
                                                >UV{{ wavelengths.uv2 }}:</span
                                            >
                                            <span class="legend-value">{{
                                                currentValues.uv280.toFixed(5)
                                            }}</span>
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-a'
                                            "
                                        >
                                            <span class="legend-label"
                                                >{{ series.label }}:</span
                                            >
                                            <span class="legend-value"
                                                >{{
                                                    gradientValues?.solutionA ||
                                                    0
                                                }}%</span
                                            >
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-b'
                                            "
                                        >
                                            <span class="legend-label"
                                                >{{ series.label }}:</span
                                            >
                                            <span class="legend-value"
                                                >{{
                                                    gradientValues?.solutionB ||
                                                    0
                                                }}%</span
                                            >
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-c'
                                            "
                                        >
                                            <span class="legend-label"
                                                >{{ series.label }}:</span
                                            >
                                            <span class="legend-value"
                                                >{{
                                                    gradientValues?.solutionC ||
                                                    0
                                                }}%</span
                                            >
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-d'
                                            "
                                        >
                                            <span class="legend-label"
                                                >{{ series.label }}:</span
                                            >
                                            <span class="legend-value"
                                                >{{
                                                    gradientValues?.solutionD ||
                                                    0
                                                }}%</span
                                            >
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'pressure'
                                            "
                                        >
                                            <span class="legend-label"
                                                >{{ series.label }}:</span
                                            >
                                            <span class="legend-value">{{
                                                currentValues.pressure.toFixed(
                                                    0
                                                )
                                            }}</span>
                                        </template>
                                        <template v-else>
                                            <span class="legend-label">{{
                                                series.label
                                            }}</span>
                                        </template>
                                    </span>
                                </el-checkbox>
                            </div>
                        </div>

                        <!-- 实时图表区域 -->
                        <div class="chart-area" ref="chartContainer">
                            <svg ref="d3Chart" class="chromatogram-chart"></svg>
                        </div>
                    </div>

                    <!-- 馏分收集器可折叠面板 -->
                    <div class="data-card tube-rack-card">
                        <!-- 可折叠的内容区域 - 向上展开 -->
                        <div
                            class="fraction-collector-content"
                            :class="{ expanded: isFractionCollectorExpanded }"
                        >
                            <!-- 操作按钮区域 -->
                            <div class="rack-actions-panel">
                                <div class="rack-actions">
                                    <el-button
                                        type="primary"
                                        size="small"
                                        @click.stop="reverseTubes"
                                        icon="Sort"
                                    >
                                        反转
                                    </el-button>
                                    <el-button
                                        type="success"
                                        size="small"
                                        @click.stop="mergeTubes"
                                        icon="Merge"
                                    >
                                        合并
                                    </el-button>
                                    <el-button
                                        type="warning"
                                        size="small"
                                        @click.stop="cleanTubes"
                                        icon="Brush"
                                    >
                                        清洗
                                    </el-button>
                                </div>
                            </div>

                            <!-- 试管架区域 -->
                            <div class="tube-rack">
                                <div class="rack-grid">
                                    <div
                                        v-for="tube in tubes"
                                        :key="tube.id"
                                        class="tube-slot"
                                        :class="getTubeClass(tube)"
                                        @click.stop="selectTube(tube)"
                                        :title="getTubeTooltip(tube)"
                                    >
                                        <span class="tube-number">{{
                                            tube.id
                                        }}</span>
                                        <div
                                            v-if="tube.status !== 'empty'"
                                            class="tube-fill"
                                            :style="{
                                                height: `${tube.fillLevel}%`,
                                            }"
                                        ></div>
                                    </div>
                                </div>

                                <!-- 试管状态说明 -->
                                <div class="tube-legend">
                                    <div class="legend-item">
                                        <span class="tube-sample empty"></span>
                                        <span>空闲</span>
                                    </div>
                                    <div class="legend-item">
                                        <span class="tube-sample ready"></span>
                                        <span>准备</span>
                                    </div>
                                    <div class="legend-item">
                                        <span
                                            class="tube-sample collecting"
                                        ></span>
                                        <span>收集中</span>
                                    </div>
                                    <div class="legend-item">
                                        <span
                                            class="tube-sample completed"
                                        ></span>
                                        <span>已完成</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 可点击的头部区域 - 固定在底部 -->
                        <div
                            class="fraction-collector-header"
                            @click="toggleFractionCollector"
                        >
                            <div class="header-left">
                                <h3 class="data-card-title">馏分收集器</h3>
                                <div class="basic-stats">
                                    <span class="basic-stat"
                                        >当前：{{ currentTube }}</span
                                    >
                                    <span class="basic-stat"
                                        >{{ completedTubes }}已收集</span
                                    >
                                    <span class="basic-stat"
                                        >模式：{{ collectionMode }}</span
                                    >
                                </div>
                            </div>
                            <div class="header-right">
                                <el-icon
                                    class="expand-icon"
                                    :class="{
                                        expanded: isFractionCollectorExpanded,
                                    }"
                                >
                                    <ArrowDown />
                                </el-icon>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 合并任务管理弹窗 -->
                <el-dialog
                    v-model="showMergeTaskDialog"
                    title="合并任务管理"
                    width="80%"
                    :before-close="closeMergeTaskDialog"
                    class="merge-task-dialog"
                >
                    <div class="merge-task-content">
                        <!-- 已选择的试管信息 -->
                        <div
                            class="selected-tubes-info"
                            v-if="selectedTubesCount > 0"
                        >
                            <h4>已选择的试管</h4>
                            <div class="selected-tubes-list">
                                <el-tag
                                    v-for="tubeId in selectedTubesArray"
                                    :key="tubeId"
                                    type="warning"
                                    class="selected-tube-tag"
                                >
                                    试管 {{ tubeId }}
                                </el-tag>
                            </div>
                        </div>

                        <el-divider />

                        <!-- 任务列表 -->
                        <div class="task-list-section">
                            <div class="task-list-header">
                                <h4>任务列表</h4>
                                <div class="batch-controls">
                                    <el-button
                                        type="success"
                                        size="small"
                                        @click="batchStart"
                                        :disabled="selectedTaskIds.length === 0"
                                        icon="VideoPlay"
                                    >
                                        批量开始
                                    </el-button>
                                    <el-button
                                        type="warning"
                                        size="small"
                                        @click="batchPause"
                                        :disabled="selectedTaskIds.length === 0"
                                        icon="VideoPause"
                                    >
                                        批量暂停
                                    </el-button>
                                    <el-button
                                        type="primary"
                                        size="small"
                                        @click="batchResume"
                                        :disabled="selectedTaskIds.length === 0"
                                        icon="VideoPlay"
                                    >
                                        批量继续
                                    </el-button>
                                    <el-button
                                        type="danger"
                                        size="small"
                                        @click="batchTerminate"
                                        :disabled="selectedTaskIds.length === 0"
                                        icon="Close"
                                    >
                                        批量终止
                                    </el-button>
                                </div>
                            </div>

                            <el-table
                                :data="mergeTasks"
                                style="width: 100%"
                                @selection-change="handleTaskSelectionChange"
                                v-loading="false"
                            >
                                <el-table-column type="selection" width="55" />
                                <el-table-column
                                    prop="id"
                                    label="任务ID"
                                    width="100"
                                    align="center"
                                />
                                <el-table-column
                                    label="试管编号"
                                    width="200"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <span class="tube-ids">
                                            [{{ scope.row.tubeIds.join(", ") }}]
                                        </span>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="type"
                                    label="类型"
                                    width="80"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <el-tag type="info" size="small">
                                            {{ scope.row.type }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="status"
                                    label="状态"
                                    width="100"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <el-tag
                                            :type="
                                                getTaskStatusType(
                                                    scope.row.status
                                                )
                                            "
                                            size="small"
                                        >
                                            {{
                                                getTaskStatusText(
                                                    scope.row.status
                                                )
                                            }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="progress"
                                    label="进度"
                                    width="120"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <el-progress
                                            :percentage="scope.row.progress"
                                            :stroke-width="8"
                                            :show-text="false"
                                            :color="
                                                getProgressColor(
                                                    scope.row.status
                                                )
                                            "
                                        />
                                        <span class="progress-text"
                                            >{{ scope.row.progress }}%</span
                                        >
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="createdAt"
                                    label="创建时间"
                                    width="150"
                                    align="center"
                                />
                                <el-table-column
                                    label="操作"
                                    min-width="200"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <div class="task-actions">
                                            <el-button
                                                v-if="
                                                    scope.row.status ===
                                                        'pending' ||
                                                    scope.row.status ===
                                                        'paused'
                                                "
                                                type="success"
                                                size="small"
                                                @click="startTask(scope.row.id)"
                                                icon="VideoPlay"
                                            >
                                                开始
                                            </el-button>
                                            <el-button
                                                v-if="
                                                    scope.row.status ===
                                                    'running'
                                                "
                                                type="warning"
                                                size="small"
                                                @click="pauseTask(scope.row.id)"
                                                icon="VideoPause"
                                            >
                                                暂停
                                            </el-button>
                                            <el-button
                                                v-if="
                                                    scope.row.status ===
                                                    'paused'
                                                "
                                                type="primary"
                                                size="small"
                                                @click="
                                                    resumeTask(scope.row.id)
                                                "
                                                icon="VideoPlay"
                                            >
                                                继续
                                            </el-button>
                                            <el-button
                                                v-if="
                                                    scope.row.status !==
                                                        'terminated' &&
                                                    scope.row.status !==
                                                        'completed'
                                                "
                                                type="danger"
                                                size="small"
                                                @click="
                                                    terminateTask(scope.row.id)
                                                "
                                                icon="Close"
                                            >
                                                终止
                                            </el-button>
                                            <el-button
                                                type="info"
                                                size="small"
                                                @click="
                                                    deleteTask(scope.row.id)
                                                "
                                                icon="Delete"
                                            >
                                                删除
                                            </el-button>
                                        </div>
                                    </template>
                                </el-table-column>
                            </el-table>

                            <div
                                class="task-summary"
                                v-if="mergeTasks.length === 0"
                            >
                                <el-empty description="暂无任务" />
                            </div>
                        </div>
                    </div>

                    <template #footer>
                        <div class="dialog-footer">
                            <el-button @click="clearSelection" type="info">
                                清空选择
                            </el-button>
                            <el-button
                                @click="closeMergeTaskDialog"
                                type="primary"
                            >
                                关闭
                            </el-button>
                        </div>
                    </template>
                </el-dialog>
            </el-col>

            <!-- 右侧：控制面板和峰信息 -->
            <el-col :span="5">
                <!-- 大按钮控制面板 -->
                <div class="data-card control-buttons-card">
                    <div class="data-card-header">
                        <h3 class="data-card-title">实时控制</h3>
                    </div>
                    <div class="control-buttons-grid">
                        <!-- 开始/暂停/继续按钮 -->
                        <el-button
                            v-if="!isRunning"
                            type="primary"
                            size="large"
                            class="control-btn control-btn-primary"
                            style="margin-left: 12px"
                            @click="togglePause"
                        >
                            <el-icon class="btn-icon"><VideoPlay /></el-icon>
                            <span class="btn-text">{{ getStartButtonText() }}</span>
                        </el-button>
                        <el-button
                            v-else-if="isRunning && !isPaused"
                            type="warning"
                            size="large"
                            class="control-btn control-btn-warning"
                            style="margin-left: 12px"
                            @click="togglePause"
                        >
                            <el-icon class="btn-icon"><VideoPause /></el-icon>
                            <span class="btn-text">暂停</span>
                        </el-button>
                        <el-button
                            v-else-if="isRunning && isPaused"
                            type="success"
                            size="large"
                            class="control-btn control-btn-success"
                            style="margin-left: 12px"
                            @click="togglePause"
                        >
                            <el-icon class="btn-icon"><VideoPlay /></el-icon>
                            <span class="btn-text">继续</span>
                        </el-button>

                        <!-- 终止按钮 -->
                        <el-button
                            type="danger"
                            size="large"
                            class="control-btn control-btn-danger"
                            @click="emergencyStop"
                        >
                            <el-icon class="btn-icon"><CircleClose /></el-icon>
                            <span class="btn-text">终止</span>
                        </el-button>

                        <!-- 清空按钮 -->
                        <el-button
                            type="warning"
                            size="large"
                            class="control-btn control-btn-clear"
                            @click="clearChartData"
                            plain
                        >
                            <el-icon class="btn-icon"><Delete /></el-icon>
                            <span class="btn-text">清空</span>
                        </el-button>

                        <!-- 手动保持按钮 -->
                        <el-button
                            type="info"
                            size="large"
                            class="control-btn control-btn-info"
                            @click="toggleManualHold"
                            :class="{ 'is-active': isManualHold }"
                        >
                            <el-icon class="btn-icon"><Lock /></el-icon>
                            <span class="btn-text">{{
                                isManualHold ? "取消保持" : "手动保持"
                            }}</span>
                        </el-button>

                        <!-- 修改洗脱液比例按钮 -->
                        <el-button
                            type="primary"
                            size="large"
                            class="control-btn control-btn-gradient"
                            @click="openGradientDialog"
                            plain
                        >
                            <el-icon class="btn-icon"><Setting /></el-icon>
                            <span class="btn-text">洗脱液比例</span>
                        </el-button>

                        <!-- 收集模式切换按钮 -->
                        <el-button
                            size="large"
                            class="control-btn control-btn-mode"
                            :type="
                                collectionMode === '收集'
                                    ? 'success'
                                    : 'warning'
                            "
                            @click="toggleCollectionMode"
                        >
                            <el-icon class="btn-icon">
                                <component
                                    :is="
                                        collectionMode === '收集'
                                            ? 'CollectionTag'
                                            : 'Delete'
                                    "
                                />
                            </el-icon>
                            <span class="btn-text"
                                >{{ collectionMode }}模式</span
                            >
                        </el-button>

                        <!-- 切换试管按钮 -->
                        <el-button
                            type="primary"
                            size="large"
                            class="control-btn control-btn-tube"
                            @click="openTubeSwitchDialog"
                            plain
                        >
                            <el-icon class="btn-icon"><Grid /></el-icon>
                            <span class="btn-text">切换试管</span>
                        </el-button>

                        <!-- 润柱按钮 -->
                        <el-button
                            type="primary"
                            size="large"
                            class="control-btn control-btn-conditioning"
                            @click="openColumnConditioningDialog"
                            plain
                        >
                            <el-icon class="btn-icon"><Refresh /></el-icon>
                            <span class="btn-text">润柱</span>
                        </el-button>

                        <!-- Mock模式按钮 -->
                        <el-button
                            type="info"
                            size="large"
                            class="control-btn control-btn-mock"
                            @click="openMockModeDialog"
                            plain
                        >
                            <el-icon class="btn-icon"><Tools /></el-icon>
                            <span class="btn-text">Mock模式</span>
                        </el-button>
                    </div>
                </div>

                <!-- 峰检测详情弹窗 -->
                <el-dialog
                    v-model="showPeakDialog"
                    title="峰检测详情"
                    width="80%"
                    :before-close="closePeakDialog"
                >
                    <div class="peak-dialog-content">
                        <div class="peak-summary">
                            <div class="summary-card">
                                <div class="summary-icon">📊</div>
                                <div class="summary-content">
                                    <div class="summary-value">
                                        {{ detectedPeaks.length }}
                                    </div>
                                    <div class="summary-label">已检测峰数</div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">📏</div>
                                <div class="summary-content">
                                    <div class="summary-value">
                                        {{ currentBaseline.toFixed(3) }}
                                    </div>
                                    <div class="summary-label">
                                        当前基线 (AU)
                                    </div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">🔊</div>
                                <div class="summary-content">
                                    <div class="summary-value">
                                        {{ noiseLevel.toFixed(3) }}
                                    </div>
                                    <div class="summary-label">
                                        噪声水平 (AU)
                                    </div>
                                </div>
                            </div>
                        </div>

                        <el-divider />

                        <div class="peak-table-container">
                            <el-table
                                :data="detectedPeaks"
                                style="width: 100%"
                                size="small"
                            >
                                <el-table-column
                                    prop="id"
                                    label="峰编号"
                                    width="80"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <span class="peak-number"
                                            >峰 {{ scope.row.id }}</span
                                        >
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="retentionTime"
                                    label="保留时间 (min)"
                                    width="120"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <span>{{
                                            scope.row.retentionTime.toFixed(2)
                                        }}</span>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="height"
                                    label="峰高 (AU)"
                                    width="100"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <span>{{
                                            scope.row.height.toFixed(3)
                                        }}</span>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="tubeId"
                                    label="试管编号"
                                    width="80"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <span>{{ scope.row.tubeId }}</span>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="status"
                                    label="状态"
                                    width="100"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <el-tag
                                            :type="
                                                getPeakStatusType(
                                                    scope.row.status
                                                )
                                            "
                                            size="small"
                                        >
                                            {{
                                                getPeakStatusText(
                                                    scope.row.status
                                                )
                                            }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    label="操作"
                                    width="120"
                                    align="center"
                                >
                                    <template #default="scope">
                                        <el-button
                                            type="text"
                                            size="small"
                                            @click="locatePeak(scope.row)"
                                        >
                                            定位
                                        </el-button>
                                        <el-button
                                            type="text"
                                            size="small"
                                            @click="exportPeak(scope.row)"
                                        >
                                            导出
                                        </el-button>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </div>
                    </div>

                    <template #footer>
                        <div class="dialog-footer">
                            <el-button @click="exportAllPeaks" type="primary"
                                >导出全部</el-button
                            >
                            <el-button @click="showPeakDialog = false"
                                >关闭</el-button
                            >
                        </div>
                    </template>
                </el-dialog>

                <!-- 洗脱液比例调整弹窗 -->
                <el-dialog
                    v-model="showGradientDialog"
                    title="调整洗脱液比例"
                    width="500px"
                >
                    <div class="gradient-dialog-content">
                        <div class="gradient-item">
                            <label>执行时间:</label>
                            <el-select
                                v-model="selectedGradientTime"
                                placeholder="选择时间"
                                style="width: 200px"
                            >
                                <el-option
                                    v-for="time in availableGradientTimes"
                                    :key="time.value"
                                    :label="time.label"
                                    :value="time.value"
                                />
                            </el-select>
                        </div>
                        <div class="gradient-item">
                            <label>原液A:</label>
                            <el-slider
                                v-model="gradientValues.solutionA"
                                :max="100"
                                style="flex: 1; margin: 0 15px"
                            />
                            <span class="gradient-value"
                                >{{ gradientValues.solutionA }}%</span
                            >
                        </div>
                        <div class="gradient-item">
                            <label>原液B:</label>
                            <el-slider
                                v-model="gradientValues.solutionB"
                                :max="100"
                                style="flex: 1; margin: 0 15px"
                            />
                            <span class="gradient-value"
                                >{{ gradientValues.solutionB }}%</span
                            >
                        </div>
                        <div class="gradient-item">
                            <label>原液C:</label>
                            <el-slider
                                v-model="gradientValues.solutionC"
                                :max="100"
                                style="flex: 1; margin: 0 15px"
                            />
                            <span class="gradient-value"
                                >{{ gradientValues.solutionC }}%</span
                            >
                        </div>
                        <div class="gradient-item">
                            <label>原液D:</label>
                            <el-slider
                                v-model="gradientValues.solutionD"
                                :max="100"
                                style="flex: 1; margin: 0 15px"
                            />
                            <span class="gradient-value"
                                >{{ gradientValues.solutionD }}%</span
                            >
                        </div>
                    </div>
                    <template #footer>
                        <div class="dialog-footer">
                            <el-button @click="cancelGradientChange"
                                >取消</el-button
                            >
                            <el-button
                                type="primary"
                                @click="applyGradientChangeWrapper"
                            >
                                应用更改 {{ selectedGradientTime ? "✓" : "❌" }}
                            </el-button>
                        </div>
                    </template>
                </el-dialog>

                <!-- 切换试管弹窗 -->
                <el-dialog
                    v-model="showTubeDialog"
                    title="切换试管"
                    width="400px"
                >
                    <div class="tube-dialog-content">
                        <div class="current-tube-info">
                            <p>
                                当前试管：<strong
                                    >试管 {{ currentTube }}</strong
                                >
                            </p>
                        </div>
                        <el-divider />
                        <div class="tube-selection">
                            <label>选择试管：</label>
                            <el-select
                                v-model="selectedTubeForSwitch"
                                placeholder="选择试管"
                                style="width: 200px"
                            >
                                <el-option
                                    v-for="tube in availableTubes"
                                    :key="tube"
                                    :label="`试管 ${tube}`"
                                    :value="tube"
                                />
                            </el-select>
                        </div>
                    </div>
                    <template #footer>
                        <div class="dialog-footer">
                            <el-button @click="showTubeDialog = false"
                                >取消</el-button
                            >
                            <el-button
                                type="primary"
                                @click="switchToTubeWrapper"
                                :disabled="
                                    !selectedTubeForSwitch ||
                                    selectedTubeForSwitch === currentTube
                                "
                            >
                                切换
                            </el-button>
                        </div>
                    </template>
                </el-dialog>

                <!-- 润柱弹窗 -->
                <el-dialog
                    v-model="showColumnConditioningDialog"
                    title="润柱设置"
                    width="400px"
                >
                    <div class="conditioning-dialog-content">
                        <div class="conditioning-info">
                            <el-alert
                                title="润柱说明"
                                type="info"
                                description="润柱过程将清洗色谱柱并平衡系统，建议在实验前或长期停机后进行。"
                                show-icon
                                :closable="false"
                            />
                        </div>

                        <el-divider />

                        <div class="conditioning-settings">
                            <el-form label-width="100px">
                                <el-form-item label="润柱时间">
                                    <el-input-number
                                        v-model="conditioningTime"
                                        :min="1"
                                        :max="60"
                                        placeholder="请输入润柱时间"
                                        style="width: 200px"
                                    />
                                    <span style="margin-left: 10px; color: #666;">分钟</span>
                                </el-form-item>

                                <el-form-item label="润柱溶液">
                                    <el-select
                                        v-model="conditioningSolution"
                                        placeholder="选择润柱溶液"
                                        style="width: 200px"
                                    >
                                        <el-option label="溶液A (100%)" value="A" />
                                        <el-option label="溶液B (100%)" value="B" />
                                        <el-option label="溶液A/B (50:50)" value="AB" />
                                    </el-select>
                                </el-form-item>
                            </el-form>
                        </div>

                        <div v-if="isColumnConditioning" class="conditioning-status">
                            <el-divider />
                            <div class="status-info">
                                <el-tag type="success" size="large">
                                    <el-icon><Timer /></el-icon>
                                    润柱进行中...
                                </el-tag>
                                <p style="margin-top: 10px; color: #666;">
                                    剩余时间: {{ remainingConditioningTime }} 分钟
                                </p>
                                <p style="color: #666;">
                                    当前信号值: {{ currentSignalValue.toFixed(3) }} AU
                                </p>
                            </div>
                        </div>
                    </div>

                    <template #footer>
                        <div class="dialog-footer">
                            <el-button
                                @click="showColumnConditioningDialog = false"
                                :disabled="isColumnConditioning"
                            >
                                取消
                            </el-button>
                            <el-button
                                v-if="!isColumnConditioning"
                                type="primary"
                                @click="startColumnConditioning"
                                :disabled="!conditioningTime || !conditioningSolution"
                            >
                                开始润柱
                            </el-button>
                            <el-button
                                v-else
                                type="danger"
                                @click="stopColumnConditioning"
                            >
                                停止润柱
                            </el-button>
                        </div>
                    </template>
                </el-dialog>

                <!-- Mock模式弹窗 -->
                <el-dialog
                    v-model="showMockModeDialog"
                    title="Mock模式设置"
                    width="500px"
                >
                    <div class="mock-mode-dialog-content">
                        <div class="mock-info">
                            <el-alert
                                title="Mock模式说明"
                                type="info"
                                description="启用Mock模式后，设备将返回模拟数据而非真实硬件数据，用于开发和测试。"
                                show-icon
                                :closable="false"
                            />
                        </div>

                        <el-divider />

                        <div v-if="loadingDevices" class="loading-section">
                            <el-skeleton :rows="3" animated />
                        </div>

                        <div v-else class="devices-section">
                            <!-- 全部Mock开关 -->
                            <div class="device-item global-mock">
                                <div class="device-info">
                                    <el-icon class="device-icon"><Setting /></el-icon>
                                    <div class="device-details">
                                        <h4>全部设备</h4>
                                        <p>一键控制所有设备的Mock模式</p>
                                    </div>
                                </div>
                                <el-switch
                                    v-model="globalMockMode"
                                    @change="toggleGlobalMockMode"
                                    active-text="Mock"
                                    inactive-text="真实"
                                    :loading="updatingGlobalMock"
                                />
                            </div>

                            <el-divider />

                            <!-- 单个设备Mock开关 -->
                            <div class="devices-list">
                                <div
                                    v-for="device in devices"
                                    :key="device.device_id"
                                    class="device-item"
                                >
                                    <div class="device-info">
                                        <el-icon class="device-icon" :style="{color: getDeviceStatusColor(device.status)}">
                                            <component :is="getDeviceIcon(device.type)" />
                                        </el-icon>
                                        <div class="device-details">
                                            <h4>{{ device.device_name || device.device_id }}</h4>
                                            <p>{{ getDeviceTypeText(device.type) }} - {{ getDeviceStatusText(device.status) }}</p>
                                        </div>
                                    </div>
                                    <el-switch
                                        v-model="device.mockMode"
                                        @change="toggleDeviceMockMode(device)"
                                        active-text="Mock"
                                        inactive-text="真实"
                                        :loading="device.updating"
                                        :disabled="updatingGlobalMock"
                                    />
                                </div>
                            </div>

                            <div v-if="devices.length === 0" class="empty-devices">
                                <el-empty description="暂无设备数据" />
                            </div>
                        </div>
                    </div>

                    <template #footer>
                        <div class="dialog-footer">
                            <el-button @click="showMockModeDialog = false">
                                关闭
                            </el-button>
                            <el-button
                                type="primary"
                                @click="refreshDevicesList"
                                :loading="loadingDevices"
                            >
                                刷新设备
                            </el-button>
                        </div>
                    </template>
                </el-dialog>
            </el-col>
        </el-row>

        <!-- MQTT连接失败弹窗 -->
        <el-dialog
            v-model="showMqttConnectionDialog"
            title="MQTT连接失败"
            width="450px"
            :before-close="handleMqttCancel"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
        >
            <div class="mqtt-connection-dialog">
                <div class="error-icon">
                    <el-icon size="48" color="#f56c6c">
                        <Warning />
                    </el-icon>
                </div>
                <div class="error-content">
                    <h3>MQTT连接失败</h3>
                    <p class="error-message">
                        无法连接到MQTT服务器，这可能影响实时数据的接收。
                    </p>
                    <div class="error-details" v-if="mqttConnectionError">
                        <details>
                            <summary>查看详细错误信息</summary>
                            <pre>{{
                                mqttConnectionError.message ||
                                mqttConnectionError
                            }}</pre>
                        </details>
                    </div>
                    <div class="connection-options">
                        <p>您可以选择：</p>
                        <ul>
                            <li>重新尝试连接MQTT服务器</li>
                            <li>取消连接，继续使用模拟数据</li>
                        </ul>
                    </div>
                </div>
            </div>

            <template #footer>
                <div class="dialog-footer">
                    <el-button
                        @click="handleMqttCancel"
                        :disabled="mqttReconnecting"
                    >
                        取消连接
                    </el-button>
                    <el-button
                        type="primary"
                        @click="handleMqttReconnect"
                        :loading="mqttReconnecting"
                    >
                        {{ mqttReconnecting ? "重连中..." : "重新连接" }}
                    </el-button>
                </div>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { ArrowDown, Delete, Refresh, Timer, Tools, Setting, Operation, View, Box, Switch, Monitor } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRealtimeChart } from "@/composables/useRealtimeChart.js";
import { useDeviceStatus } from "@/composables/useDeviceStatus.js";
import { useTubeRack } from "@/composables/useTubeRack.js";
import { usePeakDetection } from "@/composables/usePeakDetection.js";
import { useGradientControl } from "@/composables/useGradientControl.js";
import mqttService from "@/services/mqtt-service.js";

export default {
    name: "RealtimeMonitoring",
    components: {
        ArrowDown,
    },
    setup() {
        // 使用各个Hook
        const {
            currentValues,
            systemStatus,
            liquidLevels,
            pressureStatus,
            overallStatus,
            liquidWarnings,
            getPressureClass,
            getLiquidColor,
            getWasteColor,
            updateCurrentValues,
            emergencyStop: deviceEmergencyStop,
        } = useDeviceStatus();

        const {
            chartContainer,
            d3Chart,
            timeRange,
            chartSeries,
            detectors,
            runningTime,
            isRunning,
            initChart,
            updateChart,
            startChart,
            stopChart,
            restartChart: originalRestartChart,
            toggleSeries,
            switchDetector,
            updateTimeRange,
            resetZoom,
            exportChart,
            clearChartCache,
            clearAndRestartChart,
            clearChartDataOnly,
        } = useRealtimeChart(currentValues);

        // 包装restartChart方法，在重新开始时获取波长
        const restartChart = async () => {
            await originalRestartChart(fetchWavelengths);
        };

        // 清空图表数据
        const clearChartData = async () => {
            try {
                await ElMessageBox.confirm(
                    "清空操作将删除所有历史数据，是否继续？",
                    "确认清空",
                    {
                        confirmButtonText: "确定",
                        cancelButtonText: "取消",
                        type: "warning",
                    }
                );

                clearChartDataOnly();
                ElMessage.success("图表数据已清空");
            } catch (error) {
                if (error !== "cancel") {
                    console.error("清空图表数据失败:", error);
                    ElMessage.error("清空图表数据失败");
                }
            }
        };

        const {
            tubes,
            currentTube,
            collectionMode,
            selectedTubeForSwitch,
            selectedTubes,
            selectedTubesArray,
            selectedTubesCount,
            mergeTasks,
            showMergeTaskDialog,
            availableTubes,
            completedTubes,
            getTubeClass,
            getTubeTooltip,
            selectTube,
            clearSelection,
            switchToTube,
            changeCollectionMode,
            reverseTubes,
            mergeTubes,
            cleanTubes,
            startTask,
            pauseTask,
            resumeTask,
            terminateTask,
            batchStartTasks,
            batchPauseTasks,
            batchResumeTasks,
            batchTerminateTasks,
            deleteTask,
            closeMergeTaskDialog,
        } = useTubeRack();

        const {
            peakDetectionStatus,
            currentBaseline,
            noiseLevel,
            detectedPeaks,
            showPeakDialog,
            peakCount,
            activePeaks,
            completedPeaks,
            getPeakStatusType,
            getPeakStatusText,
            openPeakDialog,
            closePeakDialog,
            locatePeak,
            exportPeak,
            exportAllPeaks,
        } = usePeakDetection();

        const {
            gradientValues,
            selectedGradientTime,
            availableGradientTimes,
            gradientSum,
            isGradientValid,
            applyGradientChange,
            resetGradientValues,
            fetchAvailableGradientTimes,
        } = useGradientControl();

        // 暂停状态
        const isPaused = ref(false);

        // 馏分收集器展开/折叠状态
        const isFractionCollectorExpanded = ref(false);

        // 任务选择状态
        const selectedTaskIds = ref([]);

        // 检测器波长状态
        const wavelengths = ref({
            uv1: 254, // 第一个UV波长，默认254
            uv2: 280, // 第二个UV波长，默认280
        });

        // MQTT连接失败弹窗状态
        const showMqttConnectionDialog = ref(false);
        const mqttConnectionError = ref(null);
        const mqttReconnecting = ref(false);

        // 新增控制面板状态
        const showGradientDialog = ref(false);
        const showTubeDialog = ref(false);
        const isManualHold = ref(false);

        // 润柱相关状态
        const showColumnConditioningDialog = ref(false);
        const isColumnConditioning = ref(false);
        const conditioningTime = ref(10);
        const conditioningSolution = ref('A');
        const remainingConditioningTime = ref(0);
        const currentSignalValue = ref(0);
        let conditioningInterval = null;

        // Mock模式相关状态
        const showMockModeDialog = ref(false);
        const devices = ref([]);
        const loadingDevices = ref(false);
        const globalMockMode = ref(false);
        const updatingGlobalMock = ref(false);

        // 获取检测器波长的方法
        const fetchWavelengths = async () => {
            try {
                const response = await fetch(
                    "http://0.0.0.0:8008/api/data/device/detector_1/parameter/wavelength"
                );
                if (response.ok) {
                    const data = await response.json();
                    if (data.value && Array.isArray(data.value)) {
                        wavelengths.value.uv1 = data.value[0] || 254;
                        wavelengths.value.uv2 = data.value[1] || 280;
                        console.log("检测器波长已更新:", wavelengths.value);
                    }
                }
            } catch (error) {
                console.error("获取检测器波长失败:", error);
            }
        };

        // 调用实验开始API
        const startExperimentAPI = async () => {
            try {
                const response = await fetch('http://localhost:8008/api/experiments/start/20', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log('实验开始API调用成功:', result);
                return result;
            } catch (error) {
                console.error('实验开始API调用失败:', error);
                throw error;
            }
        };

        // 主要控制方法
        const togglePause = async () => {
            if (!isRunning.value) {
                // 如果图表未运行，则开始
                try {
                    // 调用实验开始API
                    console.log("调用实验开始API: http://localhost:8008/api/experiments/start/20");
                    await startExperimentAPI();
                    console.log("实验开始API调用成功");

                    // 启动图表
                    startChart();
                    isPaused.value = false;
                    console.log("实验已开始");
                    ElMessage.success("实验已开始");

                } catch (error) {
                    console.error("启动实验失败:", error);
                    ElMessage.error(`启动实验失败: ${error.message}`);
                }
            } else if (!isPaused.value) {
                // 如果图表正在运行且未暂停，则暂停（但保持 isRunning 为 true）
                // 这里不调用 stopChart()，而是暂停数据更新
                isPaused.value = true;
                console.log("实验已暂停");
                ElMessage.info("实验已暂停");
            } else {
                // 如果图表已暂停，则继续
                isPaused.value = false;
                console.log("实验已继续");
                ElMessage.success("实验已继续");
            }
        };

        // 紧急停止（使用下面更完整的定义，包含确认对话框）

        // 切换馏分收集器展开/折叠状态
        const toggleFractionCollector = () => {
            isFractionCollectorExpanded.value =
                !isFractionCollectorExpanded.value;
        };

        // 任务管理方法
        const handleTaskSelectionChange = (selection) => {
            selectedTaskIds.value = selection.map((task) => task.id);
        };

        const batchStart = () => {
            batchStartTasks(selectedTaskIds.value);
        };

        const batchPause = () => {
            batchPauseTasks(selectedTaskIds.value);
        };

        const batchResume = () => {
            batchResumeTasks(selectedTaskIds.value);
        };

        const batchTerminate = () => {
            batchTerminateTasks(selectedTaskIds.value);
        };

        const getTaskStatusType = (status) => {
            const statusMap = {
                pending: "info",
                running: "success",
                paused: "warning",
                completed: "success",
                terminated: "danger",
            };
            return statusMap[status] || "info";
        };

        const getTaskStatusText = (status) => {
            const statusMap = {
                pending: "待开始",
                running: "运行中",
                paused: "已暂停",
                completed: "已完成",
                terminated: "已终止",
            };
            return statusMap[status] || "未知";
        };

        const getProgressColor = (status) => {
            const colorMap = {
                pending: "#909399",
                running: "#67c23a",
                paused: "#e6a23c",
                completed: "#67c23a",
                terminated: "#f56c6c",
            };
            return colorMap[status] || "#909399";
        };

        // MQTT连接失败处理方法
        const handleMqttConnectionError = (error) => {
            console.error("MQTT连接失败:", error);
            mqttConnectionError.value = error;
            showMqttConnectionDialog.value = true;
        };

        // 用户选择重新连接MQTT
        const handleMqttReconnect = async () => {
            mqttReconnecting.value = true;
            try {
                await mqttService.reconnect();
                showMqttConnectionDialog.value = false;
                mqttConnectionError.value = null;
            } catch (error) {
                console.error("MQTT重连失败:", error);
                mqttConnectionError.value = error;
            } finally {
                mqttReconnecting.value = false;
            }
        };

        // 润柱相关功能
        const openColumnConditioningDialog = () => {
            showColumnConditioningDialog.value = true;
        };

        const startColumnConditioning = async () => {
            try {
                console.log(`开始润柱: 时间=${conditioningTime.value}分钟, 溶液=${conditioningSolution.value}`);

                isColumnConditioning.value = true;
                remainingConditioningTime.value = conditioningTime.value;

                // 模拟向后端发送润柱开始指令
                const conditioningData = {
                    duration: conditioningTime.value,
                    solution: conditioningSolution.value,
                    timestamp: new Date().toISOString()
                };

                // 这里可以调用实际的API接口
                // await deviceApi.startColumnConditioning(conditioningData);

                ElMessage.success(`润柱已开始，预计${conditioningTime.value}分钟完成`);

                // 开始倒计时和信号值模拟
                conditioningInterval = setInterval(() => {
                    remainingConditioningTime.value -= 0.1;

                    // 模拟信号值变化 (实际应从MQTT获取)
                    currentSignalValue.value = Math.random() * 0.5 + Math.sin(Date.now() / 1000) * 0.1;

                    if (remainingConditioningTime.value <= 0) {
                        stopColumnConditioning();
                    }
                }, 6000); // 每6秒减少0.1分钟 (实际1分钟为10倍速)

            } catch (error) {
                console.error("启动润柱失败:", error);
                ElMessage.error("启动润柱失败");
            }
        };

        const stopColumnConditioning = () => {
            try {
                console.log("停止润柱");

                if (conditioningInterval) {
                    clearInterval(conditioningInterval);
                    conditioningInterval = null;
                }

                isColumnConditioning.value = false;
                remainingConditioningTime.value = 0;
                showColumnConditioningDialog.value = false;

                // 模拟向后端发送停止指令
                // await deviceApi.stopColumnConditioning();

                ElMessage.info("润柱已停止");

            } catch (error) {
                console.error("停止润柱失败:", error);
                ElMessage.error("停止润柱失败");
            }
        };

        // Mock模式相关功能
        const openMockModeDialog = async () => {
            showMockModeDialog.value = true;
            await fetchDevicesList();
        };

        // 获取设备列表
        const fetchDevicesList = async () => {
            loadingDevices.value = true;
            try {
                const response = await fetch(
                    'http://0.0.0.0:8008/api/hardware/devices-status',
                    {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(`获取设备列表失败: ${response.status}`);
                }

                const result = await response.json();
                console.log("设备列表API响应:", result);

                if (result.devices && typeof result.devices === 'object') {
                    // 将devices对象转换为数组格式
                    devices.value = Object.entries(result.devices).map(([deviceId, device]) => ({
                        ...device,
                        device_id: deviceId,
                        mockMode: device.mock || false,
                        updating: false
                    }));

                    // 使用API返回的全局mock状态
                    globalMockMode.value = result.global_mock || false;

                    console.log("设备列表设置成功:", devices.value);
                } else {
                    console.warn("设备列表格式错误:", result);
                    devices.value = [];
                }
            } catch (error) {
                console.error("获取设备列表失败:", error);
                ElMessage.error("获取设备列表失败: " + error.message);

                // 提供测试数据
                devices.value = [
                    {
                        device_id: "bubble_sensor_1",
                        device_name: "气泡传感器1",
                        device_type: "bubble_sensor",
                        type: "bubble_sensor",
                        status: "online",
                        mockMode: false,
                        updating: false
                    },
                    {
                        device_id: "pump_001",
                        device_name: "高压泵-01",
                        device_type: "pump",
                        type: "pump",
                        status: "online",
                        mockMode: false,
                        updating: false
                    },
                    {
                        device_id: "detector_001",
                        device_name: "UV检测器-01",
                        device_type: "detector",
                        type: "detector",
                        status: "online",
                        mockMode: true,
                        updating: false
                    },
                    {
                        device_id: "collector_001",
                        device_name: "分馏收集器-01",
                        device_type: "collector",
                        type: "collector",
                        status: "offline",
                        mockMode: false,
                        updating: false
                    }
                ];
            } finally {
                loadingDevices.value = false;
            }
        };

        // 切换全局Mock模式
        const toggleGlobalMockMode = async (value) => {
            updatingGlobalMock.value = true;
            try {
                await setMockMode(value, null);

                // 更新所有设备的mock模式状态
                devices.value.forEach(device => {
                    device.mockMode = value;
                });

                ElMessage.success(`已${value ? '启用' : '关闭'}全部设备的Mock模式`);
            } catch (error) {
                globalMockMode.value = !value; // 恢复原状态
                ElMessage.error("设置全局Mock模式失败: " + error.message);
            } finally {
                updatingGlobalMock.value = false;
            }
        };

        // 切换单个设备Mock模式
        const toggleDeviceMockMode = async (device) => {
            device.updating = true;
            try {
                await setMockMode(device.mockMode, device.device_id);
                ElMessage.success(`已${device.mockMode ? '启用' : '关闭'}设备 ${device.device_name || device.device_id} 的Mock模式`);

                // 更新全局开关状态
                globalMockMode.value = devices.value.length > 0 &&
                    devices.value.every(d => d.mockMode);
            } catch (error) {
                device.mockMode = !device.mockMode; // 恢复原状态
                ElMessage.error("设置设备Mock模式失败: " + error.message);
            } finally {
                device.updating = false;
            }
        };

        // 调用Mock模式API
        const setMockMode = async (mockMode, deviceId = null) => {
            const requestBody = { mock: mockMode };
            if (deviceId) {
                requestBody.device_id = deviceId;
            }

            const response = await fetch(
                'http://0.0.0.0:8008/api/hardware/mock-mode',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                }
            );

            if (!response.ok) {
                throw new Error(`设置Mock模式失败: ${response.status}`);
            }

            const result = await response.json();
            console.log("Mock模式设置响应:", result);

            if (!result.success) {
                throw new Error(result.message || "设置Mock模式失败");
            }

            return result;
        };

        // 刷新设备列表
        const refreshDevicesList = async () => {
            await fetchDevicesList();
            ElMessage.success("设备列表已刷新");
        };

        // 获取设备类型文本
        const getDeviceTypeText = (type) => {
            const typeMap = {
                'pump': '高压泵',
                'detector': '检测器',
                'collector': '收集器',
                'valve': '阀门',
                'sensor': '传感器'
            };
            return typeMap[type] || type;
        };

        // 获取设备状态文本
        const getDeviceStatusText = (status) => {
            const statusMap = {
                'online': '在线',
                'offline': '离线',
                'error': '错误',
                'maintenance': '维护中'
            };
            return statusMap[status] || status;
        };

        // 获取设备状态颜色
        const getDeviceStatusColor = (status) => {
            const colorMap = {
                'online': '#67c23a',
                'offline': '#909399',
                'error': '#f56c6c',
                'maintenance': '#e6a23c'
            };
            return colorMap[status] || '#909399';
        };

        // 获取设备图标
        const getDeviceIcon = (type) => {
            const iconMap = {
                'pump': 'Operation',
                'detector': 'View',
                'collector': 'Box',
                'valve': 'Switch',
                'sensor': 'Monitor'
            };
            return iconMap[type] || 'Setting';
        };

        // 用户选择取消MQTT连接
        const handleMqttCancel = () => {
            showMqttConnectionDialog.value = false;
            mqttConnectionError.value = null;
            console.log("用户取消MQTT连接");
        };

        // 新增控制面板方法（togglePause已在上面定义，这里删除重复定义）

        const emergencyStop = () => {
            ElMessageBox.confirm(
                "确定要终止实验吗？此操作不可撤销。",
                "确认终止",
                {
                    confirmButtonText: "确定",
                    cancelButtonText: "取消",
                    type: "warning",
                }
            )
                .then(() => {
                    // 停止图表并重置状态
                    stopChart();
                    deviceEmergencyStop();

                    // 重置为初始状态，以便显示"开始"按钮
                    isPaused.value = false;
                    // isRunning 会被 stopChart() 自动设置为 false

                    console.log("实验已终止");
                    ElMessage.warning("实验已终止");
                })
                .catch(() => {
                    console.log("取消终止操作");
                });
        };

        // 手动保持 - 不影响开始按钮状态
        const toggleManualHold = () => {
            isManualHold.value = !isManualHold.value;
            console.log(
                isManualHold.value ? "已开启手动保持" : "已取消手动保持"
            );
            ElMessage.info(
                isManualHold.value ? "已开启手动保持模式" : "已取消手动保持模式"
            );
        };

        // 收集模式切换 - 不影响开始按钮状态
        const toggleCollectionMode = () => {
            const newMode = collectionMode.value === "收集" ? "废液" : "收集";
            changeCollectionMode(newMode);
            console.log(`已切换到${newMode}模式`);
            ElMessage.success(`已切换到${newMode}模式`);
        };

        // 记录洗脱比例修改前的状态
        const gradientModificationState = ref({
            wasRunningBeforeModification: false,
            wasModifying: false,
        });

        // 打开洗脱比例弹窗 - 如果实验正在运行，先暂停
        const openGradientDialog = () => {
            gradientModificationState.value.wasRunningBeforeModification =
                isRunning.value && !isPaused.value;
            gradientModificationState.value.wasModifying = true;

            if (gradientModificationState.value.wasRunningBeforeModification) {
                // 如果正在运行，先暂停（不调用stopChart，保持isRunning状态）
                isPaused.value = true;
                console.log("为修改洗脱比例暂停实验");
                ElMessage.info("已暂停实验，可修改洗脱液比例");
            }

            showGradientDialog.value = true;
        };

        // 应用洗脱比例修改 - 相当于继续
        const applyGradientChangeWrapper = () => {
            console.log("应用洗脱液比例修改被点击", selectedGradientTime.value);
            const success = applyGradientChange();

            // 只有成功应用了梯度变更才关闭对话框
            if (success) {
                showGradientDialog.value = false;

                if (
                    gradientModificationState.value.wasRunningBeforeModification
                ) {
                    // 如果修改前是运行状态，现在继续（不需要调用startChart，isRunning已经是true）
                    isPaused.value = false;
                    console.log("应用洗脱比例修改，继续实验");
                    ElMessage.success("洗脱液比例已更新，实验继续");
                } else {
                    console.log("应用洗脱比例修改，实验未运行状态不变");
                    ElMessage.success("洗脱液比例已更新");
                }

                // 重置状态
                gradientModificationState.value.wasRunningBeforeModification = false;
                gradientModificationState.value.wasModifying = false;
            } else {
                // 如果应用失败，显示错误信息但不关闭对话框
                ElMessage.error("请完善梯度设置后再应用");
            }
        };

        // 取消洗脱比例修改
        const cancelGradientChange = () => {
            if (gradientModificationState.value.wasRunningBeforeModification) {
                // 如果修改前是运行状态，现在继续（不需要调用startChart，isRunning已经是true）
                isPaused.value = false;
                console.log("取消洗脱比例修改，继续实验");
                ElMessage.info("已取消修改，实验继续");
            }

            showGradientDialog.value = false;
            // 重置状态
            gradientModificationState.value.wasRunningBeforeModification = false;
            gradientModificationState.value.wasModifying = false;
        };

        // 切换试管 - 不影响开始按钮状态
        const switchToTubeWrapper = () => {
            // 验证是否选择了试管且不是当前试管
            if (!selectedTubeForSwitch.value) {
                ElMessage.error("请选择要切换的试管");
                return;
            }

            if (selectedTubeForSwitch.value === currentTube.value) {
                ElMessage.error("不能切换到当前试管");
                return;
            }

            try {
                switchToTube();
                showTubeDialog.value = false;
                ElMessage.success(
                    `已切换到试管 ${selectedTubeForSwitch.value}`
                );
            } catch (error) {
                console.error("切换试管失败:", error);
                ElMessage.error("切换试管失败，请重试");
            }
        };

        // 打开试管切换对话框，并自动选择下一个试管
        const openTubeSwitchDialog = () => {
            // 获取当前试管号
            const currentTubeNumber = parseInt(currentTube.value);

            // 找到下一个可用试管
            const nextTube = availableTubes.value.find(
                (tube) => parseInt(tube) > currentTubeNumber
            );

            // 如果没有找到更大的试管号，选择第一个可用试管（循环）
            const defaultSelectedTube = nextTube || availableTubes.value[0];

            // 设置默认选择的试管
            if (
                defaultSelectedTube &&
                defaultSelectedTube !== currentTube.value
            ) {
                selectedTubeForSwitch.value = defaultSelectedTube;
            } else {
                // 如果没有其他可用试管，清空选择
                selectedTubeForSwitch.value = null;
            }

            // 显示对话框
            showTubeDialog.value = true;

            console.log(
                `当前试管: ${currentTube.value}, 默认选择: ${selectedTubeForSwitch.value}`
            );
        };

        // 数据更新定时器
        let dataUpdateInterval = null;

        // 生命周期
        onMounted(async () => {
            // 获取可用梯度时间
            fetchAvailableGradientTimes();

            // 初始化D3图表
            await nextTick();
            initChart();

            // 监听MQTT连接状态变化
            mqttService.onStatusChange((status) => {
                if (
                    !status.connected &&
                    status.error &&
                    !showMqttConnectionDialog.value
                ) {
                    handleMqttConnectionError(status.error);
                }
            });

            // 模拟数据更新
            dataUpdateInterval = setInterval(() => {
                if (!isPaused.value) {
                    // 更新UV值
                    updateCurrentValues({
                        uv: Math.max(
                            0,
                            currentValues.value.uv +
                                (Math.random() - 0.5) * 0.02
                        ),
                        uv254: Math.max(
                            0,
                            currentValues.value.uv254 +
                                (Math.random() - 0.5) * 0.025 +
                                Math.sin(Date.now() / 10000) * 0.1 // 添加周期性变化
                        ),
                        uv280: Math.max(
                            0,
                            currentValues.value.uv280 +
                                (Math.random() - 0.5) * 0.018 +
                                Math.cos(Date.now() / 8000) * 0.08 // 添加不同的周期性变化
                        ),
                        pressure: Math.max(
                            0,
                            currentValues.value.pressure +
                                (Math.random() - 0.5) * 20
                        ),
                    });

                    // 更新D3图表
                    updateChart();
                }
            }, 1000);
        });

        onUnmounted(() => {
            if (dataUpdateInterval) {
                clearInterval(dataUpdateInterval);
            }
            if (experimentInfoUpdateInterval) {
                clearInterval(experimentInfoUpdateInterval);
            }
        });

        // 使用ref来跟踪实验状态变化
        const experimentInfo = ref(null);

        // 获取当前实验状态信息
        const getCurrentExperimentInfo = () => {
            try {
                const savedExperiment = localStorage.getItem('currentExperiment');
                if (!savedExperiment) {
                    return null;
                }
                return JSON.parse(savedExperiment);
            } catch (error) {
                console.error('获取实验状态失败:', error);
                return null;
            }
        };

        // 更新实验信息
        const updateExperimentInfo = () => {
            experimentInfo.value = getCurrentExperimentInfo();
        };

        // 获取实验流程状态显示文本
        const getExperimentStepDisplayText = () => {
            const experiment = experimentInfo.value;
            if (!experiment || !experiment.status) {
                return '空闲';
            }

            // 如果是预处理状态，显示具体的预处理步骤
            if (experiment.status === 'pretreatment' && experiment.currentPretreatmentStep) {
                const stepNames = {
                    preprocessing_sequence: '预处理序列',
                    purge_column: '吹扫柱子',
                    purge_system: '吹扫系统',
                    column_equilibration: '柱平衡',
                };
                return stepNames[experiment.currentPretreatmentStep] || experiment.currentPretreatmentStep;
            }

            // 其他状态
            const statusNames = {
                pretreatment: '预处理中',
                running: '正式实验',
                paused: '已暂停',
                completed: '已完成',
                failed: '失败'
            };

            return statusNames[experiment.status] || '空闲';
        };

        // 获取实验流程状态指示器的样式类
        const getExperimentStepIndicatorClass = () => {
            const experiment = experimentInfo.value;
            if (!experiment || !experiment.status) {
                return 'offline'; // 空闲状态显示灰色
            }

            // 根据实验状态返回不同的颜色
            switch (experiment.status) {
                case 'pretreatment':
                case 'running':
                    return 'online'; // 运行中显示绿色
                case 'paused':
                    return 'warning'; // 暂停显示橙色
                case 'failed':
                    return 'error'; // 失败显示红色
                case 'completed':
                    return 'success'; // 完成显示蓝色
                default:
                    return 'offline'; // 其他状态显示灰色
            }
        };

        // 初始化实验信息
        updateExperimentInfo();

        // 定期更新实验状态
        const experimentInfoUpdateInterval = setInterval(() => {
            updateExperimentInfo();
        }, 1000);

        // 判断实验是否已经开始过（有实验状态记录）
        const hasExperimentStarted = computed(() => {
            const experiment = experimentInfo.value;
            return experiment && experiment.status &&
                   ['pretreatment', 'running', 'paused', 'completed', 'failed'].includes(experiment.status);
        });

        // 获取开始按钮的文本
        const getStartButtonText = () => {
            if (!isRunning.value) {
                // 如果图表没有运行，根据实验是否已经开始过来显示文本
                return hasExperimentStarted.value ? '继续' : '开始';
            }
            return '开始'; // 这个分支通常不会执行，因为有v-if="!isRunning"
        };

        return {
            // 状态
            isPaused,
            isFractionCollectorExpanded,
            wavelengths,

            // 设备状态Hook
            currentValues,
            systemStatus,
            liquidLevels,
            pressureStatus,
            overallStatus,
            liquidWarnings,
            getPressureClass,
            getLiquidColor,
            getWasteColor,

            // 图表Hook
            chartContainer,
            d3Chart,
            timeRange,
            chartSeries,
            detectors,
            runningTime,
            isRunning,
            toggleSeries,
            switchDetector,
            updateTimeRange,
            resetZoom,
            exportChart,

            // 试管管理Hook
            tubes,
            currentTube,
            collectionMode,
            selectedTubeForSwitch,
            selectedTubes,
            selectedTubesArray,
            selectedTubesCount,
            mergeTasks,
            showMergeTaskDialog,
            availableTubes,
            completedTubes,
            getTubeClass,
            getTubeTooltip,
            selectTube,
            clearSelection,
            switchToTube,
            changeCollectionMode,
            reverseTubes,
            mergeTubes,
            cleanTubes,
            startTask,
            pauseTask,
            resumeTask,
            terminateTask,
            batchStartTasks,
            batchPauseTasks,
            batchResumeTasks,
            batchTerminateTasks,
            deleteTask,
            closeMergeTaskDialog,

            // 峰检测Hook
            peakDetectionStatus,
            currentBaseline,
            noiseLevel,
            detectedPeaks,
            showPeakDialog,
            peakCount,
            activePeaks,
            completedPeaks,
            getPeakStatusType,
            getPeakStatusText,
            openPeakDialog,
            closePeakDialog,
            locatePeak,
            exportPeak,
            exportAllPeaks,

            // 梯度控制Hook
            gradientValues,
            selectedGradientTime,
            availableGradientTimes,
            gradientSum,
            isGradientValid,
            applyGradientChange: applyGradientChangeWrapper,
            resetGradientValues,

            // 主要控制方法
            startExperimentAPI,
            togglePause,
            restartChart,
            clearChartData,
            emergencyStop,
            toggleFractionCollector,

            // 任务管理
            selectedTaskIds,
            handleTaskSelectionChange,
            batchStart,
            batchPause,
            batchResume,
            batchTerminate,
            getTaskStatusType,
            getTaskStatusText,
            getProgressColor,

            // 新增控制面板
            showGradientDialog,
            showTubeDialog,
            isManualHold,
            gradientModificationState,

            // 润柱相关
            showColumnConditioningDialog,
            isColumnConditioning,
            conditioningTime,
            conditioningSolution,
            remainingConditioningTime,
            currentSignalValue,
            toggleManualHold,
            toggleCollectionMode,
            openGradientDialog,
            cancelGradientChange,
            openTubeSwitchDialog,
            switchToTube: switchToTubeWrapper,
            openColumnConditioningDialog,
            startColumnConditioning,
            stopColumnConditioning,

            // Mock模式相关
            showMockModeDialog,
            devices,
            loadingDevices,
            globalMockMode,
            updatingGlobalMock,
            openMockModeDialog,
            toggleGlobalMockMode,
            toggleDeviceMockMode,
            refreshDevicesList,
            getDeviceTypeText,
            getDeviceStatusText,
            getDeviceStatusColor,
            getDeviceIcon,

            // MQTT连接失败处理
            showMqttConnectionDialog,
            mqttConnectionError,
            mqttReconnecting,
            handleMqttReconnect,
            handleMqttCancel,

            // 实验流程状态
            experimentInfo,
            hasExperimentStarted,
            getExperimentStepDisplayText,
            getExperimentStepIndicatorClass,
            getStartButtonText,
        };
    },
};
</script>

<style scoped>
.realtime-monitoring {
    padding: 20px;
}

/* 顶部控制面板样式 */
.monitoring-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    margin-bottom: 0px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    gap: 24px;
}

.monitoring-header h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    flex-shrink: 0;
}

.status-indicators {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;
    justify-content: center;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
}

.status-item.peak-info {
    gap: 12px;
}

.peak-stat-inline {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
}

.peak-stat-inline .stat-label {
    color: #666;
    font-weight: normal;
}

.peak-stat-inline .stat-value {
    font-weight: 600;
    color: #1e293b;
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.status-indicator.online {
    background-color: #67c23a;
    animation: pulse 2s infinite;
}

.status-indicator.offline {
    background-color: #909399;
}

.status-indicator.warning {
    background-color: #e6a23c;
    animation: pulse 2s infinite;
}

.status-indicator.error {
    background-color: #f56c6c;
    animation: pulse 2s infinite;
}

.status-indicator.success {
    background-color: #409eff;
    animation: pulse 2s infinite;
}

.status-text {
    color: #333;
}

@keyframes pulse {
    0%,
    100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* 主内容区域样式 */
.main-content {
    min-height: calc(100vh - 200px);
}

.main-content .el-col {
    display: flex;
    flex-direction: column;
}

/* 图表工具栏一排显示样式 */
.chart-toolbar-inline {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.time-range {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    min-width: 150px;
}

.time-range .el-select {
    min-width: 120px;
    width: auto;
    flex: 1;
    max-width: 200px;
}

/* 响应式时间范围组件 */
@media (max-width: 768px) {
    .time-range {
        min-width: 120px;
        flex-direction: column;
        gap: 4px;
        align-items: flex-start;
    }

    .time-range .el-select {
        min-width: 100px;
        width: 100%;
        max-width: none;
    }
}

@media (max-width: 576px) {
    .time-range {
        min-width: 100px;
    }

    .time-range .el-select {
        min-width: 80px;
    }
}

.time-range label {
    font-size: 14px;
    color: #666;
    font-weight: 500;
}

.detector-controls {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.chart-controls {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

/* 数据卡片头部样式 */
.data-card {
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e1e5e9;
    margin-bottom: 20px;
    overflow: hidden;
    width: 100%;
    box-sizing: border-box;
}

.data-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #e1e5e9;
    flex-wrap: wrap;
    gap: 16px;
}

.data-card-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
    flex-shrink: 0;
}

/* 图表图例勾选框样式 */
.chart-legend {
    padding: 12px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #e1e5e9;
}

.legend-checkboxes {
    display: flex;
    align-items: center;
    gap: 8px; /* 减少间距以适应更多选项 */
    flex-wrap: nowrap; /* 强制在一行显示 */
    overflow-x: auto; /* 如果内容过长，允许水平滚动 */
    overflow-y: hidden;
    padding: 2px 0; /* 为滚动条留出空间 */
    scrollbar-width: thin; /* Firefox */
    scrollbar-color: #cbd5e1 transparent; /* Firefox */
}

/* 自定义滚动条样式 */
.legend-checkboxes::-webkit-scrollbar {
    height: 4px;
}

.legend-checkboxes::-webkit-scrollbar-track {
    background: transparent;
}

.legend-checkboxes::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 2px;
}

.legend-checkboxes::-webkit-scrollbar-thumb:hover {
    background-color: #94a3b8;
}

.legend-checkbox {
    display: flex;
    align-items: center;
    margin-right: 0 !important;
    flex-shrink: 0; /* 防止收缩 */
    white-space: nowrap; /* 防止内容换行 */
}

.legend-checkbox .el-checkbox__input {
    margin-right: 8px;
    flex-shrink: 0; /* 防止收缩 */
}

.legend-checkbox .el-checkbox__label {
    display: flex;
    align-items: center;
    gap: 4px; /* 减少间距 */
    padding-left: 0;
    font-size: 13px;
    color: #333;
    flex-shrink: 0; /* 防止label收缩 */
    white-space: nowrap; /* 防止换行 */
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    display: inline-block;
    flex-shrink: 0; /* 防止收缩 */
}

.legend-color.uv254 {
    background-color: #2563eb;
}

.legend-color.uv280 {
    background-color: #06b6d4;
}

.legend-color.gradient-a {
    background-color: #f56c6c;
}

.legend-color.gradient-b {
    background-color: #67c23a;
}

.legend-color.pressure {
    background-color: #e6a23c;
}

.legend-text {
    font-weight: 500;
    user-select: none;
    display: inline-flex;
    align-items: center;
    white-space: nowrap; /* 防止换行 */
    gap: 2px; /* 标签和数值之间的小间距 */
}

/* 为数值部分添加固定宽度 */
.legend-text .legend-label {
    flex-shrink: 0;
}

.legend-text .legend-value {
    display: inline-block;
    text-align: right;
    min-width: 45px; /* 固定数值显示区域宽度 */
    font-family: "Monaco", "Menlo", "Ubuntu Mono", "Consolas", monospace; /* 等宽字体 */
    color: #666; /* 稍微区分数值的颜色 */
    flex-shrink: 0;
}

/* 响应式调整图例选项 */
@media (max-width: 1200px) {
    .legend-checkboxes {
        gap: 6px;
    }

    .legend-checkbox .el-checkbox__label {
        font-size: 12px;
    }

    .legend-text .legend-value {
        min-width: 40px;
        font-size: 12px;
    }
}

@media (max-width: 992px) {
    .legend-checkboxes {
        gap: 4px;
    }

    .legend-checkbox .el-checkbox__label {
        font-size: 11px;
        gap: 3px;
    }

    .legend-text .legend-value {
        min-width: 35px;
        font-size: 11px;
    }

    .legend-color {
        width: 10px;
        height: 10px;
    }
}

@media (max-width: 768px) {
    .legend-checkboxes {
        gap: 2px;
        font-size: 10px;
    }

    .legend-checkbox .el-checkbox__label {
        font-size: 10px;
        gap: 2px;
    }

    .legend-text .legend-value {
        min-width: 30px;
        font-size: 10px;
    }

    .legend-color {
        width: 8px;
        height: 8px;
    }

    .legend-checkbox .el-checkbox__input {
        margin-right: 4px;
    }
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chart-card {
    margin-bottom: 20px;
}

.chart-container {
    height: 700px;
    width: 100%;
    box-sizing: border-box;
}

.chart-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 8px 0;
    border-bottom: 1px solid #ebeef5;
}

/* time-range label样式已在上面定义，此处移除重复定义 */

.legend {
    display: flex;
    gap: 16px;
}

.legend-item {
    display: flex;
    align-items: center;
    font-size: 12px;
}

.legend-color {
    width: 12px;
    height: 12px;
    margin-right: 4px;
    border-radius: 2px;
}

.legend-color.uv {
    background-color: #409eff;
}

.legend-color.gradient-a {
    background-color: #f56c6c;
}

.legend-color.gradient-b {
    background-color: #67c23a;
}

.legend-color.gradient-c {
    background-color: #e6a23c;
}

.legend-color.gradient-d {
    background-color: #909399;
}

.chart-area {
    height: 300px;
    background-color: #ffffff;
    border: 1px solid #e1e5e9;
    position: relative;
    overflow: hidden;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
}

.chromatogram-chart {
    width: 100%;
    height: 100%;
    display: block;
    box-sizing: border-box;
}

/* D3图表样式 */
.chromatogram-chart .grid-x line,
.chromatogram-chart .grid-y line {
    stroke: #e1e5e9;
    stroke-opacity: 0.7;
    shape-rendering: crispEdges;
}

.chromatogram-chart .grid-x path,
.chromatogram-chart .grid-y path {
    stroke-width: 0;
}

.chromatogram-chart .x-axis,
.chromatogram-chart .y-axis-left,
.chromatogram-chart .y-axis-right {
    font-size: 12px;
    color: #666;
}

.chromatogram-chart .y-axis-left {
    color: #409eff;
}

.chromatogram-chart .y-axis-right {
    color: #666;
}

.chromatogram-chart .x-label,
.chromatogram-chart .y-label-left,
.chromatogram-chart .y-label-right {
    font-size: 14px;
    font-weight: 500;
    color: #333;
}

.chromatogram-chart .y-label-left {
    color: #409eff;
}

.chromatogram-chart .y-label-right {
    color: #666;
}

.chromatogram-chart .uv254-line {
    filter: drop-shadow(0 1px 2px rgba(37, 99, 235, 0.3));
}

.chromatogram-chart .uv280-line {
    filter: drop-shadow(0 1px 2px rgba(6, 182, 212, 0.3));
}

.chromatogram-chart .gradient-a-line {
    filter: drop-shadow(0 1px 1px rgba(245, 108, 108, 0.3));
}

.chromatogram-chart .gradient-b-line {
    filter: drop-shadow(0 1px 1px rgba(103, 194, 58, 0.3));
}

.chromatogram-chart .gradient-c-line {
    filter: drop-shadow(0 1px 1px rgba(230, 162, 60, 0.3));
}

.chromatogram-chart .gradient-d-line {
    filter: drop-shadow(0 1px 1px rgba(144, 147, 153, 0.3));
}

.chart-placeholder {
    text-align: center;
    color: #909399;
}

.chart-icon {
    font-size: 48px;
    margin-bottom: 16px;
}

.chart-info {
    font-size: 12px;
    margin-top: 8px;
}

.chart-info-bar {
    margin-top: 16px;
    padding: 8px 0;
    border-top: 1px solid #ebeef5;
}

.current-values {
    display: flex;
    gap: 24px;
    font-size: 14px;
}

.pressure.normal {
    color: #67c23a;
}

.pressure.warning {
    color: #e6a23c;
}

.pressure.danger {
    color: #f56c6c;
}

.tube-rack-card {
    margin-top: 0px;
    margin-bottom: 0px;
    clear: both;
}

.tube-rack {
    margin-left: 30px;
    overflow: hidden;
}

/* 响应式馏分收集器整体布局 */
@media (max-width: 1200px) {
    .tube-rack {
        margin-left: 20px;
    }
}

@media (max-width: 768px) {
    .tube-rack {
        margin-left: 10px;
    }
}

@media (max-width: 576px) {
    .tube-rack {
        margin-left: 5px;
    }
}

.rack-header-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}

/* 响应式头部控制区域 */
@media (max-width: 992px) {
    .rack-header-controls {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
    }

    .rack-stats {
        justify-content: center;
    }

    .rack-actions {
        justify-content: center;
    }
}

@media (max-width: 768px) {
    .rack-header-controls {
        gap: 8px;
    }

    .rack-actions .el-button {
        padding: 8px 12px;
        font-size: 12px;
    }
}

.rack-stats {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
}

.rack-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.rack-stats .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: none;
    border: none;
    border-radius: 0;
    padding: 0;
    transition: none;
    position: static;
    overflow: visible;
}

.rack-stats .stat-item::before {
    display: none;
}

.rack-stats .stat-item:hover {
    border-color: transparent;
    transform: none;
    box-shadow: none;
}

.rack-stats .stat-number {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 2px;
    font-family: inherit;
}

.rack-stats .stat-label {
    font-size: 16px;
    color: #64748b;
    font-weight: 500;
    text-align: center;
    line-height: 1.2;
}

.tube-info {
    display: flex;
    gap: 16px;
    font-size: 14px;
}

.rack-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;
    margin-bottom: 20px;
    max-width: 100%;
    overflow: hidden;
}

/* 响应式布局 - 不同屏幕尺寸下的试管排布 */
@media (max-width: 1400px) {
    .rack-grid {
        grid-template-columns: repeat(8, 1fr);
    }
}

@media (max-width: 1200px) {
    .rack-grid {
        grid-template-columns: repeat(6, 1fr);
    }
}

@media (max-width: 992px) {
    .rack-grid {
        grid-template-columns: repeat(5, 1fr);
    }
}

@media (max-width: 768px) {
    .rack-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (max-width: 576px) {
    .rack-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

.tube-slot {
    position: relative;
    width: 40px;
    height: 60px;
    min-width: 25px;
    min-height: 38px;
    border: 2px solid #dcdfe6;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
    background-color: #fff;
    aspect-ratio: 2/3;
}

/* 响应式试管尺寸调整 */
@media (max-width: 1200px) {
    .tube-slot {
        width: 35px;
        height: 52px;
    }
}

@media (max-width: 992px) {
    .tube-slot {
        width: 32px;
        height: 48px;
    }
}

@media (max-width: 768px) {
    .tube-slot {
        width: 30px;
        height: 45px;
    }
}

@media (max-width: 576px) {
    .tube-slot {
        width: 28px;
        height: 42px;
    }
}

.tube-slot:hover {
    border-color: #409eff;
}

.tube-slot.empty {
    border-color: #dcdfe6;
}

.tube-slot.ready {
    border-color: #fadb14;
    background-color: #fffbe6;
}

.tube-slot.collecting {
    border-color: #409eff;
    background-color: #f0f9ff;
    animation: collecting-pulse 2s infinite;
}

.tube-slot.completed {
    border-color: #67c23a;
    background-color: #f6ffed;
}

.tube-slot.waste {
    border-color: #909399;
    background-color: #f4f4f5;
}

.tube-slot.selected {
    border-color: #ff6b35 !important;
    background-color: #fff5f0 !important;
    box-shadow: 0 0 8px rgba(255, 107, 53, 0.4);
    transform: scale(1.05);
}

@keyframes collecting-pulse {
    0%,
    100% {
        box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
    }
    50% {
        box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.1);
    }
}

.tube-number {
    position: absolute;
    top: 2px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 10px;
    font-weight: bold;
    color: #666;
    white-space: nowrap;
}

/* 响应式试管编号字体大小 */
@media (max-width: 992px) {
    .tube-number {
        font-size: 9px;
        top: 1px;
    }
}

@media (max-width: 768px) {
    .tube-number {
        font-size: 8px;
        top: 1px;
    }
}

@media (max-width: 576px) {
    .tube-number {
        font-size: 7px;
        top: 1px;
    }
}

.tube-fill {
    position: absolute;
    bottom: 0;
    left: 2px;
    right: 2px;
    background-color: #409eff;
    border-radius: 0 0 2px 2px;
    transition: height 0.3s ease;
}

.tube-legend {
    display: flex;
    gap: 16px;
    justify-content: center;
    flex-wrap: wrap;
}

/* 响应式试管图例 */
@media (max-width: 768px) {
    .tube-legend {
        gap: 12px;
    }

    .tube-legend .legend-item {
        font-size: 11px;
    }

    .tube-sample {
        width: 14px;
        height: 18px;
    }
}

@media (max-width: 576px) {
    .tube-legend {
        gap: 8px;
    }

    .tube-legend .legend-item {
        font-size: 10px;
    }

    .tube-sample {
        width: 12px;
        height: 16px;
    }
}

.tube-legend .legend-item {
    display: flex;
    align-items: center;
    font-size: 12px;
}

.tube-sample {
    width: 16px;
    height: 20px;
    border: 1px solid;
    border-radius: 2px;
    margin-right: 4px;
}

.tube-sample.empty {
    border-color: #dcdfe6;
    background-color: #fff;
}

.tube-sample.ready {
    border-color: #fadb14;
    background-color: #fffbe6;
}

.tube-sample.collecting {
    border-color: #409eff;
    background-color: #f0f9ff;
}

.tube-sample.completed {
    border-color: #67c23a;
    background-color: #f6ffed;
}

.tube-sample.waste {
    border-color: #909399;
    background-color: #f4f4f5;
}

.device-status-card,
.peak-detection-card,
.control-panel-card {
    margin-bottom: 20px;
    margin-left: 0px;
}

.status-section {
    margin-bottom: 20px;
}

.status-section h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.status-indicator.online {
    background-color: #67c23a;
}

.status-indicator.offline {
    background-color: #909399;
}

.status-indicator.warning {
    background-color: #e6a23c;
}

.status-indicator.error {
    background-color: #f56c6c;
}

.gauge-container {
    text-align: center;
    margin-bottom: 12px;
}

.gauge-placeholder {
    width: 120px;
    height: 120px;
    border: 4px solid #dcdfe6;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
}

.gauge-icon {
    font-size: 24px;
    color: #909399;
}

.range-color {
    width: 12px;
    height: 12px;
    margin-right: 8px;
    border-radius: 2px;
}

.range-color.safe {
    background-color: #67c23a;
}

.range-color.warning {
    background-color: #e6a23c;
}

.range-color.danger {
    background-color: #f56c6c;
}

.temperature-info,
.liquid-levels {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.temp-item,
.liquid-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.temp-item label,
.liquid-item label {
    font-size: 14px;
    color: #666;
    min-width: 60px;
}

.temp-value {
    font-weight: bold;
    color: #333;
}

.peak-summary {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.summary-label {
    color: #666;
    font-size: 14px;
}

.summary-value {
    font-weight: bold;
    color: #333;
}

.peak-list-header {
    font-weight: bold;
    margin-bottom: 8px;
    color: #333;
}

.no-peaks {
    text-align: center;
    padding: 20px 0;
}

.peaks-table {
    max-height: 200px;
    overflow-y: auto;
}

.peak-row {
    padding: 8px;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

.peak-row:hover {
    background-color: #f8f9fa;
}

.peak-row.peak-active {
    border-color: #409eff;
    background-color: #f0f9ff;
}

.peak-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.peak-number {
    font-weight: bold;
    color: #333;
}

.peak-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 12px;
    color: #666;
}

.control-section {
    margin-bottom: 20px;
}

.control-section h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
}

.control-row {
    display: flex;
    gap: 8px;
    align-items: center;
}

.control-row .el-select {
    flex: 1;
}

.gradient-controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.gradient-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.gradient-item label {
    min-width: 50px;
    font-size: 14px;
    color: #666;
}

.gradient-item .el-slider {
    flex: 1;
}

.gradient-item span {
    min-width: 40px;
    font-weight: bold;
    color: #333;
}

.control-section.emergency {
    border-top: 1px solid #ebeef5;
    padding-top: 20px;
}

.emergency-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: bold;
}

/* 峰检测紧凑摘要样式 */
.peak-summary-compact {
    padding: 16px 20px;
}

.summary-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 12px;
    background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.stat-item::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.stat-item:hover {
    border-color: #667eea;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.stat-number {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stat-label {
    font-size: 15px;
    color: #64748b;
    font-weight: 500;
    text-align: center;
    line-height: 1.3;
}

/* 峰检测弹窗样式 */
.peak-dialog-content {
    padding: 16px 0;
}

.peak-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 20px;
}

.summary-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.summary-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.summary-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.summary-icon {
    font-size: 28px;
    width: 56px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #ffffff;
    border-radius: 12px;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.summary-content {
    flex: 1;
}

.summary-value {
    font-size: 24px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.summary-label {
    font-size: 13px;
    color: #64748b;
    font-weight: 500;
    line-height: 1.2;
}

.peak-table-container {
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e1e5e9;
}

.peak-number {
    font-weight: 600;
    color: #6366f1;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

/* 合并任务弹窗样式 */
.merge-task-dialog {
    .el-dialog__body {
        padding: 20px;
    }
}

.merge-task-content {
    min-height: 400px;
}

.selected-tubes-info {
    margin-bottom: 16px;
}

.selected-tubes-info h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 16px;
    font-weight: 600;
}

.selected-tubes-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.selected-tube-tag {
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 6px;
}

.task-list-section {
    margin-top: 16px;
}

.task-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.task-list-header h4 {
    margin: 0;
    color: #333;
    font-size: 16px;
    font-weight: 600;
}

.batch-controls {
    display: flex;
    gap: 8px;
}

.tube-ids {
    font-weight: 600;
    color: #6366f1;
}

.task-actions {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: center;
}

.task-actions .el-button {
    margin: 0;
}

.progress-text {
    font-size: 12px;
    color: #666;
    margin-top: 4px;
}

.task-summary {
    text-align: center;
    padding: 40px 0;
}

/* MQTT连接失败弹窗样式 */
.mqtt-connection-dialog {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
}

.mqtt-connection-dialog .error-icon {
    margin-bottom: 16px;
}

.mqtt-connection-dialog .error-content {
    text-align: center;
    width: 100%;
}

.mqtt-connection-dialog h3 {
    margin: 0 0 12px 0;
    color: #f56c6c;
    font-size: 18px;
    font-weight: 600;
}

.mqtt-connection-dialog .error-message {
    margin: 0 0 16px 0;
    color: #666;
    line-height: 1.6;
}

.mqtt-connection-dialog .error-details {
    margin: 16px 0;
    text-align: left;
}

.mqtt-connection-dialog .error-details details {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 8px 12px;
}

.mqtt-connection-dialog .error-details summary {
    cursor: pointer;
    color: #666;
    font-size: 14px;
    margin-bottom: 8px;
}

.mqtt-connection-dialog .error-details pre {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 8px;
    margin: 8px 0 0 0;
    font-size: 12px;
    color: #d32f2f;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

.mqtt-connection-dialog .connection-options {
    margin: 16px 0 0 0;
    text-align: left;
}

.mqtt-connection-dialog .connection-options p {
    margin: 0 0 8px 0;
    color: #666;
    font-weight: 500;
}

.mqtt-connection-dialog .connection-options ul {
    margin: 0;
    padding-left: 20px;
    color: #666;
}

.mqtt-connection-dialog .connection-options li {
    margin-bottom: 4px;
    line-height: 1.5;
}

/* 馏分收集器折叠面板样式 */
.fraction-collector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #e1e5e9;
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
}

.fraction-collector-header:hover {
    background: #f1f5f9;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;
}

.header-left .data-card-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.basic-stats {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.basic-stat {
    font-size: 12px;
    color: #64748b;
    background: #e2e8f0;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
}

.header-right {
    display: flex;
    align-items: center;
}

.expand-icon {
    font-size: 16px;
    color: #64748b;
    transition: transform 0.3s ease;
    transform: rotate(180deg); /* 默认向上指 */
}

.expand-icon.expanded {
    transform: rotate(0deg); /* 展开时向下指 */
}

/* 可折叠内容区域 - 向上展开 */
.fraction-collector-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
    order: 2;
    background: #ffffff;
    border-top: 1px solid #e1e5e9;
}

.fraction-collector-content.expanded {
    max-height: 600px;
    transition: max-height 0.3s ease-in;
}

/* 馏分收集器容器改为flex布局，头部在下方 */
.tube-rack-card {
    display: flex;
    flex-direction: column-reverse;
}

/* 操作按钮面板 */
.rack-actions-panel {
    padding: 16px 20px;
    background: #ffffff;
    border-top: 1px solid #e1e5e9;
    border-bottom: 1px solid #e1e5e9;
}

.rack-actions-panel .rack-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
}

/* 图表区域动态高度调整 */
.chart-container-card {
    transition: all 0.3s ease;
}

/* 图表容器高度动态调整 */
.chart-container-card.expanded-chart .chart-container {
    height: 700px !important;
    transition: height 0.3s ease;
}

.chart-container-card .chart-container {
    height: 400px;
    transition: height 0.3s ease;
}

/* 图表区域高度动态调整 */
.chart-container-card.expanded-chart .chart-area {
    height: 587px;
    transition: height 0.3s ease;
}

.chart-container-card .chart-area {
    height: 300px;
    transition: height 0.3s ease;
}

/* 响应式适配 */
@media (max-width: 992px) {
    .basic-stats {
        gap: 8px;
    }

    .basic-stat {
        font-size: 11px;
        padding: 1px 6px;
    }

    .fraction-collector-content.expanded {
        max-height: 500px;
    }
}

@media (max-width: 768px) {
    .header-left {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .basic-stats {
        gap: 6px;
        flex-wrap: wrap;
    }

    .basic-stat {
        font-size: 10px;
        padding: 1px 4px;
    }

    .rack-actions-panel .rack-actions {
        flex-wrap: wrap;
        justify-content: center;
    }

    .fraction-collector-content.expanded {
        max-height: 450px;
    }
}

@media (max-width: 576px) {
    .fraction-collector-header {
        padding: 12px 16px;
    }

    .rack-actions-panel {
        padding: 12px 16px;
    }

    .basic-stat {
        font-size: 9px;
        padding: 1px 3px;
    }

    .fraction-collector-content.expanded {
        max-height: 400px;
    }
}

/* 新增大按钮控制面板样式 */
.peak-overview-card {
    margin-bottom: 16px;
}

.peak-overview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.view-details-btn {
    color: #409eff;
    text-decoration: none;
}

.view-details-btn:hover {
    color: #337ecc;
}

.peak-overview-content {
    padding: 8px 0;
}

.peak-stats-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}

.peak-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}

.peak-stat .stat-value {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
}

.peak-stat .stat-label {
    font-size: 11px;
    color: #64748b;
    text-align: center;
}

/* 控制按钮卡片 */
.control-buttons-card {
    margin-top: 16px;
}

.control-buttons-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 8px 0;
}

.control-btn {
    min-height: 60px !important;
    width: 90% !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: 2px solid !important;
    transition: all 0.3s ease !important;
    position: relative;
    overflow: hidden;
}

.control-btn .btn-icon {
    font-size: 20px !important;
    display: flex;
    align-items: center;
    justify-content: center;
}

.control-btn .btn-text {
    font-size: 12px;
    line-height: 1.2;
    text-align: center;
    white-space: nowrap;
}

/* 按钮特定样式 */
.control-btn-primary {
    background: linear-gradient(135deg, #409eff 0%, #337ecc 100%) !important;
    border-color: #409eff !important;
    color: white !important;
}

.control-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3) !important;
}

.control-btn-warning {
    background: linear-gradient(135deg, #e6a23c 0%, #cf9236 100%) !important;
    border-color: #e6a23c !important;
    color: white !important;
}

.control-btn-warning:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(230, 162, 60, 0.3) !important;
}

.control-btn-success {
    background: linear-gradient(135deg, #67c23a 0%, #5daf34 100%) !important;
    border-color: #67c23a !important;
    color: white !important;
}

.control-btn-success:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(103, 194, 58, 0.3) !important;
}

.control-btn-danger {
    background: linear-gradient(135deg, #f56c6c 0%, #f04142 100%) !important;
    border-color: #f56c6c !important;
    color: white !important;
}

.control-btn-danger:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(245, 108, 108, 0.3) !important;
}

.control-btn-info {
    background: linear-gradient(135deg, #909399 0%, #82848a 100%) !important;
    border-color: #909399 !important;
    color: white !important;
}

.control-btn-info:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(144, 147, 153, 0.3) !important;
}

.control-btn-info.is-active {
    background: linear-gradient(135deg, #67c23a 0%, #5daf34 100%) !important;
    border-color: #67c23a !important;
}

.control-btn-gradient,
.control-btn-tube,
.control-btn-conditioning,
.control-btn-mock {
    background: white !important;
    border-color: #409eff !important;
    color: #409eff !important;
}

.control-btn-gradient:hover,
.control-btn-tube:hover,
.control-btn-conditioning:hover,
.control-btn-mock:hover {
    background: #409eff !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.2) !important;
}

.control-btn-clear {
    background: white !important;
    border-color: #e6a23c !important;
    color: #e6a23c !important;
}

.control-btn-clear:hover {
    background: #e6a23c !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(230, 162, 60, 0.2) !important;
}

.control-btn-mode {
    transition: all 0.3s ease !important;
}

.control-btn-mode:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
}

/* 弹窗内容样式 */
.gradient-dialog-content {
    padding: 16px 0;
}

.gradient-item {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    gap: 12px;
}

.gradient-item label {
    min-width: 60px;
    font-weight: 500;
    color: #606266;
}

.gradient-value {
    min-width: 45px;
    text-align: center;
    font-weight: 600;
    color: #409eff;
}

.tube-dialog-content {
    padding: 16px 0;
}

.current-tube-info {
    text-align: center;
    margin-bottom: 16px;
}

.tube-selection {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}

.tube-selection label {
    font-weight: 500;
    color: #606266;
}

/* 响应式适配 */
@media (max-width: 1200px) {
    .control-btn {
        min-height: 55px !important;
    }

    .control-btn .btn-icon {
        font-size: 18px !important;
    }

    .control-btn .btn-text {
        font-size: 11px;
    }
}

@media (max-width: 992px) {
    .control-buttons-grid {
        gap: 8px;
    }

    .control-btn {
        min-height: 50px !important;
    }

    .control-btn .btn-icon {
        font-size: 16px !important;
    }

    .control-btn .btn-text {
        font-size: 10px;
    }
}

/* Mock模式弹窗样式 */
.mock-mode-dialog-content {
    padding: 10px 0;
}

.mock-info {
    margin-bottom: 20px;
}

.device-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    margin-bottom: 10px;
    transition: all 0.3s ease;
}

.device-item:hover {
    border-color: #409eff;
    background-color: #f0f9ff;
}

.device-item.global-mock {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-color: #6c757d;
    font-weight: 600;
}

.device-item.global-mock:hover {
    border-color: #495057;
    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.device-info {
    display: flex;
    align-items: center;
    flex: 1;
}

.device-icon {
    font-size: 24px;
    margin-right: 15px;
    min-width: 24px;
}

.device-details h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    color: #303133;
}

.device-details p {
    margin: 0;
    font-size: 13px;
    color: #606266;
}

.devices-list {
    max-height: 300px;
    overflow-y: auto;
}

.loading-section {
    padding: 20px;
}

.empty-devices {
    text-align: center;
    padding: 40px 20px;
    color: #909399;
}
</style>
