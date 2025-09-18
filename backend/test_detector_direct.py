"""
直接测试检测器双通道功能
"""
import asyncio
import sys
sys.path.insert(0, 'D:/back/chromatography_system/backend')

from hardware.host_devices.detector import DetectorController
from core.mqtt_manager import MQTTManager
import json

async def test_detector():
    print("=" * 80)
    print("测试检测器双通道功能")
    print("=" * 80)

    # 创建检测器实例
    detector = DetectorController(mock=True)

    # 连接检测器
    await detector.connect()
    print("[OK] 检测器已连接")

    # 设置双通道波长
    await detector.set_wavelength(254, 'A')
    await detector.set_wavelength(280, 'B')
    print(f"[OK] A通道波长: {detector.wavelength_a}nm")
    print(f"[OK] B通道波长: {detector.wavelength_b}nm")

    # 启动检测
    await detector.start_detection()
    print("[OK] 检测已启动\n")

    # 创建MQTT连接
    mqtt_manager = MQTTManager()
    if await mqtt_manager.connect():
        print("[OK] MQTT已连接\n")

        print("-" * 80)
        print("开始采集和发布双通道数据 (10秒)...")
        print("-" * 80)

        # 采集10个数据点
        for i in range(10):
            # 获取双通道信号
            signals = await detector.get_signal()

            # 获取完整状态
            status = await detector.get_status()

            print(f"\n时间点 {i+1}:")
            print(f"  双通道信号: {signals} mAU")
            print(f"  A通道: λ={status['channel_a']['wavelength']}nm, 信号={status['channel_a']['signal']} mAU")
            print(f"  B通道: λ={status['channel_b']['wavelength']}nm, 信号={status['channel_b']['signal']} mAU")
            print(f"  保留时间: {status['retention_time']} min")

            # 发布到MQTT（模拟DataProcessor的行为）
            device_id = "detector_test"

            # 发布双通道信号 [A, B]
            await mqtt_manager.publish_data(f"chromatography/detector/{device_id}/signal", signals)
            print(f"  --> 已发布信号: {signals}")

            # 发布双通道波长 [254, 280]
            wavelengths = [detector.wavelength_a, detector.wavelength_b]
            await mqtt_manager.publish_data(f"chromatography/detector/{device_id}/wavelength", wavelengths)
            print(f"  --> 已发布波长: {wavelengths}")

            # 发布各通道数据
            await mqtt_manager.publish_data(f"chromatography/detector/{device_id}/channel_a", status['channel_a'])
            await mqtt_manager.publish_data(f"chromatography/detector/{device_id}/channel_b", status['channel_b'])

            # 发布完整数据
            await mqtt_manager.publish_data(f"chromatography/detector/{device_id}/full_data", status)

            # 等待1秒
            await asyncio.sleep(1)

        # 停止检测
        await detector.stop_detection()
        print("\n[OK] 检测已停止")

        # 断开连接
        await detector.disconnect()
        await mqtt_manager.disconnect()
        print("[OK] 已断开所有连接")
    else:
        print("[ERROR] MQTT连接失败")

    print("\n" + "=" * 80)
    print("测试完成！")
    print("双通道数据已发布到MQTT")
    print("主题前缀: chromatography/detector/detector_test/")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_detector())