"""
测试自主数据采集系统
"""
import asyncio
import logging
from datetime import datetime

# 设置日志级别为DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入必要模块
from core.mqtt_manager import MQTTManager
from services.data_processor.host_devices_processor import HostDevicesProcessor
from hardware.host_devices.detector import DetectorController
from hardware.host_devices.pressure_sensor import PressureSensor

async def main():
    print("=" * 60)
    print("测试自主数据采集系统")
    print("=" * 60)

    # 创建MQTT管理器
    mqtt_manager = MQTTManager()
    if await mqtt_manager.connect():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] MQTT连接成功")
    else:
        print("MQTT连接失败")
        return

    # 创建HostDevicesProcessor
    host_processor = HostDevicesProcessor(mqtt_manager)

    # 初始化检测器
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 初始化检测器...")
    detector = DetectorController(mock=True)
    await detector.connect()
    await detector.set_wavelength(254, 'A')
    await detector.set_wavelength(280, 'B')
    await detector.start_detection()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检测器已启动: A={detector.wavelength_a}nm, B={detector.wavelength_b}nm")

    # 注册设备
    host_processor.register_device("detector_1", detector)

    # 初始化压力传感器
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 初始化压力传感器...")
    pressure = PressureSensor(mock=True)
    if hasattr(pressure, 'connect'):
        await pressure.connect()
    host_processor.register_device("pressure_1", pressure)

    # 设置采集间隔并启动
    host_processor.set_collection_interval(1.0)
    await host_processor.start()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据采集已启动")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在发布数据到MQTT...")
    print("-" * 60)

    # 运行10秒
    await asyncio.sleep(10)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 停止数据采集...")

    # 停止
    await host_processor.stop()
    await detector.stop_detection()
    await detector.disconnect()
    await mqtt_manager.disconnect()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())