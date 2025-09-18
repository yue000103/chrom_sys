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

from core.mqtt_manager import MQTTManager
from core.database import DatabaseManager
from services.data_processor.host_devices_processor import HostDevicesProcessor
from api import device_control,data_collection,system_management,chromatography,hardware_control

# 导入硬件设备控制器
from hardware.host_devices.detector import DetectorController
from hardware.host_devices.pressure_sensor import PressureSensor

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
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 液相色谱仪系统启动中...")

    # 初始化数据库
    db_manager = DatabaseManager()
    await db_manager.initialize()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据库连接成功")

    # 创建MQTT管理器
    mqtt_manager = MQTTManager()
    if await mqtt_manager.connect():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT连接成功")

        # 创建HostDevicesProcessor管理设备数据采集
        host_processor = HostDevicesProcessor(mqtt_manager)

        # 初始化硬件设备（mock模式）
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 初始化硬件设备...")

        # 初始化检测器
        detector = DetectorController(mock=True)
        if hasattr(detector, 'connect'):
            await detector.connect()
        # 设置双通道波长
        await detector.set_wavelength(254, 'A')
        await detector.set_wavelength(280, 'B')
        # 启动检测
        await detector.start_detection()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检测器: A通道={detector.wavelength_a}nm, B通道={detector.wavelength_b}nm")

        # 注册检测器到处理器
        host_processor.register_device("detector_1", detector)

        # 初始化其他设备（可选）
        pressure_sensor = PressureSensor(mock=True)
        if hasattr(pressure_sensor, 'connect'):
            await pressure_sensor.connect()
        host_processor.register_device("pressure_1", pressure_sensor)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 设备初始化完成")

        # 设置采集间隔并启动自主数据采集
        host_processor.set_collection_interval(1.0)  # 1秒采集一次
        await host_processor.start()

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据采集已启动")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 采集间隔: 1秒")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT主题:")
        print("  - 信号: chromatography/detector/detector_1/signal [A, B]")
        print("  - 波长: chromatography/detector/detector_1/wavelength [254, 280]")
        print("  - A通道: chromatography/detector/detector_1/channel_a")
        print("  - B通道: chromatography/detector/detector_1/channel_b")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT连接失败")

    yield

    # 关闭时清理资源
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 系统关闭中...")

    if host_processor:
        # 停止数据采集
        await host_processor.stop()

        # 断开所有设备
        for device_name, device in host_processor.devices.items():
            try:
                if hasattr(device, 'stop_detection'):
                    await device.stop_detection()
                if hasattr(device, 'disconnect'):
                    await device.disconnect()
            except Exception as e:
                logger.error(f"断开设备 {device_name} 时出错: {e}")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据采集已停止")

    if mqtt_manager:
        await mqtt_manager.disconnect()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT连接已断开")

app = FastAPI(title="液相色谱仪控制系统", version="1.0.0", lifespan=lifespan)

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
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
    print("=" * 60)
    print("液相色谱仪控制系统 - FastAPI后端")
    print("实时数据采集和硬件设备控制")
    print("MQTT服务器: broker.emqx.io:1883")
    print("数据采集频率: 1Hz (1秒/次)")
    print("检测器模拟: 双通道(A:254nm, B:280nm) 三个高斯峰(4min, 7min, 12min)")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )