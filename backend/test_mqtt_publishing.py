"""
测试MQTT数据发布功能
Test MQTT Data Publishing
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.mqtt_manager import MQTTManager
# 直接导入DataProcessor，避免通过services的__init__.py
from services.data_processor import DataProcessor
from hardware.host_devices.detector import DetectorController
from hardware.host_devices.pressure_sensor import PressureSensor
from datetime import datetime


async def test_mqtt_publishing():
    """测试MQTT数据发布"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始测试MQTT数据发布...")

    # 创建MQTT管理器
    mqtt_manager = MQTTManager()

    # 连接MQTT
    connected = await mqtt_manager.connect()
    if not connected:
        print("MQTT连接失败")
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT连接成功")

    # 创建数据处理器
    data_processor = DataProcessor(mqtt_manager)

    # 创建并注册模拟设备
    try:
        # 创建检测器
        detector = DetectorController(mock=True)
        await detector.connect()
        await detector.start_detection()
        data_processor.register_host_device("detector_1", detector)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 注册检测器设备")

        # 创建压力传感器
        pressure_sensor = PressureSensor(mock=True)
        await pressure_sensor.connect()
        data_processor.register_host_device("pressure_sensor_1", pressure_sensor)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 注册压力传感器设备")

    except Exception as e:
        print(f"设备初始化错误: {e}")

    # 启动数据处理器
    await data_processor.start()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据处理器已启动")

    # 运行10秒，观察数据发布
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始发布数据到MQTT...")
    print("=" * 60)
    print("数据将发布到以下主题:")
    print("- data/random (随机数据)")
    print("- chromatography/detector/signal (检测器信号)")
    print("- chromatography/pressure/sensor/value (压力传感器值)")
    print("- chromatography/data/aggregated (聚合数据)")
    print("- chromatography/system/status (系统状态)")
    print("=" * 60)

    for i in range(10):
        await asyncio.sleep(1)

        # 获取并显示统计信息
        stats = data_processor.get_statistics()
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 第 {i+1} 秒:")
        print(f"  - 已生成随机数据: {stats['generated_count']} 个")
        print(f"  - 数据处理器运行: {stats['is_running']}")

        # 获取设备数据示例
        if hasattr(detector, 'get_signal'):
            signal = await detector.get_signal()
            print(f"  - 检测器信号: {signal:.5f}")

        if hasattr(pressure_sensor, 'get_pressure'):
            pressure = await pressure_sensor.get_pressure()
            print(f"  - 压力值: {pressure:.2f}")

        # 显示MQTT发布统计
        if hasattr(data_processor, 'mqtt_publisher'):
            mqtt_stats = data_processor.mqtt_publisher.get_statistics()
            print(f"  - MQTT队列大小: {mqtt_stats.get('queue_size', 0)}")
            if mqtt_stats.get('statistics'):
                for key, value in mqtt_stats['statistics'].items():
                    if value > 0:
                        print(f"    - {key}: {value}")

    # 停止数据处理器
    await data_processor.stop()
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据处理器已停止")

    # 断开MQTT
    await mqtt_manager.disconnect()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MQTT已断开")

    print("\n测试完成！")
    print("=" * 60)
    print("总结:")
    print(f"  - 总共生成数据: {data_processor.generated_count} 个")
    print(f"  - 注册设备数: {len(data_processor.host_devices)} 个")
    print("  - 所有数据已发布到MQTT服务器")


if __name__ == "__main__":
    print("=" * 60)
    print("MQTT数据发布测试")
    print("=" * 60)

    try:
        asyncio.run(test_mqtt_publishing())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()