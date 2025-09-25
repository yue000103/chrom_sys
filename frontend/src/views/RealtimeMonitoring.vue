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
                    <span
                        class="status-indicator"
                        :class="isPaused ? 'offline' : 'online'"
                    ></span>
                    <span class="status-text">{{
                        isPaused ? "待机" : "采集中"
                    }}</span>
                </div>
            </div>
            <div class="header-controls">
                <el-button
                    type="primary"
                    class="btn-gradient"
                    @click="togglePause"
                    :icon="isPaused ? 'VideoPlay' : 'VideoPause'"
                >
                    {{ isPaused ? "继续" : "暂停" }}
                </el-button>
                <el-button type="success" @click="restartChart" icon="Refresh">
                    重新开始
                </el-button>
                <el-button type="danger" icon="Close" @click="emergencyStop"
                    >停止</el-button
                >
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
                                            UV{{ wavelengths.uv1 }}：{{
                                                currentValues.uv254.toFixed(5)
                                            }}
                                        </template>
                                        <template
                                            v-else-if="series.key === 'uv280'"
                                        >
                                            UV{{ wavelengths.uv2 }}：{{
                                                currentValues.uv280.toFixed(5)
                                            }}
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-a'
                                            "
                                        >
                                            {{ series.label }}：{{
                                                gradientValues.solutionA
                                            }}%
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-b'
                                            "
                                        >
                                            {{ series.label }}：{{
                                                gradientValues.solutionB
                                            }}%
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-c'
                                            "
                                        >
                                            {{ series.label }}：{{
                                                gradientValues.solutionC
                                            }}%
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'gradient-d'
                                            "
                                        >
                                            {{ series.label }}：{{
                                                gradientValues.solutionD
                                            }}%
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'pressure'
                                            "
                                        >
                                            {{ series.label }}：{{
                                                currentValues.pressure.toFixed(
                                                    0
                                                )
                                            }}
                                        </template>
                                        <template
                                            v-else-if="
                                                series.key === 'flowRate'
                                            "
                                        >
                                            {{ series.label }}：12.0
                                        </template>
                                        <template v-else>
                                            {{ series.label }}
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

            <!-- 右侧：设备状态和控制面板 -->
            <el-col :span="5">
                <!-- 峰检测结果卡片 -->
                <div class="data-card peak-detection-card">
                    <div class="data-card-header">
                        <h3 class="data-card-title">峰检测结果</h3>
                        <div class="peak-controls">
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
                            <el-button
                                type="primary"
                                size="small"
                                @click="showPeakDialog = true"
                                icon="View"
                            >
                                查看详情 ({{ detectedPeaks.length }})
                            </el-button>
                        </div>
                    </div>

                    <div class="peak-summary-compact">
                        <div class="summary-stats">
                            <div class="stat-item">
                                <span class="stat-number">{{
                                    detectedPeaks.length
                                }}</span>
                                <span class="stat-label">已检测峰数</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number">{{
                                    currentBaseline.toFixed(3)
                                }}</span>
                                <span class="stat-label">基线 (AU)</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number">{{
                                    noiseLevel.toFixed(3)
                                }}</span>
                                <span class="stat-label">噪声 (AU)</span>
                            </div>
                        </div>
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

                <!-- 实时控制面板 -->
                <el-card class="control-panel-card">
                    <template #header>
                        <span>实时控制</span>
                    </template>

                    <div class="control-panel">
                        <!-- 试管控制 -->
                        <div class="control-section">
                            <h4>试管控制</h4>
                            <div class="control-row">
                                <el-select
                                    v-model="selectedTubeForSwitch"
                                    placeholder="选择试管"
                                >
                                    <el-option
                                        v-for="tube in availableTubes"
                                        :key="tube"
                                        :label="`试管 ${tube}`"
                                        :value="tube"
                                    />
                                </el-select>
                                <el-button
                                    @click="switchToTube"
                                    :disabled="!selectedTubeForSwitch"
                                >
                                    切换
                                </el-button>
                            </div>
                        </div>

                        <!-- 收集模式控制 -->
                        <div class="control-section">
                            <h4>收集模式</h4>
                            <el-radio-group
                                v-model="collectionMode"
                                @change="changeCollectionMode"
                            >
                                <el-radio label="收集">收集模式</el-radio>
                                <el-radio label="废液">废液模式</el-radio>
                            </el-radio-group>
                        </div>

                        <!-- 梯度调整 -->
                        <div class="control-section">
                            <h4>梯度调整</h4>
                            <div class="gradient-controls">
                                <div class="gradient-item">
                                    <label>执行时间:</label>
                                    <el-select
                                        v-model="selectedGradientTime"
                                        placeholder="选择时间"
                                        size="small"
                                        style="flex: 1"
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
                                    />
                                    <span>{{ gradientValues.solutionA }}%</span>
                                </div>
                                <div class="gradient-item">
                                    <label>原液B:</label>
                                    <el-slider
                                        v-model="gradientValues.solutionB"
                                        :max="100"
                                    />
                                    <span>{{ gradientValues.solutionB }}%</span>
                                </div>
                                <div class="gradient-item">
                                    <label>原液C:</label>
                                    <el-slider
                                        v-model="gradientValues.solutionC"
                                        :max="100"
                                    />
                                    <span>{{ gradientValues.solutionC }}%</span>
                                </div>
                                <div class="gradient-item">
                                    <label>原液D:</label>
                                    <el-slider
                                        v-model="gradientValues.solutionD"
                                        :max="100"
                                    />
                                    <span>{{ gradientValues.solutionD }}%</span>
                                </div>
                                <el-button
                                    type="primary"
                                    @click="applyGradientChange"
                                    :disabled="!selectedGradientTime"
                                    >确定</el-button
                                >
                            </div>
                        </div>
                    </div>
                </el-card>
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
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";
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
        } = useRealtimeChart(currentValues);

        // 包装restartChart方法，在重新开始时获取波长
        const restartChart = async () => {
            await originalRestartChart(fetchWavelengths);
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

        // 主要控制方法
        const togglePause = () => {
            isPaused.value = !isPaused.value;

            if (isPaused.value) {
                stopChart();
                console.log("图表已暂停");
            } else {
                startChart();
                console.log("图表继续运行");
            }
        };

        // 紧急停止
        const emergencyStop = () => {
            console.log("紧急停止");
            stopChart();
            isPaused.value = true;
            deviceEmergencyStop();
        };

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

        // 用户选择取消MQTT连接
        const handleMqttCancel = () => {
            showMqttConnectionDialog.value = false;
            mqttConnectionError.value = null;
            console.log("用户取消MQTT连接");
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
        });

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
            applyGradientChange,
            resetGradientValues,

            // 主要控制方法
            togglePause,
            restartChart,
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

            // MQTT连接失败处理
            showMqttConnectionDialog,
            mqttConnectionError,
            mqttReconnecting,
            handleMqttReconnect,
            handleMqttCancel,
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

.status-text {
    color: #333;
}

.header-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
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
    gap: 24px;
    flex-wrap: wrap;
}

.legend-checkbox {
    display: flex;
    align-items: center;
    margin-right: 0 !important;
}

.legend-checkbox .el-checkbox__input {
    margin-right: 8px;
}

.legend-checkbox .el-checkbox__label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding-left: 0;
    font-size: 13px;
    color: #333;
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    display: inline-block;
    flex-shrink: 0;
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

.legend-color.flowRate {
    background-color: #8b5cf6;
}

.legend-text {
    font-weight: 500;
    user-select: none;
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

.chromatogram-chart .flowRate-line {
    filter: drop-shadow(0 1px 2px rgba(139, 92, 246, 0.3));
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
    font-size: 12px;
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
    font-size: 12px;
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
</style>
