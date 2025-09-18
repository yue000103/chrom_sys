"""
MQTT订阅测试脚本 - 监听检测器数据
"""
import asyncio
import json
from datetime import datetime
from aiomqtt import Client

async def subscribe_detector_data():
    """订阅并显示检测器数据"""
    async with Client("broker.emqx.io") as client:
        # 订阅所有检测器相关主题
        topics = [
            "chromatography/detector/+/signal",
            "chromatography/detector/+/wavelength",
            "chromatography/detector/+/retention_time",
            "chromatography/detector/+/full_data",
            "chromatography/detector/signal",  # 兼容旧主题
        ]

        for topic in topics:
            await client.subscribe(topic)
            print(f"已订阅主题: {topic}")

        print("\n等待检测器数据...\n")
        print("-" * 80)

        async with client.messages() as messages:
            async for message in messages:
                topic = str(message.topic)
                try:
                    # 解析消息内容
                    if isinstance(message.payload, bytes):
                        payload_str = message.payload.decode('utf-8')
                    else:
                        payload_str = str(message.payload)

                    # 尝试解析为JSON
                    try:
                        data = json.loads(payload_str)
                    except:
                        data = {"value": payload_str}

                    # 显示接收到的数据
                    timestamp = datetime.now().strftime('%H:%M:%S')

                    if "signal" in topic:
                        if isinstance(data, dict):
                            signal = data.get('value', data.get('signal', 'N/A'))
                        else:
                            signal = data
                        print(f"[{timestamp}] 信号值: {signal} mAU")

                    elif "wavelength" in topic:
                        wavelength = data.get('wavelength', 'N/A')
                        print(f"[{timestamp}] 波长: {wavelength} nm")

                    elif "retention_time" in topic:
                        rt = data.get('retention_time', 'N/A')
                        print(f"[{timestamp}] 保留时间: {rt} min")

                    elif "full_data" in topic:
                        print(f"[{timestamp}] 完整数据:")
                        print(f"  - 设备ID: {data.get('device_id', 'N/A')}")
                        print(f"  - 波长: {data.get('wavelength', 'N/A')} nm")
                        print(f"  - 信号: {data.get('signal', 'N/A')} mAU")
                        print(f"  - 保留时间: {data.get('retention_time', 'N/A')} min")
                        print(f"  - 检测模式: {data.get('detection_mode', 'N/A')}")
                        print(f"  - 连接状态: {data.get('is_connected', 'N/A')}")
                        print(f"  - 检测状态: {data.get('is_detecting', 'N/A')}")
                        print("-" * 80)

                except Exception as e:
                    print(f"[{timestamp}] 解析消息错误 ({topic}): {e}")

if __name__ == "__main__":
    print("MQTT检测器数据监听器")
    print("连接到: broker.emqx.io:1883")
    print("=" * 80)

    try:
        asyncio.run(subscribe_detector_data())
    except KeyboardInterrupt:
        print("\n监听已停止")