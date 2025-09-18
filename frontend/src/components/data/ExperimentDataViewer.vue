<template>
    <div class="experiment-data-viewer">
        <div class="viewer-header">
            <h3>{{ experiment.name }} - 数据详情</h3>
            <div class="header-actions">
                <el-button @click="exportData">
                    <el-icon><Download /></el-icon>
                    导出数据
                </el-button>
                <el-button @click="$emit('close')">
                    <el-icon><Close /></el-icon>
                    关闭
                </el-button>
            </div>
        </div>

        <el-tabs v-model="activeTab" type="border-card">
            <!-- 图表数据 -->
            <el-tab-pane label="色谱图" name="chart">
                <div class="chart-panel">
                    <div class="chart-controls">
                        <div class="control-group">
                            <label>显示数据:</label>
                            <el-checkbox-group
                                v-model="chartOptions.visibleData"
                            >
                                <el-checkbox label="uv">UV吸收</el-checkbox>
                                <el-checkbox label="pressure">压力</el-checkbox>
                                <el-checkbox label="gradient">梯度</el-checkbox>
                                <el-checkbox label="peaks">峰标记</el-checkbox>
                                <el-checkbox label="tubes"
                                    >试管标记</el-checkbox
                                >
                            </el-checkbox-group>
                        </div>

                        <div class="control-group">
                            <label>时间范围:</label>
                            <el-slider
                                v-model="chartOptions.timeRange"
                                range
                                :min="0"
                                :max="totalTime"
                                :format-tooltip="formatTime"
                            />
                        </div>

                        <div class="control-group">
                            <label>Y轴缩放:</label>
                            <el-slider
                                v-model="chartOptions.yScale"
                                :min="0.1"
                                :max="5"
                                :step="0.1"
                                :format-tooltip="formatScale"
                            />
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart-placeholder">
                            <el-icon class="chart-icon"
                                ><TrendCharts
                            /></el-icon>
                            <p>实验色谱图表</p>
                            <p class="chart-info">
                                {{ experiment.name }} 完整数据展示
                            </p>
                        </div>
                    </div>

                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-color uv"></span>
                            <span>UV吸收 (AU)</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color pressure"></span>
                            <span>压力 (bar)</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color gradient"></span>
                            <span>梯度 (%)</span>
                        </div>
                    </div>
                </div>
            </el-tab-pane>

            <!-- 峰数据 -->
            <el-tab-pane label="峰分析" name="peaks">
                <div class="peaks-panel">
                    <div class="peaks-header">
                        <h4>检测到的峰</h4>
                        <div class="peaks-stats">
                            <span
                                >总峰数:
                                <strong>{{ peakData.length }}</strong></span
                            >
                            <span
                                >有效峰:
                                <strong>{{ validPeaks.length }}</strong></span
                            >
                            <span
                                >平均峰宽:
                                <strong>{{ averagePeakWidth }}s</strong></span
                            >
                        </div>
                    </div>

                    <el-table
                        :data="peakData"
                        stripe
                        style="width: 100%"
                        max-height="400"
                        @row-click="selectPeak"
                    >
                        <el-table-column prop="id" label="峰号" width="60" />
                        <el-table-column
                            prop="retentionTime"
                            label="保留时间(min)"
                            width="120"
                        />
                        <el-table-column
                            prop="height"
                            label="峰高(AU)"
                            width="100"
                        />
                        <el-table-column
                            prop="area"
                            label="峰面积(AU·s)"
                            width="120"
                        />
                        <el-table-column
                            prop="width"
                            label="峰宽(s)"
                            width="100"
                        />
                        <el-table-column
                            prop="symmetry"
                            label="对称因子"
                            width="100"
                        />
                        <el-table-column
                            prop="tubeId"
                            label="收集试管"
                            width="100"
                        />
                        <el-table-column
                            prop="purity"
                            label="纯度(%)"
                            width="100"
                        />
                        <el-table-column prop="status" label="状态" width="100">
                            <template #default="scope">
                                <el-tag
                                    :type="getPeakStatusType(scope.row.status)"
                                    size="small"
                                >
                                    {{ getPeakStatusText(scope.row.status) }}
                                </el-tag>
                            </template>
                        </el-table-column>
                    </el-table>

                    <!-- 峰详情 -->
                    <div v-if="selectedPeak" class="peak-detail">
                        <el-card>
                            <template #header>
                                <span>峰 {{ selectedPeak.id }} 详细信息</span>
                            </template>

                            <div class="peak-info-grid">
                                <div class="info-section">
                                    <h5>基本参数</h5>
                                    <div class="info-items">
                                        <div class="info-item">
                                            <label>保留时间:</label>
                                            <span
                                                >{{
                                                    selectedPeak.retentionTime
                                                }}
                                                min</span
                                            >
                                        </div>
                                        <div class="info-item">
                                            <label>峰高:</label>
                                            <span
                                                >{{
                                                    selectedPeak.height
                                                }}
                                                AU</span
                                            >
                                        </div>
                                        <div class="info-item">
                                            <label>峰面积:</label>
                                            <span
                                                >{{
                                                    selectedPeak.area
                                                }}
                                                AU·s</span
                                            >
                                        </div>
                                        <div class="info-item">
                                            <label>峰宽:</label>
                                            <span
                                                >{{
                                                    selectedPeak.width
                                                }}
                                                s</span
                                            >
                                        </div>
                                    </div>
                                </div>

                                <div class="info-section">
                                    <h5>质量参数</h5>
                                    <div class="info-items">
                                        <div class="info-item">
                                            <label>对称因子:</label>
                                            <span>{{
                                                selectedPeak.symmetry
                                            }}</span>
                                        </div>
                                        <div class="info-item">
                                            <label>理论塔板数:</label>
                                            <span>{{
                                                selectedPeak.plates
                                            }}</span>
                                        </div>
                                        <div class="info-item">
                                            <label>分离度:</label>
                                            <span>{{
                                                selectedPeak.resolution
                                            }}</span>
                                        </div>
                                        <div class="info-item">
                                            <label>纯度:</label>
                                            <span
                                                >{{
                                                    selectedPeak.purity
                                                }}%</span
                                            >
                                        </div>
                                    </div>
                                </div>

                                <div class="info-section">
                                    <h5>收集信息</h5>
                                    <div class="info-items">
                                        <div class="info-item">
                                            <label>收集试管:</label>
                                            <span>{{
                                                selectedPeak.tubeId
                                            }}</span>
                                        </div>
                                        <div class="info-item">
                                            <label>收集体积:</label>
                                            <span
                                                >{{
                                                    selectedPeak.collectedVolume
                                                }}
                                                mL</span
                                            >
                                        </div>
                                        <div class="info-item">
                                            <label>收集开始:</label>
                                            <span>{{
                                                selectedPeak.collectionStart
                                            }}</span>
                                        </div>
                                        <div class="info-item">
                                            <label>收集结束:</label>
                                            <span>{{
                                                selectedPeak.collectionEnd
                                            }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </el-card>
                    </div>
                </div>
            </el-tab-pane>

            <!-- 原始数据 -->
            <el-tab-pane label="原始数据" name="raw">
                <div class="raw-data-panel">
                    <div class="data-controls">
                        <div class="control-group">
                            <label>数据类型:</label>
                            <el-select
                                v-model="rawDataOptions.dataType"
                                @change="loadRawData"
                            >
                                <el-option label="UV数据" value="uv" />
                                <el-option label="压力数据" value="pressure" />
                                <el-option label="梯度数据" value="gradient" />
                                <el-option
                                    label="温度数据"
                                    value="temperature"
                                />
                            </el-select>
                        </div>

                        <div class="control-group">
                            <label>时间范围:</label>
                            <el-date-picker
                                v-model="rawDataOptions.timeRange"
                                type="datetimerange"
                                range-separator="至"
                                start-placeholder="开始时间"
                                end-placeholder="结束时间"
                                format="HH:mm:ss"
                                value-format="HH:mm:ss"
                            />
                        </div>

                        <div class="control-group">
                            <label>采样间隔:</label>
                            <el-select v-model="rawDataOptions.interval">
                                <el-option label="0.1秒" value="0.1" />
                                <el-option label="1秒" value="1" />
                                <el-option label="5秒" value="5" />
                                <el-option label="10秒" value="10" />
                            </el-select>
                        </div>

                        <el-button @click="exportRawData">
                            <el-icon><Download /></el-icon>
                            导出原始数据
                        </el-button>
                    </div>

                    <div class="data-table">
                        <el-table
                            :data="rawData"
                            stripe
                            style="width: 100%"
                            max-height="500"
                            :loading="rawDataLoading"
                        >
                            <el-table-column
                                prop="timestamp"
                                label="时间戳"
                                width="120"
                            />
                            <el-table-column
                                prop="time"
                                label="相对时间"
                                width="100"
                            />
                            <el-table-column
                                prop="value"
                                label="数值"
                                width="120"
                            />
                            <el-table-column
                                prop="unit"
                                label="单位"
                                width="80"
                            />
                            <el-table-column
                                prop="quality"
                                label="数据质量"
                                width="100"
                            >
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            getQualityType(scope.row.quality)
                                        "
                                        size="small"
                                    >
                                        {{ scope.row.quality }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                        </el-table>

                        <div class="data-pagination">
                            <el-pagination
                                v-model:current-page="
                                    rawDataPagination.currentPage
                                "
                                v-model:page-size="rawDataPagination.pageSize"
                                :page-sizes="[50, 100, 200, 500]"
                                :total="rawDataPagination.total"
                                layout="total, sizes, prev, pager, next, jumper"
                            />
                        </div>
                    </div>
                </div>
            </el-tab-pane>

            <!-- 方法参数 -->
            <el-tab-pane label="方法参数" name="method">
                <div class="method-panel">
                    <div class="method-info">
                        <h4>使用方法: {{ experiment.method }}</h4>

                        <el-divider content-position="left"
                            >基本参数</el-divider
                        >
                        <div class="params-grid">
                            <div class="param-item">
                                <label>流速:</label>
                                <span>{{ methodParams.flowRate }} mL/min</span>
                            </div>
                            <div class="param-item">
                                <label>检测波长:</label>
                                <span>{{ methodParams.wavelength }} nm</span>
                            </div>
                            <div class="param-item">
                                <label>柱温:</label>
                                <span>{{ methodParams.temperature }} °C</span>
                            </div>
                            <div class="param-item">
                                <label>进样量:</label>
                                <span
                                    >{{ methodParams.injectionVolume }} μL</span
                                >
                            </div>
                        </div>

                        <el-divider content-position="left"
                            >梯度程序</el-divider
                        >
                        <el-table
                            :data="methodParams.gradientProgram"
                            style="width: 100%"
                        >
                            <el-table-column
                                prop="time"
                                label="时间(min)"
                                width="100"
                            />
                            <el-table-column
                                prop="solutionA"
                                label="原液A(%)"
                                width="100"
                            />
                            <el-table-column
                                prop="solutionB"
                                label="原液B(%)"
                                width="100"
                            />
                            <el-table-column
                                prop="solutionC"
                                label="原液C(%)"
                                width="100"
                            />
                            <el-table-column
                                prop="solutionD"
                                label="原液D(%)"
                                width="100"
                            />
                            <el-table-column
                                prop="flowRate"
                                label="流速(mL/min)"
                                width="120"
                            />
                        </el-table>

                        <el-divider content-position="left"
                            >收集参数</el-divider
                        >
                        <div class="params-grid">
                            <div class="param-item">
                                <label>收集策略:</label>
                                <span>{{
                                    methodParams.collectionStrategy
                                }}</span>
                            </div>
                            <div class="param-item">
                                <label>收集体积:</label>
                                <span
                                    >{{
                                        methodParams.collectionVolume
                                    }}
                                    mL</span
                                >
                            </div>
                            <div class="param-item">
                                <label>清洗体积:</label>
                                <span>{{ methodParams.washVolume }} mL</span>
                            </div>
                            <div class="param-item">
                                <label>清洗次数:</label>
                                <span>{{ methodParams.washCycles }} 次</span>
                            </div>
                        </div>
                    </div>
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";

export default {
    name: "ExperimentDataViewer",
    props: {
        experiment: {
            type: Object,
            required: true,
        },
    },
    emits: ["close"],
    setup(props) {
        const activeTab = ref("chart");
        const selectedPeak = ref(null);
        const rawDataLoading = ref(false);

        // 图表选项
        const chartOptions = ref({
            visibleData: ["uv", "gradient", "peaks", "tubes"],
            timeRange: [0, 45],
            yScale: 1.0,
        });

        // 原始数据选项
        const rawDataOptions = ref({
            dataType: "uv",
            timeRange: null,
            interval: "1",
        });

        // 原始数据分页
        const rawDataPagination = ref({
            currentPage: 1,
            pageSize: 100,
            total: 2700,
        });

        const totalTime = computed(() => 45); // 45分钟

        // 峰数据
        const peakData = ref([
            {
                id: 1,
                retentionTime: 5.2,
                height: 0.485,
                area: 24.3,
                width: 15.2,
                symmetry: 1.05,
                tubeId: 1,
                purity: 95.2,
                status: "valid",
                plates: 15420,
                resolution: 2.3,
                collectedVolume: 5.2,
                collectionStart: "14:32:15",
                collectionEnd: "14:33:08",
            },
            {
                id: 2,
                retentionTime: 8.7,
                height: 0.332,
                area: 18.6,
                width: 18.4,
                symmetry: 1.12,
                tubeId: 2,
                purity: 88.7,
                status: "valid",
                plates: 12350,
                resolution: 1.8,
                collectedVolume: 4.8,
                collectionStart: "14:38:42",
                collectionEnd: "14:39:28",
            },
            {
                id: 3,
                retentionTime: 12.1,
                height: 0.678,
                area: 35.2,
                width: 22.1,
                symmetry: 0.98,
                tubeId: 3,
                purity: 97.5,
                status: "valid",
                plates: 18930,
                resolution: 2.7,
                collectedVolume: 6.1,
                collectionStart: "14:45:06",
                collectionEnd: "14:46:12",
            },
        ]);

        // 有效峰
        const validPeaks = computed(() => {
            return peakData.value.filter((peak) => peak.status === "valid");
        });

        // 平均峰宽
        const averagePeakWidth = computed(() => {
            const total = validPeaks.value.reduce(
                (sum, peak) => sum + peak.width,
                0
            );
            return (total / validPeaks.value.length).toFixed(1);
        });

        // 方法参数
        const methodParams = ref({
            flowRate: 1.0,
            wavelength: 254,
            temperature: 25,
            injectionVolume: 20,
            collectionStrategy: "峰驱动",
            collectionVolume: 5.0,
            washVolume: 5.0,
            washCycles: 1,
            gradientProgram: [
                {
                    time: 0,
                    solutionA: 80,
                    solutionB: 20,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
                {
                    time: 10,
                    solutionA: 60,
                    solutionB: 40,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
                {
                    time: 25,
                    solutionA: 20,
                    solutionB: 80,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
                {
                    time: 35,
                    solutionA: 0,
                    solutionB: 100,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
                {
                    time: 45,
                    solutionA: 80,
                    solutionB: 20,
                    solutionC: 0,
                    solutionD: 0,
                    flowRate: 1.0,
                },
            ],
        });

        // 原始数据
        const rawData = ref([]);

        const formatTime = (value) => {
            return `${value}min`;
        };

        const formatScale = (value) => {
            return `${value}x`;
        };

        const getPeakStatusType = (status) => {
            const statusMap = {
                valid: "success",
                invalid: "danger",
                uncertain: "warning",
            };
            return statusMap[status] || "info";
        };

        const getPeakStatusText = (status) => {
            const statusMap = {
                valid: "有效",
                invalid: "无效",
                uncertain: "不确定",
            };
            return statusMap[status] || status;
        };

        const getQualityType = (quality) => {
            const qualityMap = {
                excellent: "success",
                good: "success",
                fair: "warning",
                poor: "danger",
            };
            return qualityMap[quality] || "info";
        };

        const selectPeak = (peak) => {
            selectedPeak.value = peak;
        };

        const loadRawData = () => {
            rawDataLoading.value = true;

            setTimeout(() => {
                // 模拟生成原始数据
                const data = [];
                for (let i = 0; i < 100; i++) {
                    data.push({
                        timestamp: `14:${30 + Math.floor(i / 60)}:${(i % 60)
                            .toString()
                            .padStart(2, "0")}`,
                        time: `${(i * 0.1).toFixed(1)}s`,
                        value: (Math.random() * 0.5 + 0.1).toFixed(4),
                        unit:
                            rawDataOptions.value.dataType === "uv"
                                ? "AU"
                                : rawDataOptions.value.dataType === "pressure"
                                ? "bar"
                                : rawDataOptions.value.dataType ===
                                  "temperature"
                                ? "°C"
                                : "%",
                        quality: Math.random() > 0.1 ? "good" : "fair",
                    });
                }
                rawData.value = data;
                rawDataLoading.value = false;
            }, 1000);
        };

        const exportData = () => {
            console.log("导出实验数据");
        };

        const exportRawData = () => {
            console.log("导出原始数据");
        };

        onMounted(() => {
            loadRawData();
            if (peakData.value.length > 0) {
                selectedPeak.value = peakData.value[0];
            }
        });

        return {
            activeTab,
            selectedPeak,
            rawDataLoading,
            chartOptions,
            rawDataOptions,
            rawDataPagination,
            totalTime,
            peakData,
            validPeaks,
            averagePeakWidth,
            methodParams,
            rawData,
            formatTime,
            formatScale,
            getPeakStatusType,
            getPeakStatusText,
            getQualityType,
            selectPeak,
            loadRawData,
            exportData,
            exportRawData,
        };
    },
};
</script>

<style scoped>
.experiment-data-viewer {
    padding: 20px;
}

.viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.viewer-header h3 {
    margin: 0;
    color: #333;
}

.header-actions {
    display: flex;
    gap: 8px;
}

.chart-panel,
.peaks-panel,
.raw-data-panel,
.method-panel {
    padding: 20px;
}

.chart-controls,
.data-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.control-group label {
    font-size: 14px;
    color: #666;
    white-space: nowrap;
}

.chart-container {
    height: 400px;
    background-color: #f8f9fa;
    border: 1px dashed #dcdfe6;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    margin-bottom: 20px;
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

.chart-legend {
    display: flex;
    gap: 20px;
    justify-content: center;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
}

.legend-color.uv {
    background-color: #409eff;
}

.legend-color.pressure {
    background-color: #f56c6c;
}

.legend-color.gradient {
    background-color: #67c23a;
}

.peaks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.peaks-header h4 {
    margin: 0;
    color: #333;
}

.peaks-stats {
    display: flex;
    gap: 16px;
    font-size: 14px;
    color: #666;
}

.peak-detail {
    margin-top: 20px;
}

.peak-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.info-section h5 {
    margin: 0 0 12px 0;
    color: #666;
    font-size: 14px;
    border-bottom: 1px solid #ebeef5;
    padding-bottom: 4px;
}

.info-items {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.info-item label {
    color: #666;
    font-weight: 500;
}

.data-table {
    margin-top: 20px;
}

.data-pagination {
    margin-top: 20px;
    text-align: center;
}

.method-info h4 {
    margin: 0 0 20px 0;
    color: #333;
}

.params-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}

.param-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.param-item label {
    color: #666;
    font-weight: 500;
}
</style>
