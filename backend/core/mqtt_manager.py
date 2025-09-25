import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime
import threading
import time
import logging
from typing import Dict, Callable, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTManager:
    """MQTT管理器 - 实现开发文档要求的MQTT功能"""

    def __init__(self):
        # MQTT配置 - 与开发文档保持一致
        self.broker_host = "broker.emqx.io"
        self.broker_port = 1883
        self.client_id = "chromatography_system_" + str(int(time.time()))

        # 主题定义 - 基于开发文档要求
        self.topics = {
            "data_random": "data/random",  # 随机数据主题
            "chromatography_pressure": "chromatography/pressure",
            "chromatography_detector": "chromatography/detector",
            "chromatography_bubble": "chromatography/bubble",
            "chromatography_flow": "chromatography/flow",
            "system_status": "system/status"
        }

        self.client = None
        self.is_connected = False
        self._loop = None
        self._thread = None
        self.message_handlers: Dict[str, Callable] = {}

        # 重连配置
        self.reconnect_enabled = True
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.max_reconnect_attempts = 10
        self.reconnect_count = 0

    async def connect(self):
        """连接到MQTT服务器"""
        try:
            logger.info(f"连接MQTT服务器: {self.broker_host}:{self.broker_port}")

            # 在新线程中运行MQTT客户端
            self._thread = threading.Thread(target=self._run_mqtt_client, daemon=True)
            self._thread.start()

            # 等待连接建立
            timeout = 10
            while not self.is_connected and timeout > 0:
                await asyncio.sleep(0.1)
                timeout -= 0.1

            if self.is_connected:
                logger.info("MQTT连接成功")
                return True
            else:
                logger.error("MQTT连接超时")
                return False

        except Exception as e:
            logger.error(f"MQTT连接错误: {e}")
            return False

    def _run_mqtt_client(self):
        """在单独线程中运行MQTT客户端"""
        self.client = mqtt.Client(client_id=self.client_id)

        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message

        try:
            # 连接到broker
            self.client.connect(self.broker_host, self.broker_port, 60)

            # 开始循环
            self.client.loop_forever()

        except Exception as e:
            logger.error(f"MQTT客户端错误: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        if rc == 0:
            self.is_connected = True
            self.reconnect_count = 0  # 重置重连计数
            logger.info("MQTT连接建立成功")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调函数"""
        self.is_connected = False
        logger.warning("MQTT连接断开")

        # 如果是意外断开（rc != 0）且启用了重连，则尝试重连
        if rc != 0 and self.reconnect_enabled:
            self._attempt_reconnect()

    def _on_publish(self, client, userdata, mid):
        """消息发布回调函数"""
        pass  # 不记录每次发布，避免日志过多

    def _on_message(self, client, userdata, message):
        """消息接收回调函数"""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')

            # 处理JSON消息
            try:
                data = json.loads(payload)
            except:
                data = payload

            # 调用注册的消息处理器
            if topic in self.message_handlers:
                try:
                    self.message_handlers[topic](topic, data)
                except Exception as e:
                    logger.error(f"消息处理错误 {topic}: {e}")

            logger.debug(f"收到消息 {topic}: {payload[:100]}...")

        except Exception as e:
            logger.error(f"处理MQTT消息时出错: {e}")

    def _attempt_reconnect(self):
        """尝试重新连接"""
        if self.reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"达到最大重连次数 {self.max_reconnect_attempts}，停止重连")
            return

        self.reconnect_count += 1
        logger.info(f"尝试重连 MQTT ({self.reconnect_count}/{self.max_reconnect_attempts})...")

        # 使用定时器延迟重连
        def delayed_reconnect():
            time.sleep(self.reconnect_delay)
            if self.client and not self.is_connected:
                try:
                    self.client.reconnect()
                    logger.info("MQTT重连命令已发送")
                except Exception as e:
                    logger.error(f"MQTT重连失败: {e}")
                    # 如果重连失败，继续尝试
                    if self.reconnect_count < self.max_reconnect_attempts:
                        self._attempt_reconnect()

        # 在新线程中延迟重连
        reconnect_thread = threading.Thread(target=delayed_reconnect, daemon=True)
        reconnect_thread.start()

    async def publish_data(self, topic: str, data: Any, qos: int = 0):
        """发布数据到MQTT - 实现开发文档要求的数据格式"""
        if not self.is_connected or not self.client:
            logger.warning(f"MQTT未连接，无法发布数据到 {topic}")

            # 如果启用了重连且当前未在重连过程中，则尝试重连
            if self.reconnect_enabled and self.reconnect_count < self.max_reconnect_attempts:
                self._attempt_reconnect()

            return False

        try:
            # 如果data是列表或基本类型，直接发送
            if isinstance(data, (list, int, float, str, bool)):
                json_message = json.dumps(data, ensure_ascii=False)
            # 如果是字典，按照原有逻辑处理
            elif isinstance(data, dict):
                # 确保数据格式符合开发文档要求
                if topic == self.topics["data_random"]:
                    # data/random主题的数据格式: {"timestamp": "2025-09-12T10:30:45", "value": 85.6}
                    message = {
                        "timestamp": data.get("timestamp", datetime.now().isoformat()),
                        "value": float(data.get("value", 0))
                    }
                else:
                    # 其他主题的通用格式
                    message = {
                        "timestamp": datetime.now().isoformat(),
                        "device_id": data.get("device_id", "unknown"),
                        "data": data
                    }
                json_message = json.dumps(message, ensure_ascii=False)
            else:
                # 其他类型，尝试直接序列化
                json_message = json.dumps(data, ensure_ascii=False)

            # 发布消息
            result = self.client.publish(topic, json_message, qos=qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"成功发布到 {topic}: {json_message[:100]}...")
                return True
            else:
                logger.error(f"发布失败到 {topic}，错误码: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"发布数据时出错: {e}")
            return False

    async def subscribe_topic(self, topic: str, handler: Callable = None, qos: int = 0):
        """订阅主题"""
        if not self.client or not self.is_connected:
            logger.error("MQTT未连接，无法订阅主题")
            return False

        try:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"成功订阅主题: {topic}")

                # 注册消息处理器
                if handler:
                    self.message_handlers[topic] = handler

                return True
            else:
                logger.error(f"订阅主题失败 {topic}，错误码: {result[0]}")
                return False

        except Exception as e:
            logger.error(f"订阅主题时出错: {e}")
            return False

    async def unsubscribe_topic(self, topic: str):
        """取消订阅主题"""
        if not self.client:
            return False

        try:
            result = self.client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"成功取消订阅主题: {topic}")

                # 移除消息处理器
                if topic in self.message_handlers:
                    del self.message_handlers[topic]

                return True
            else:
                logger.error(f"取消订阅失败 {topic}，错误码: {result[0]}")
                return False

        except Exception as e:
            logger.error(f"取消订阅时出错: {e}")
            return False

    async def publish_random_data(self, value: float):
        """发布随机数据 - 开发文档要求的核心功能"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "value": value
        }
        return await self.publish_data(self.topics["data_random"], data)

    async def publish_chromatography_data(self, data_type: str, device_id: str, value: float):
        """发布色谱仪数据"""
        topic_map = {
            "pressure": self.topics["chromatography_pressure"],
            "detector": self.topics["chromatography_detector"],
            "bubble": self.topics["chromatography_bubble"],
            "flow": self.topics["chromatography_flow"]
        }

        topic = topic_map.get(data_type, self.topics["system_status"])

        data = {
            "device_id": device_id,
            "data_type": data_type,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

        return await self.publish_data(topic, data)

    # 为了兼容性，添加publish别名
    async def publish(self, topic: str, data: Any, qos: int = 0):
        """发布数据到MQTT (别名)"""
        return await self.publish_data(topic, data, qos)

    async def reconnect_mqtt(self):
        """手动重连MQTT"""
        if self.is_connected:
            logger.info("MQTT已连接，无需重连")
            return True

        logger.info("手动触发MQTT重连...")
        self.reconnect_count = 0  # 重置重连计数
        self._attempt_reconnect()

        # 等待连接建立
        timeout = 10
        while not self.is_connected and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

        return self.is_connected

    async def disconnect(self):
        """断开MQTT连接"""
        self.reconnect_enabled = False  # 禁用自动重连

        if self.client:
            self.is_connected = False
            self.client.loop_stop()
            self.client.disconnect()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        logger.info("MQTT连接已断开")

    def get_connection_status(self):
        """获取连接状态"""
        return {
            "connected": self.is_connected,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "client_id": self.client_id,
            "subscribed_topics": list(self.message_handlers.keys()),
            "reconnect_enabled": self.reconnect_enabled,
            "reconnect_count": self.reconnect_count,
            "max_reconnect_attempts": self.max_reconnect_attempts
        }