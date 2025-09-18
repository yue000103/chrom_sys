"""
测试双通道检测器数据
"""
import asyncio
import json
from datetime import datetime
import paho.mqtt.client as mqtt

class DualChannelMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"连接到MQTT服务器: {'成功' if rc == 0 else '失败'}")
        # 订阅双通道相关主题
        topics = [
            "chromatography/detector/+/signal",  # 双通道信号 [A, B]
            "chromatography/detector/+/wavelength",  # 双通道波长 [254, 280]
            "chromatography/detector/+/channel_a",  # A通道单独数据
            "chromatography/detector/+/channel_b",  # B通道单独数据
            "chromatography/detector/+/full_data",  # 完整数据
        ]
        for topic in topics:
            client.subscribe(topic)
            print(f"已订阅: {topic}")
        print("-" * 80)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            # 解析消息
            payload_str = msg.payload.decode('utf-8')

            # 尝试解析为JSON
            try:
                data = json.loads(payload_str)
            except:
                data = payload_str

            timestamp = datetime.now().strftime('%H:%M:%S')

            # 根据主题显示数据
            if "signal" in topic and "/signal" in topic:
                if isinstance(data, list) and len(data) == 2:
                    print(f"[{timestamp}] 双通道信号: A={data[0]:.3f} mAU, B={data[1]:.3f} mAU")
                else:
                    print(f"[{timestamp}] 信号数据: {data}")

            elif "wavelength" in topic and "/wavelength" in topic:
                if isinstance(data, list) and len(data) == 2:
                    print(f"[{timestamp}] 双通道波长: A={data[0]}nm, B={data[1]}nm")
                else:
                    print(f"[{timestamp}] 波长数据: {data}")

            elif "/channel_a" in topic:
                if isinstance(data, dict):
                    print(f"[{timestamp}] A通道: λ={data.get('wavelength', 'N/A')}nm, "
                          f"信号={data.get('signal', 'N/A')} mAU")

            elif "/channel_b" in topic:
                if isinstance(data, dict):
                    print(f"[{timestamp}] B通道: λ={data.get('wavelength', 'N/A')}nm, "
                          f"信号={data.get('signal', 'N/A')} mAU")

            elif "/full_data" in topic:
                if isinstance(data, dict):
                    print(f"[{timestamp}] ===== 完整数据 =====")
                    print(f"  设备ID: {data.get('device_id', 'N/A')}")
                    print(f"  保留时间: {data.get('retention_time', 'N/A')} min")

                    # 显示双通道数据
                    signal = data.get('signal', [])
                    wavelength = data.get('wavelength', [])

                    if isinstance(signal, list) and len(signal) == 2:
                        print(f"  双通道信号: {signal}")

                    if isinstance(wavelength, list) and len(wavelength) == 2:
                        print(f"  双通道波长: {wavelength}")

                    # 显示各通道详细信息
                    if 'channel_a' in data:
                        ch_a = data['channel_a']
                        print(f"  A通道: {ch_a}")

                    if 'channel_b' in data:
                        ch_b = data['channel_b']
                        print(f"  B通道: {ch_b}")

                    print("-" * 80)

        except Exception as e:
            print(f"解析消息错误: {e}")

    def run(self):
        """运行监控器"""
        print("=" * 80)
        print("双通道检测器数据监控器")
        print("连接到: broker.emqx.io:1883")
        print("=" * 80)

        self.client.connect("broker.emqx.io", 1883, 60)

        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n监控已停止")
            self.client.disconnect()

if __name__ == "__main__":
    monitor = DualChannelMonitor()
    monitor.run()