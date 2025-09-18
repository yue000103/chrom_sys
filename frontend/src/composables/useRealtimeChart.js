import { ref, computed, nextTick, onMounted, onUnmounted } from "vue";
import * as d3 from "d3";
import mqttService from '../services/mqtt-service.js';

export function useRealtimeChart(currentValues) {
    // 响应式状态
    const chartContainer = ref(null);
    const d3Chart = ref(null);
    const timeRange = ref("30");

    // D3图表相关变量
    let svg = null;
    let xScale = null;
    let yScaleLeft = null; // 左侧Y轴 (UV信号)
    let yScaleRight = null; // 右侧Y轴 (原液百分比)
    let uv254Line = null; // UV254nm数据线
    let uv280Line = null; // UV280nm数据线
    let gradientLines = {}; // 原液数据线集合
    let chartData = [];
    let isChartRunning = false;
    let chartStartTime = 0;
    let lastUpdateTime = 0;
    let resizeObserver = null;

    // 动态范围追踪
    let uvDataRange = { min: 0, max: 1 };
    let gradientDataRange = { min: 0, max: 100 };

    // MQTT连接状态
    let mqttConnected = false;
    let mqttSubscribed = false;

    // 缓存键名
    const CHART_CACHE_KEY = 'chromatography_chart_data';

    // 计算数据范围
    const calculateDataRanges = (data) => {
        if (!data || data.length === 0) return;

        // 计算UV数据范围（两个波长的合并范围）
        const uvValues = [];
        const gradientValues = [];

        data.forEach(point => {
            if (point.uv254 !== undefined && point.uv254 !== null) uvValues.push(point.uv254);
            if (point.uv280 !== undefined && point.uv280 !== null) uvValues.push(point.uv280);

            ['gradient-a', 'gradient-b', 'gradient-c', 'gradient-d'].forEach(key => {
                if (point[key] !== undefined && point[key] !== null) {
                    gradientValues.push(point[key]);
                }
            });
        });

        if (uvValues.length > 0) {
            const uvMin = Math.min(...uvValues);
            const uvMax = Math.max(...uvValues);
            const uvPadding = (uvMax - uvMin) * 0.1 || 0.1; // 10% padding or 0.1 minimum

            uvDataRange.min = Math.max(0, uvMin - uvPadding);
            uvDataRange.max = uvMax + uvPadding;
        }

        if (gradientValues.length > 0) {
            const gradMin = Math.min(...gradientValues);
            const gradMax = Math.max(...gradientValues);

            // 对于原液百分比，使用固定的padding而不是比例padding
            // 这样可以确保刻度对齐
            const gradPadding = 2; // 固定2%的padding

            gradientDataRange.min = Math.max(0, gradMin - gradPadding);
            gradientDataRange.max = Math.min(100, gradMax + gradPadding);

            // 确保范围至少有一定的跨度，便于观察
            if (gradientDataRange.max - gradientDataRange.min < 10) {
                const center = (gradientDataRange.max + gradientDataRange.min) / 2;
                gradientDataRange.min = Math.max(0, center - 5);
                gradientDataRange.max = Math.min(100, center + 5);
            }
        }
    };

    // 更新Y轴比例尺
    const updateYScales = () => {
        if (!yScaleLeft || !yScaleRight) return;

        // 更新左侧Y轴（UV信号）
        yScaleLeft.domain([uvDataRange.min, uvDataRange.max]);

        // 更新右侧Y轴（原液百分比）
        yScaleRight.domain([gradientDataRange.min, gradientDataRange.max]);

        // 更新坐标轴
        if (svg) {
            svg.select(".y-axis-left")
               .transition()
               .duration(300)
               .call(d3.axisLeft(yScaleLeft).tickFormat((d) => `${d.toFixed(3)}`));

            svg.select(".y-axis-right")
               .transition()
               .duration(300)
               .call(d3.axisRight(yScaleRight)
                    .tickFormat((d) => `${d.toFixed(0)}%`)
                    .ticks(Math.max(3, Math.min(8, Math.floor((gradientDataRange.max - gradientDataRange.min) / 10)))));
        }
    };

    // 图表系列配置
    const chartSeries = ref([
        {
            key: "uv254",
            label: "UV254nm (mAU)",
            visible: true,
        },
        {
            key: "uv280",
            label: "UV280nm (mAU)",
            visible: true,
        },
        {
            key: "gradient-a",
            label: "原液A (%)",
            visible: true,
        },
        {
            key: "gradient-b",
            label: "原液B (%)",
            visible: true,
        },
        {
            key: "gradient-c",
            label: "原液C (%)",
            visible: false,
        },
        {
            key: "gradient-d",
            label: "原液D (%)",
            visible: false,
        },
    ]);

    // 检测器配置
    const detectors = ref([{ name: "UV", active: true }]);

    // D3图表初始化
    const initChart = () => {
        if (!d3Chart.value) return;

        const margin = { top: 20, right: 80, bottom: 40, left: 60 };

        // 动态获取容器宽度
        const containerWidth = d3Chart.value.parentElement?.clientWidth || 800;
        const containerHeight = d3Chart.value.parentElement?.clientHeight || 300;

        const width = containerWidth - margin.left - margin.right;
        const height = containerHeight - margin.bottom - margin.top;

        // 清除现有内容
        d3.select(d3Chart.value).selectAll("*").remove();

        // 创建SVG
        svg = d3
            .select(d3Chart.value)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // 创建比例尺
        xScale = d3
            .scaleLinear()
            .domain([0, 30]) // 固定30分钟范围
            .range([0, width]);

        // 左侧Y轴 - UV信号（初始范围，后续会动态调整）
        yScaleLeft = d3
            .scaleLinear()
            .domain([uvDataRange.min, uvDataRange.max])
            .range([height, 0]);

        // 右侧Y轴 - 原液百分比（初始范围，后续会动态调整）
        yScaleRight = d3
            .scaleLinear()
            .domain([gradientDataRange.min, gradientDataRange.max])
            .range([height, 0]);

        // 创建坐标轴
        const xAxis = d3
            .axisBottom(xScale)
            .tickFormat((d) => `${d.toFixed(1)}min`);

        const yAxisLeft = d3
            .axisLeft(yScaleLeft)
            .tickFormat((d) => `${d.toFixed(3)}`);

        const yAxisRight = d3.axisRight(yScaleRight)
            .tickFormat((d) => `${d.toFixed(0)}%`)
            .ticks(Math.max(3, Math.min(8, Math.floor((gradientDataRange.max - gradientDataRange.min) / 10))));

        // 添加坐标轴
        g.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(xAxis);

        g.append("g").attr("class", "y-axis-left").call(yAxisLeft);

        g.append("g")
            .attr("class", "y-axis-right")
            .attr("transform", `translate(${width},0)`)
            .call(yAxisRight);

        // 添加坐标轴标签
        g.append("text")
            .attr("class", "x-label")
            .attr("text-anchor", "middle")
            .attr("x", width / 2)
            .attr("y", height + 35)
            .text("时间 (min)");

        g.append("text")
            .attr("class", "y-label-left")
            .attr("text-anchor", "middle")
            .attr("transform", "rotate(-90)")
            .attr("y", -40)
            .attr("x", -height / 2)
            .text("UV信号 (mAU)");

        g.append("text")
            .attr("class", "y-label-right")
            .attr("text-anchor", "middle")
            .attr("transform", "rotate(-90)")
            .attr("y", width + 70)
            .attr("x", -height / 2)
            .text("原液 (%)");

        // 创建线条生成器
        uv254Line = d3
            .line()
            .x((d) => xScale(d.time))
            .y((d) => yScaleLeft(d.uv254))
            .curve(d3.curveLinear);

        uv280Line = d3
            .line()
            .x((d) => xScale(d.time))
            .y((d) => yScaleLeft(d.uv280))
            .curve(d3.curveLinear);

        // 为每个原液创建线条生成器
        const gradientKeys = [
            "gradient-a",
            "gradient-b",
            "gradient-c",
            "gradient-d",
        ];
        gradientKeys.forEach((key) => {
            gradientLines[key] = d3
                .line()
                .x((d) => xScale(d.time))
                .y((d) => yScaleRight(d[key]))
                .curve(d3.curveLinear);
        });

        // 添加UV254nm数据线条路径
        g.append("path")
            .attr("class", "uv254-line")
            .attr("fill", "none")
            .attr("stroke", "#2563eb")
            .attr("stroke-width", 2);

        // 添加UV280nm数据线条路径
        g.append("path")
            .attr("class", "uv280-line")
            .attr("fill", "none")
            .attr("stroke", "#06b6d4")
            .attr("stroke-width", 2);

        // 添加原液数据线条路径
        const gradientColors = {
            "gradient-a": "#f56c6c",
            "gradient-b": "#67c23a",
            "gradient-c": "#e6a23c",
            "gradient-d": "#909399",
        };

        gradientKeys.forEach((key) => {
            g.append("path")
                .attr("class", `${key}-line`)
                .attr("fill", "none")
                .attr("stroke", gradientColors[key])
                .attr("stroke-width", 1.5)
                .attr("opacity", 0.8);
        });

        // 添加窗口大小变化监听
        setupResizeObserver();
    };

    // 设置resize observer
    const setupResizeObserver = () => {
        if (typeof ResizeObserver !== 'undefined' && d3Chart.value?.parentElement) {
            // 清理之前的observer
            if (resizeObserver) {
                resizeObserver.disconnect();
            }

            resizeObserver = new ResizeObserver(() => {
                // 防抖处理
                clearTimeout(window.chartResizeTimeout);
                window.chartResizeTimeout = setTimeout(() => {
                    if (svg) {
                        resizeChart();
                    }
                }, 150);
            });

            resizeObserver.observe(d3Chart.value.parentElement);
        }
    };

    // 图表resize方法
    const resizeChart = () => {
        if (!d3Chart.value || !svg) return;

        const margin = { top: 20, right: 80, bottom: 40, left: 60 };
        const containerWidth = d3Chart.value.parentElement?.clientWidth || 800;
        const containerHeight = d3Chart.value.parentElement?.clientHeight || 300;

        const width = containerWidth - margin.left - margin.right;
        const height = containerHeight - margin.bottom - margin.top;

        // 更新SVG尺寸
        svg.attr("width", width + margin.left + margin.right)
           .attr("height", height + margin.top + margin.bottom);

        // 更新比例尺
        xScale.range([0, width]);
        yScaleLeft.domain([uvDataRange.min, uvDataRange.max]).range([height, 0]);
        yScaleRight.domain([gradientDataRange.min, gradientDataRange.max]).range([height, 0]);

        // 更新轴
        svg.select(".x-axis")
           .attr("transform", `translate(0,${height})`)
           .call(d3.axisBottom(xScale).tickFormat((d) => `${d.toFixed(1)}min`));

        svg.select(".y-axis-left")
           .call(d3.axisLeft(yScaleLeft).tickFormat((d) => `${d.toFixed(3)}`));

        svg.select(".y-axis-right")
           .attr("transform", `translate(${width},0)`)
           .call(d3.axisRight(yScaleRight).tickFormat((d) => `${d}%`));

        // 更新轴标签位置
        svg.select(".x-label")
           .attr("x", width / 2)
           .attr("y", height + 35);

        svg.select(".y-label-left")
           .attr("x", -height / 2);

        svg.select(".y-label-right")
           .attr("y", width + 70)
           .attr("x", -height / 2);

        // 更新线条生成器
        uv254Line.x((d) => xScale(d.time)).y((d) => yScaleLeft(d.uv254));
        uv280Line.x((d) => xScale(d.time)).y((d) => yScaleLeft(d.uv280));

        Object.keys(gradientLines).forEach(key => {
            gradientLines[key].x((d) => xScale(d.time)).y((d) => yScaleRight(d[key]));
        });

        // 重绘所有线条
        redrawLines();
    };

    // 重绘所有线条
    const redrawLines = () => {
        if (!svg || !chartData.length) return;

        const currentTime = (Date.now() - chartStartTime) / 1000 / 60;
        const timeIndex = Math.floor(currentTime / 0.1);
        const currentUVData = chartData.slice(0, timeIndex + 1);

        // 重绘UV线条
        const uv254Series = chartSeries.value.find((s) => s.key === "uv254");
        if (uv254Series && uv254Series.visible) {
            svg.select(".uv254-line").datum(currentUVData).attr("d", uv254Line);
        }

        const uv280Series = chartSeries.value.find((s) => s.key === "uv280");
        if (uv280Series && uv280Series.visible) {
            svg.select(".uv280-line").datum(currentUVData).attr("d", uv280Line);
        }

        // 重绘原液线条
        Object.keys(gradientLines).forEach(key => {
            const series = chartSeries.value.find((s) => s.key === key);
            if (series && series.visible) {
                svg.select(`.${key}-line`).datum(chartData).attr("d", gradientLines[key]);
            }
        });
    };

    // 生成完整的原液数据
    const generateGradientData = () => {
        chartData = [];
        // 生成0-30分钟的原液数据点，每0.1分钟一个点
        for (let time = 0; time <= 30; time += 0.1) {
            chartData.push({
                time: time,
                uv254: 0.156, // 初始UV254nm值
                uv280: 0.132, // 初始UV280nm值
                "gradient-a": 80, // 原液A恒定80%
                "gradient-b": 20, // 原液B恒定20%
                "gradient-c": 0, // 原液C恒定0%
                "gradient-d": 0, // 原液D恒定0%
            });
        }

        // 计算初始数据范围
        calculateDataRanges(chartData);

        // 立即更新图表显示原液线条
        updateGradientLines();
    };

    // 更新原液线条
    const updateGradientLines = () => {
        if (!svg) return;

        const gradientKeys = [
            "gradient-a",
            "gradient-b",
            "gradient-c",
            "gradient-d",
        ];

        gradientKeys.forEach((key) => {
            const series = chartSeries.value.find((s) => s.key === key);
            const lineElement = svg.select(`.${key}-line`);

            if (series && series.visible) {
                lineElement
                    .datum(chartData)
                    .attr("d", gradientLines[key])
                    .attr("opacity", 0.8);
            } else {
                lineElement.attr("opacity", 0);
            }
        });
    };

    // 开始图表
    const startChart = () => {
        // 尝试从缓存中恢复数据
        const cachedData = loadChartDataFromCache();

        if (cachedData && cachedData.chartData.length > 0) {
            // 恢复缓存的数据
            chartData = cachedData.chartData;
            chartStartTime = cachedData.chartStartTime;
            lastUpdateTime = cachedData.lastUpdateTime;
            uvDataRange = cachedData.uvDataRange || { min: 0, max: 1 };
            gradientDataRange = cachedData.gradientDataRange || { min: 0, max: 100 };
            console.log("从缓存恢复图表数据", chartData.length, "个数据点");
        } else {
            // 首次启动或无缓存数据
            chartData = [];
            chartStartTime = Date.now();
            lastUpdateTime = 0;
            uvDataRange = { min: 0, max: 1 };
            gradientDataRange = { min: 0, max: 100 };

            // 立即生成完整的原液数据（0-30分钟）
            generateGradientData();
        }

        isChartRunning = true;

        // 连接MQTT并订阅UV数据
        connectToMQTT();

        console.log("图表开始绘制");
    };

    // 停止图表
    const stopChart = () => {
        isChartRunning = false;

        // 保存数据到缓存
        saveChartDataToCache();

        // 断开MQTT连接
        disconnectFromMQTT();

        console.log("图表停止绘制");
    };

    // 重新开始图表
    const restartChart = () => {
        startChart();
    };

    // 更新图表
    const updateChart = () => {
        if (!isChartRunning || !svg) return;

        const currentTime = (Date.now() - chartStartTime) / 1000 / 60; // 转换为分钟

        // 只更新当前时间点的UV数据
        if (currentTime <= 30) {
            // 找到对应时间点的数据并更新UV值
            const timeIndex = Math.floor(currentTime / 0.1);
            if (timeIndex < chartData.length) {
                // UV值通过MQTT实时更新，这里不再模拟
                // 保持现有的UV值，如果没有MQTT数据则使用默认值
                if (!mqttConnected) {
                    chartData[timeIndex].uv254 = currentValues.value.uv254 || currentValues.value.uv;
                    chartData[timeIndex].uv280 = currentValues.value.uv280 || (currentValues.value.uv * 0.85);
                }
            }

            // 创建仅包含到当前时间的数据片段用于UV线条绘制
            const currentUVData = chartData.slice(0, timeIndex + 1);

            // 重新计算数据范围并更新Y轴（每10个数据点更新一次，避免过于频繁）
            if (timeIndex % 10 === 0 || timeIndex < 50) {
                calculateDataRanges(currentUVData);
                updateYScales();
            }

            // 固定时间轴范围为[0,30]分钟
            xScale.domain([0, 30]);

            // 更新x轴（保持固定范围）
            svg.select(".x-axis").call(
                d3.axisBottom(xScale).tickFormat((d) => `${d.toFixed(1)}min`)
            );

            // 更新UV254nm数据线（只显示到当前时间）
            const uv254Series = chartSeries.value.find((s) => s.key === "uv254");
            if (uv254Series && uv254Series.visible) {
                svg.select(".uv254-line")
                    .datum(currentUVData)
                    .transition()
                    .duration(100)
                    .attr("d", uv254Line)
                    .attr("opacity", 1);
            } else {
                svg.select(".uv254-line").attr("opacity", 0);
            }

            // 更新UV280nm数据线（只显示到当前时间）
            const uv280Series = chartSeries.value.find((s) => s.key === "uv280");
            if (uv280Series && uv280Series.visible) {
                svg.select(".uv280-line")
                    .datum(currentUVData)
                    .transition()
                    .duration(100)
                    .attr("d", uv280Line)
                    .attr("opacity", 1);
            } else {
                svg.select(".uv280-line").attr("opacity", 0);
            }

            // 原液线条已经在开始时绘制完成，不需要重复更新
        }
    };

    // 切换图表系列显示
    const toggleSeries = (seriesKey) => {
        const series = chartSeries.value.find((s) => s.key === seriesKey);
        if (series && svg) {
            console.log(`切换图表系列 ${seriesKey}:`, series.visible);

            // 立即更新图表线条的可见性
            if (seriesKey === "uv254") {
                svg.select(".uv254-line")
                    .transition()
                    .duration(200)
                    .attr("opacity", series.visible ? 1 : 0);
            } else if (seriesKey === "uv280") {
                svg.select(".uv280-line")
                    .transition()
                    .duration(200)
                    .attr("opacity", series.visible ? 1 : 0);
            } else if (seriesKey.startsWith("gradient-")) {
                svg.select(`.${seriesKey}-line`)
                    .transition()
                    .duration(200)
                    .attr("opacity", series.visible ? 0.8 : 0);
            }
        }
    };

    // 切换检测器
    const switchDetector = (detectorName) => {
        detectors.value.forEach((detector) => {
            detector.active = detector.name === detectorName;
        });
        console.log("切换检测器:", detectorName);
    };

    // 更新时间范围
    const updateTimeRange = () => {
        console.log("更新时间范围:", timeRange.value);
    };

    // 重置缩放
    const resetZoom = () => {
        console.log("重置图表缩放");
    };

    // 导出图表
    const exportChart = () => {
        console.log("导出图表");
    };

    // 运行时间计算
    const startTime = ref(new Date(Date.now() - 18 * 60 * 1000)); // 18分钟前开始
    const runningTime = computed(() => {
        const elapsed = Date.now() - startTime.value.getTime();
        const minutes = Math.floor(elapsed / (60 * 1000));
        const seconds = Math.floor((elapsed % (60 * 1000)) / 1000);
        return `${minutes}:${seconds.toString().padStart(2, "0")}`;
    });

    // 清理资源
    const cleanup = () => {
        // 断开MQTT连接
        disconnectFromMQTT();

        // 保存数据到缓存
        if (isChartRunning) {
            saveChartDataToCache();
        }

        if (resizeObserver) {
            resizeObserver.disconnect();
            resizeObserver = null;
        }
        if (window.chartResizeTimeout) {
            clearTimeout(window.chartResizeTimeout);
        }
    };

    // 组件卸载时清理
    onUnmounted(() => {
        cleanup();
    });

    // MQTT连接和数据接收函数
    const connectToMQTT = async () => {
        try {
            if (!mqttConnected) {
                await mqttService.connect();
                mqttConnected = true;
                console.log('MQTT服务连接成功');
            }

            if (!mqttSubscribed) {
                // 订阅UV检测器信号主题
                await mqttService.subscribe('chromatography/detector/detector_1/signal', handleUVSignalData);
                mqttSubscribed = true;
                console.log('已订阅UV信号主题: chromatography/detector/detector_1/signal');
            }
        } catch (error) {
            console.error('MQTT连接失败:', error);
            mqttConnected = false;
        }
    };

    const disconnectFromMQTT = async () => {
        try {
            if (mqttSubscribed) {
                await mqttService.unsubscribe('chromatography/detector/detector_1/signal');
                mqttSubscribed = false;
                console.log('已取消订阅UV信号主题');
            }
        } catch (error) {
            console.error('MQTT断开失败:', error);
        }
    };

    // 处理UV信号数据
    const handleUVSignalData = (data) => {
        try {
            console.log('收到UV信号数据:', data);

            // 数据格式应该是数组 [uv254_value, uv280_value]
            if (Array.isArray(data) && data.length >= 2) {
                const uv254Value = parseFloat(data[0]);
                const uv280Value = parseFloat(data[1]);

                // 更新当前时间点的数据
                const currentTime = (Date.now() - chartStartTime) / 1000 / 60; // 转换为分钟

                if (currentTime <= 30 && isChartRunning) {
                    const timeIndex = Math.floor(currentTime / 0.1);

                    if (timeIndex < chartData.length) {
                        // 更新UV数据
                        chartData[timeIndex].uv254 = uv254Value;
                        chartData[timeIndex].uv280 = uv280Value;

                        // 更新设备状态中的当前值
                        if (currentValues.value) {
                            currentValues.value.uv254 = uv254Value;
                            currentValues.value.uv280 = uv280Value;
                            currentValues.value.uv = uv254Value; // 保持兼容性
                        }

                        // 每10个数据点更新一次范围和图表
                        if (timeIndex % 10 === 0 || timeIndex < 50) {
                            const currentUVData = chartData.slice(0, timeIndex + 1);
                            calculateDataRanges(currentUVData);
                            updateYScales();
                        }

                        // 保存到缓存
                        saveChartDataToCache();

                        console.log(`UV数据更新 - 时间: ${currentTime.toFixed(1)}min, UV254: ${uv254Value}, UV280: ${uv280Value}`);
                    }
                }
            } else {
                console.warn('UV信号数据格式不正确，期望数组格式 [uv254, uv280]:', data);
            }
        } catch (error) {
            console.error('处理UV信号数据时出错:', error);
        }
    };

    // 缓存管理函数
    const saveChartDataToCache = () => {
        try {
            const cacheData = {
                chartData: chartData,
                chartStartTime: chartStartTime,
                lastUpdateTime: lastUpdateTime,
                uvDataRange: uvDataRange,
                gradientDataRange: gradientDataRange,
                timestamp: Date.now()
            };
            localStorage.setItem(CHART_CACHE_KEY, JSON.stringify(cacheData));
        } catch (error) {
            console.warn('保存图表数据到缓存失败:', error);
        }
    };

    const loadChartDataFromCache = () => {
        try {
            const cached = localStorage.getItem(CHART_CACHE_KEY);
            if (cached) {
                const cacheData = JSON.parse(cached);

                // 检查缓存是否过期（24小时）
                const now = Date.now();
                const cacheAge = now - (cacheData.timestamp || 0);
                const maxAge = 24 * 60 * 60 * 1000; // 24小时

                if (cacheAge < maxAge) {
                    return cacheData;
                } else {
                    // 缓存过期，清除
                    localStorage.removeItem(CHART_CACHE_KEY);
                    console.log('图表缓存已过期，已清除');
                }
            }
        } catch (error) {
            console.warn('从缓存加载图表数据失败:', error);
        }
        return null;
    };

    const clearChartCache = () => {
        try {
            localStorage.removeItem(CHART_CACHE_KEY);
            console.log('图表缓存已清除');
        } catch (error) {
            console.warn('清除图表缓存失败:', error);
        }
    };

    return {
        // 响应式状态
        chartContainer,
        d3Chart,
        timeRange,
        chartSeries,
        detectors,
        runningTime,

        // 状态查询
        isRunning: () => isChartRunning,

        // 图表方法
        initChart,
        updateChart,
        startChart,
        stopChart,
        restartChart,
        generateGradientData,
        updateGradientLines,
        toggleSeries,
        switchDetector,
        updateTimeRange,
        resetZoom,
        exportChart,
        resizeChart,
        cleanup,
        calculateDataRanges,
        updateYScales,

        // MQTT和缓存方法
        connectToMQTT,
        disconnectFromMQTT,
        saveChartDataToCache,
        loadChartDataFromCache,
        clearChartCache,
    };
}
