"""
监听MQTT双通道检测器数据
"""
import paho.mqtt.client as mqtt
import json
from datetime import datetime

def on_connect(client, userdata, flags, rc):
    print(f"连接MQTT: {'成功' if rc == 0 else f'失败({rc})'}")
    # 订阅所有检测器相关主题
    topics = [
        "chromatography/detector/+/signal",
        "chromatography/detector/+/wavelength",
        "chromatography/detector/+/channel_a",
        "chromatography/detector/+/channel_b",
        "chromatography/detector/+/retention_time",
        "chromatography/detector/+/full_data",
        "chromatography/pressure/+/value",
    ]
    for topic in topics:
        client.subscribe(topic)
        print(f"  订阅: {topic}")
    print("-" * 60)

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        # 解析消息
        payload = msg.payload.decode('utf-8')
        try:
            data = json.loads(payload)
        except:
            data = payload

        timestamp = datetime.now().strftime('%H:%M:%S')

        # 根据主题类型显示
        if "/signal" in topic:
            if isinstance(data, list) and len(data) == 2:
                print(f"[{timestamp}] 信号: A={data[0]:.3f}, B={data[1]:.3f} mAU")
            else:
                print(f"[{timestamp}] 信号: {data}")

        elif "/wavelength" in topic:
            if isinstance(data, list) and len(data) == 2:
                print(f"[{timestamp}] 波长: A={data[0]}nm, B={data[1]}nm")

        elif "/channel_a" in topic:
            if isinstance(data, dict):
                print(f"[{timestamp}] A通道: λ={data.get('wavelength')}nm, 信号={data.get('signal'):.3f} mAU")

        elif "/channel_b" in topic:
            if isinstance(data, dict):
                print(f"[{timestamp}] B通道: λ={data.get('wavelength')}nm, 信号={data.get('signal'):.3f} mAU")

        elif "/retention_time" in topic:
            if isinstance(data, dict):
                print(f"[{timestamp}] 保留时间: {data.get('retention_time')} min")

        elif "/pressure" in topic and "/value" in topic:
            if isinstance(data, dict):
                print(f"[{timestamp}] 压力: {data.get('pressure'):.2f} MPa")

        elif "/full_data" in topic:
            print(f"[{timestamp}] === 完整数据 ===")
            if isinstance(data, dict):
                print(f"  设备: {data.get('device_id')}")
                print(f"  信号: {data.get('signal')}")
                print(f"  波长: {data.get('wavelength')}")
                print(f"  保留时间: {data.get('retention_time')} min")
            print("-" * 60)

    except Exception as e:
        print(f"解析错误: {e}")

print("=" * 60)
print("MQTT数据监听器")
print("连接: broker.emqx.io:1883")
print("=" * 60)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("broker.emqx.io", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n监听停止")
    client.disconnect()
except Exception as e:
    print(f"连接错误: {e}")