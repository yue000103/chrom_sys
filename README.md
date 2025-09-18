# 液相色谱仪控制系统

基于Vue + FastAPI + MQTT的液相色谱仪硬件控制和实时数据采集系统，支持22个硬件设备的集成控制。

## 📋 项目概述

本系统基于现有的Vue+FastAPI+MQTT实时采集架构，扩展支持液相色谱仪的完整硬件控制功能，包括：

### 硬件设备支持
- **主机模块** (5类设备，通过树莓派串口通信)
  - 继电器控制 (双2/双1/泵2)
  - 压力传感器 (ttyAMA0, 9600波特率)
  - 检测器 (ttyAMA3, 57600波特率)
  - 四合一高压恒流泵 (ttyAMA2, 115200波特率)
  - 气泡传感器 (气1-气4)

- **收集模块** (17个设备，通过IP/HTTP通信)
  - LED灯控制 (192.168.1.129/led/on)
  - 阀门控制 (电1-电6、泵3、双3)
  - 气泡传感器状态 (气5-气7)
  - 多向阀控制 (多1-多11)
  - 隔膜泵控制 (泵4)

### 核心功能
- ✅ **实时数据采集** - 基于开发文档要求，每秒生成随机数据并通过MQTT发布
- ✅ **设备统一控制** - 22个硬件设备的统一管理和控制
- ✅ **液相色谱仪工作流** - 自动化的样品注入、分离、检测流程
- ✅ **实时数据可视化** - Chart.js图表，支持开始/暂停/继续/重新开始控制
- ✅ **MQTT通信** - 连接broker.emqx.io，主题data/random
- ✅ **模块化架构** - 分层设计，便于扩展和维护

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue前端界面    │    │  FastAPI核心    │    │   硬件抽象层     │
│                │    │                │    │                │
│ ├─实时数据显示   │◄──►│ ├─MQTT服务      │◄──►│ ├─主机模块驱动   │
│ ├─设备控制面板   │    │ ├─RESTful API   │    │ ├─收集模块驱动   │
│ ├─流程管理      │    │ ├─设备管理器     │    │ ├─协议转换器     │
│ └─状态监控      │    │ └─数据处理器     │    │ └─错误处理器     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   数据存储层     │    │   物理硬件层     │
                       │                │    │                │
                       │ ├─时序数据库     │    │ ├─树莓派串口设备  │
                       │ ├─配置数据库     │    │ ├─IP网络设备     │
                       │ ├─日志系统      │    │ ├─传感器群      │
                       │ └─文件存储      │    │ └─执行器群      │
                       └─────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
chromatography_system/
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面视图
│   │   ├── components/        # 组件库
│   │   │   ├── charts/        # 图表组件
│   │   │   ├── device-panels/ # 设备控制面板
│   │   │   ├── monitoring/    # 监控组件
│   │   │   └── workflow/      # 工作流组件
│   │   ├── services/          # 前端服务
│   │   └── store/             # 状态管理
│   ├── package.json
│   └── vite.config.js
│
├── backend/                    # FastAPI 后端
│   ├── api/                   # API路由
│   ├── services/              # 业务服务
│   ├── models/                # 数据模型
│   ├── core/                  # 核心功能
│   ├── config/                # 配置管理
│   ├── utils/                 # 工具函数
│   ├── main.py               # 应用入口
│   └── requirements.txt
│
├── hardware/                   # 硬件抽象层
│   ├── host_devices/          # 主机模块 (串口)
│   │   ├── relay_controller.py
│   │   ├── pressure_sensor.py
│   │   ├── detector.py
│   │   ├── pump_controller.py
│   │   └── bubble_sensor.py
│   ├── collect_devices/       # 收集模块 (HTTP)
│   │   ├── led_controller.py
│   │   ├── valve_controller.py
│   │   ├── multi_valve.py
│   │   └── pump_spray.py
│   ├── drivers/               # 底层驱动
│   ├── interfaces/            # 硬件接口
│   └── tests/                 # 硬件测试
│
├── data/                       # 数据管理层
│   ├── database/              # 数据库
│   ├── storage/               # 文件存储
│   └── backup/                # 数据备份
│
├── docs/                       # 文档
├── scripts/                    # 脚本工具
│   ├── start_system.bat       # 系统启动脚本
│   └── install_dependencies.bat
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- 网络连接 (连接MQTT服务器 broker.emqx.io)

