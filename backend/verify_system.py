"""
验证系统完整性 - 检查检测器数据发布
"""
import requests
import json
from datetime import datetime

# API端点
base_url = "http://localhost:8008"

print("=" * 80)
print("液相色谱仪控制系统 - 功能验证")
print("=" * 80)

# 1. 检查系统状态
try:
    response = requests.get(f"{base_url}/")
    status = response.json()
    print(f"\n[OK] 系统状态: {status.get('status', 'unknown')}")
    print(f"  MQTT连接: {status.get('mqtt_connected', False)}")
except Exception as e:
    print(f"\n[ERROR] 无法连接到系统: {e}")
    exit(1)

# 2. 检查数据发布状态
try:
    response = requests.get(f"{base_url}/api/data/publishing-status")
    pub_status = response.json()

    print(f"\n[OK] 数据发布状态: {pub_status.get('status', 'unknown')}")

    # 显示注册设备
    devices = pub_status.get('registered_devices', {})
    print(f"\n注册的设备:")
    for device_type, device_list in devices.items():
        for device in device_list:
            print(f"  - {device}")

    # 显示设备数据样本
    samples = pub_status.get('device_data_samples', {})
    if samples:
        print(f"\n最新数据样本:")
        for device_id, data in samples.items():
            if isinstance(data, dict):
                print(f"  {device_id}:")
                print(f"    - 信号: {data.get('signal', 'N/A')} mAU")
                print(f"    - 波长: {data.get('wavelength', 'N/A')} nm")
                print(f"    - 保留时间: {data.get('retention_time', 'N/A')} min")
            else:
                print(f"  {device_id}: {data}")

    # 显示数据处理器统计
    dp_stats = pub_status.get('data_processor_stats', {})
    print(f"\n数据处理统计:")
    print(f"  - 运行状态: {dp_stats.get('is_running', False)}")
    print(f"  - 生成计数: {dp_stats.get('generated_count', 0)}")
    print(f"  - 数据间隔: {dp_stats.get('data_interval', 1.0)}秒")

except Exception as e:
    print(f"\n[ERROR] 获取数据发布状态失败: {e}")

print("\n" + "=" * 80)
print("验证完成!")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)