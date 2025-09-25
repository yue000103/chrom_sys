import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import uvicorn
import logging
from fastapi import Request
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from services.data_processor.host_devices_processor import HostDevicesProcessor
from api import device_control,data_collection,system_management,chromatography,hardware_control
from api import main_router

# 导入硬件设备控制器
from hardware.host_devices.detector import DetectorController
from hardware.host_devices.pressure_sensor import PressureSensor
from hardware.host_devices.bubble_sensor import BubbleSensorHost
from hardware.collect_devices.bubble_sensor_collect import BubbleSensorCollect

logger = logging.getLogger(__name__)

# 全局变量
mqtt_manager = None
db_manager = None
host_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global mqtt_manager, db_manager, host_processor

    # 启动时初始化服务
    print("=" * 60)
    print("液相色谱仪控制系统启动")
    print("=" * 60)

    # 初始化数据库
    db_manager = DatabaseManager()
    await db_manager.initialize()

    # 创建MQTT管理器
    mqtt_manager = MQTTManager()
    if await mqtt_manager.connect():
        print("✓ MQTT连接成功")

        # 创建HostDevicesProcessor管理设备数据采集
        host_processor = HostDevicesProcessor(mqtt_manager)

        # 初始化硬件设备（mock模式）
        detector = DetectorController(mock=True)
        if hasattr(detector, 'connect'):
            await detector.connect()
        await detector.set_wavelength([120, 254])
        await detector.start_detection()
        host_processor.register_device("detector_1", detector)
        print(f"✓ 检测器: A={detector.wavelength_a}nm, B={detector.wavelength_b}nm")

        pressure_sensor = PressureSensor(mock=True)
        if hasattr(pressure_sensor, 'connect'):
            await pressure_sensor.connect()
        host_processor.register_device("pressure_1", pressure_sensor)
        print("✓ 压力传感器: 已连接")

        bubble_sensor_host = BubbleSensorHost(mock=True)
        await bubble_sensor_host.initialize()
        host_processor.register_device("bubble_host", bubble_sensor_host)
        print("✓ 主机气泡传感器: 已连接 (气泡1-4)")

        bubble_sensor_collect = BubbleSensorCollect(mock=True)
        host_processor.register_device("bubble_collect", bubble_sensor_collect)
        print("✓ 收集气泡传感器: 已连接 (气泡5-7)")

        # 启动数据采集
        host_processor.set_collection_interval(1.0)
        await host_processor.start()

        print("\n📡 MQTT发布主题:")
        print("  🔍 检测器相关:")
        print("    ├─ chromatography/detector/{device_id}/signal")
        print("    ├─ chromatography/detector/{device_id}/wavelength")
        print("    ├─ chromatography/detector/{device_id}/channel_a")
        print("    ├─ chromatography/detector/{device_id}/channel_b")
        print("    ├─ chromatography/detector/{device_id}/retention_time")
        print("    └─ chromatography/detector/{device_id}/full_data")
        print("  📊 传感器相关:")
        print("    ├─ chromatography/pressure/{device_id}/data")
        print("    ├─ chromatography/pressure/{device_id}/value")
        print("    └─ chromatography/bubble/{device_id}/{sensor_id}")
        print("  ⚙️ 硬件设备:")
        print("    ├─ chromatography/pump/{device_id}/status")
        print("    ├─ chromatography/relay/{device_id}/status")
        print("    ├─ chromatography/valve/{device_id}/status")
        print("    ├─ chromatography/multivalve/{device_id}/position")
        print("    ├─ chromatography/led/status")
        print("    └─ chromatography/spray_pump/status")
        print("  🧪 实验数据:")
        print("    ├─ data/collection_started")
        print("    ├─ data/collection_completed")
        print("    ├─ data/real_time_status")
        print("    ├─ data/peak_detection_completed")
        print("    └─ data/random")
        print("  📋 系统管理:")
        print("    ├─ system/status")
        print("    ├─ system/preprocessing_status")
        print("    ├─ chromatography/system/status")
        print("    └─ chromatography/system/alert")
        print("  🔬 实验流程:")
        print("    ├─ experiments/status")
        print("    ├─ experiments/tube_collection")
        print("    ├─ experiments/signal_status")
        print("    ├─ experiments/signal_final")
        print("    └─ experiments/emergency")
        print("  🧮 业务功能:")
        print("    ├─ tubes/{operation}")
        print("    ├─ methods/updated")
        print("    ├─ gradient/{status}")
        print("    ├─ hardware/gradient_control")
        print("    └─ chromatography/data/aggregated")
        print("\n✅ 系统就绪 - 数据采集运行中")
        print("=" * 60)
    else:
        print("❌ MQTT连接失败")

    yield

    # 关闭时清理资源
    print("\n" + "=" * 60)
    print("系统关闭中...")

    if host_processor:
        await host_processor.stop()
        for device_name, device in host_processor.devices.items():
            try:
                if hasattr(device, 'stop_detection'):
                    await device.stop_detection()
                if hasattr(device, 'disconnect'):
                    await device.disconnect()
            except Exception as e:
                logger.error(f"断开设备 {device_name} 时出错: {e}")
        print("✓ 设备连接已断开")

    if mqtt_manager:
        await mqtt_manager.disconnect()
        print("✓ MQTT连接已断开")

    print("✅ 系统已安全关闭")
    print("=" * 60)

app = FastAPI(title="液相色谱仪控制系统", version="1.0.0", lifespan=lifespan)

# HTTP 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求开始
    logger.info(f"API Request: {request.method} {request.url}")

    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录请求结束
    logger.info(f"API Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")

    return response

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
# 注册统一的API路由器（包含所有模块化的路由）
app.include_router(main_router)

# 注册其他独立的路由（在api/__init__.py中没有包含的）
app.include_router(device_control.router, prefix="/api/devices", tags=["设备控制"])
app.include_router(data_collection.router, prefix="/api/data", tags=["数据采集"])
app.include_router(system_management.router, prefix="/api/system", tags=["系统管理"])
app.include_router(chromatography.router, prefix="/api/chromatography", tags=["色谱仪"])
app.include_router(hardware_control.router, tags=["硬件控制"])  # 硬件控制路由已包含/api/hardware前缀

@app.get("/")
async def root():
    """根路径，返回系统状态"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {
        "message": "液相色谱仪控制系统",
        "time": current_time,
        "status": "running" if host_processor and host_processor.is_running else "stopped",
        "mqtt_connected": mqtt_manager.is_connected if mqtt_manager else False
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/data/publishing-status")
async def get_publishing_status():
    """获取MQTT数据发布状态"""
    if host_processor:
        stats = host_processor.get_statistics()
        return {
            "status": "active" if host_processor.is_running else "stopped",
            "processor_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "status": "not_initialized",
            "message": "Host processor not initialized",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info",
        access_log=False
    )