### 安装依赖
```bash
# 方式1: 使用脚本安装
scripts\install_dependencies.bat

# 方式2: 手动安装
cd backend
pip install -r requirements.txt

cd ..\frontend
npm install
```

### 初始化数据库
```bash
# 初始化SQLite数据库
scripts\init_database.bat
```

### 启动系统
```bash
# 方式1: 使用脚本启动
scripts\start_system.bat

# 方式2: 手动启动
# 启动后端
cd backend
python main.py

# 启动前端
cd frontend
npm run dev
```

### 访问地址
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8008
- API文档: http://localhost:8008/docs

## 📊 功能特性

### 实时数据采集 (基于开发文档)
- ✅ 每秒生成随机数据 (0-100)
- ✅ MQTT发布到 `data/random` 主题
- ✅ 数据格式: `{"timestamp": "2025-09-12T10:30:45", "value": 85.6}`
- ✅ 前端实时图表显示，保持最近5分钟数据
- ✅ 控制按钮: 开始/暂停/继续/重新开始

### 硬件设备控制
- 🔧 22个设备的统一管理接口
- 🔧 双协议支持 (串口 + HTTP)
- 🔧 设备状态实时监控
- 🔧 错误处理和自动恢复

### 液相色谱仪工作流
- 🧪 样品注入自动化
- 🧪 分离过程控制
- 🧪 检测周期管理
- 🧪 清洗程序自动化

### 数据管理
- 💾 SQLite数据库存储 (零配置，轻量级)
- 💾 22个设备配置管理
- 💾 传感器数据历史记录
- 💾 完整操作审计日志
- 💾 分析方法存储
- 💾 用户权限管理
- 💾 数据导出功能

## 🔧 技术栈

### 前端技术
- **Vue 3** + Composition API
- **Chart.js** - 实时数据可视化
- **Element Plus** - UI组件库
- **Pinia** - 状态管理
- **MQTT.js** - MQTT客户端
- **Vite** - 构建工具

### 后端技术
- **FastAPI** - 高性能API框架
- **Pydantic** - 数据验证
- **paho-mqtt** - MQTT客户端
- **pyserial** - 串口通信
- **aiohttp** - HTTP异步客户端
- **SQLite** - 轻量级数据库 (零配置)
- **aiosqlite** - 异步SQLite操作

### 通信协议
- **MQTT** - 实时消息传输 (broker.emqx.io)
- **HTTP/WebSocket** - API通信
- **Serial/RS485** - 硬件设备通信

## 📈 性能指标

- 数据采集频率: 1秒/次 (开发文档要求)
- MQTT消息延迟: ≤50ms
- 前端图表更新: ≤200ms
- 设备控制响应: ≤500ms
- 支持设备数量: 22个硬件设备
- 数据保留周期: 最近5分钟 (300个数据点)

## 🔍 MQTT主题设计

基于开发文档要求：

- `data/random` - 随机数据发布 (开发文档核心要求)
- `chromatography/pressure` - 压力传感器数据
- `chromatography/detector` - 检测器数据
- `chromatography/bubble` - 气泡传感器数据
- `chromatography/flow` - 流量数据
- `system/status` - 系统状态

## 📝 开发说明

### 关键实现
1. **MQTT功能** - 完全基于开发文档要求实现
2. **随机数据生成** - 每秒生成0-100的随机数
3. **前端控制逻辑** - 开始/暂停/继续/重新开始按钮
4. **图表显示** - 实时更新，保持5分钟历史数据
5. **硬件抽象** - 22个设备的统一接口封装

### 扩展功能
- 设备控制面板
- 液相色谱仪工作流
- 数据分析界面
- 系统配置管理

## 🐛 故障排除

### 常见问题
1. **MQTT连接失败** - 检查网络连接到 broker.emqx.io
2. **端口占用** - 确保8008和3000端口可用
3. **设备通信失败** - 检查串口权限和IP网络连接

### 调试方法
- 查看浏览器控制台 (前端)
- 查看FastAPI日志 (后端)
- 检查MQTT连接状态
- 验证硬件设备响应

## 📧 支持

如遇问题请检查：
1. 系统日志和控制台输出
2. MQTT连接状态
3. 硬件设备连接状态
4. 网络连接和端口配置

---

**项目特点**: 基于现有Vue+FastAPI+MQTT架构，完整实现开发文档功能，扩展支持22个硬件设备控制，构建专业的液相色谱仪自动化控制系统。