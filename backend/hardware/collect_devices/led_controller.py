"""
LED灯控制器
192.168.1.129/led/on
"""

from typing import Dict, Any, Optional, List, Union
import asyncio
import requests
import json
from ..hardware_config import MockDataGenerator, is_mock_mode


class LEDController:
    """LED灯控制器类"""
    
    def __init__(self, base_url: str = 'http://192.168.1.129', mock: Optional[bool] = None):
        self.device_id = 'led_controller'
        self.base_url = base_url
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.led_status = False
        self.brightness = 100  # 0-100

        # LED状态缓存，记录每个组的LED状态
        self.led_groups_status = {
            'group0': {},  # {led_num: color}
            'group1': {}   # {led_num: color}
        }
    
    async def turn_on(self) -> bool:
        """打开LED灯（默认设置为白色）"""
        self.led_status = True
        # 使用新接口设置第1号LED为白色
        return await self.set_single_led(1, [255, 255, 255], 0)
    
    async def turn_off(self) -> bool:
        """关闭LED灯"""
        self.led_status = False
        # 关闭所有LED灯
        return await self.turn_off_all_leds()
    
    async def set_brightness(self, brightness: int) -> bool:
        """
        设置亮度（通过调整RGB值模拟亮度）
        :param brightness: 亮度值(0-100)
        :return: 设置结果
        """
        if not 0 <= brightness <= 100:
            return False

        self.brightness = brightness

        # 根据亮度调整当前所有LED的颜色
        brightness_factor = brightness / 100.0
        led_config = {}

        for group_name, leds in self.led_groups_status.items():
            if leds:  # 如果该组有LED
                led_config[group_name] = []
                for led_num, current_color in leds.items():
                    # 调整颜色亮度
                    adjusted_color = [int(c * brightness_factor) for c in current_color]
                    led_config[group_name].append({
                        'led_num': led_num,
                        'color': adjusted_color
                    })

        if led_config:
            return await self.set_leds_batch(led_config)
        return True
    
    async def blink(self, times: int = 3, interval: float = 0.5) -> bool:
        """
        LED闪烁
        :param times: 闪烁次数
        :param interval: 闪烁间隔(秒)
        :return: 执行结果
        """
        try:
            for i in range(times):
                # 点亮
                await self.turn_on()
                await asyncio.sleep(interval)
                # 关闭
                await self.turn_off()
                if i < times - 1:  # 最后一次闪烁后不需要等待
                    await asyncio.sleep(interval)
            return True
        except Exception as e:
            print(f"LED闪烁失败: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """获取LED状态"""
        return {
            'device_id': self.device_id,
            'mode': 'mock' if self.mock else 'normal',
            'status': 'on' if self.led_status else 'off',
            'brightness': self.brightness,
            'base_url': self.base_url,
            'led_groups': self.led_groups_status
        }

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock

    def _normalize_color(self, color: Union[List[int], str]) -> List[int]:
        """
        标准化颜色格式，将各种颜色格式转换为RGB列表
        :param color: 颜色值，支持 [R,G,B] 列表、"#RRGGBB" 或 "0xRRGGBB" 格式
        :return: [R, G, B] 列表
        """
        if isinstance(color, list) and len(color) == 3:
            return color
        elif isinstance(color, str):
            if color.startswith('#'):
                # #RRGGBB格式
                hex_color = color[1:]
                return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            elif color.startswith('0x'):
                # 0xRRGGBB格式
                hex_color = color[2:]
                return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        raise ValueError(f"无效的颜色格式: {color}")

    async def set_leds_batch(self, led_config: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        批量设置LED灯（使用JSON格式）
        :param led_config: LED配置，格式如：
        {
            "group0": [{"led_num": 1, "color": [255, 0, 0]}],
            "group1": [{"led_num": 1, "color": "#0000FF"}]
        }
        :return: 设置结果
        """
        if self.mock:
            # Mock模式下更新状态缓存
            for group_name, leds in led_config.items():
                if group_name not in self.led_groups_status:
                    self.led_groups_status[group_name] = {}
                for led_info in leds:
                    led_num = led_info['led_num']
                    color = self._normalize_color(led_info['color'])
                    self.led_groups_status[group_name][led_num] = color

            await asyncio.sleep(0.1)
            return True
        else:
            try:
                url = f"{self.base_url}/led/batch"
                headers = {'Content-Type': 'application/json'}

                # 标准化颜色格式
                normalized_config = {}
                for group_name, leds in led_config.items():
                    normalized_config[group_name] = []
                    for led_info in leds:
                        normalized_led = {
                            'led_num': led_info['led_num'],
                            'color': self._normalize_color(led_info['color'])
                        }
                        normalized_config[group_name].append(normalized_led)

                # 发送POST请求
                response = await asyncio.to_thread(
                    requests.post,
                    url,
                    data=json.dumps(normalized_config),
                    headers=headers
                )

                if response.status_code == 200:
                    # 更新状态缓存
                    for group_name, leds in normalized_config.items():
                        if group_name not in self.led_groups_status:
                            self.led_groups_status[group_name] = {}
                        for led_info in leds:
                            led_num = led_info['led_num']
                            color = led_info['color']
                            self.led_groups_status[group_name][led_num] = color
                    return True
                return False

            except Exception as e:
                print(f"批量设置LED失败: {e}")
                return False

    async def set_single_led(self, led_num: int, color: Union[List[int], str], group_num: int = 0) -> bool:
        """
        设置单个LED灯
        :param led_num: LED编号
        :param color: 颜色值，支持RGB列表或十六进制字符串
        :param group_num: 组号（0或1）
        :return: 设置结果
        """
        group_name = f"group{group_num}"
        led_config = {
            group_name: [{"led_num": led_num, "color": color}]
        }
        return await self.set_leds_batch(led_config)

    async def control_led_legacy(self, led_num: int, color_name: str, group_num: int) -> bool:
        """
        传统方式控制LED（兼容原硬件接口）
        :param led_num: LED编号
        :param color_name: 颜色名称 ('red' 或 'green')
        :param group_num: 组号 (0或1)
        :return: 控制结果
        """
        # 颜色映射
        color_map = {
            'red': [255, 0, 0],
            'green': [0, 255, 0],
            'blue': [0, 0, 255],
            'yellow': [255, 255, 0],
            'white': [255, 255, 255],
            'off': [0, 0, 0]
        }

        if color_name not in color_map:
            raise ValueError(f"不支持的颜色: {color_name}")

        return await self.set_single_led(led_num, color_map[color_name], group_num)

    async def turn_off_all_leds(self) -> bool:
        """关闭所有LED灯"""
        # 获取当前所有已点亮的LED，将它们设置为黑色(关闭)
        led_config = {}

        for group_name, leds in self.led_groups_status.items():
            if leds:  # 如果该组有LED
                led_config[group_name] = []
                for led_num in leds.keys():
                    led_config[group_name].append({
                        'led_num': led_num,
                        'color': [0, 0, 0]  # 黑色 = 关闭
                    })

        if led_config:
            return await self.set_leds_batch(led_config)
        return True

    def get_led_groups_status(self) -> Dict[str, Any]:
        """获取LED组状态"""
        return {
            'device_id': self.device_id,
            'groups': self.led_groups_status.copy(),
            'mock_mode': self.mock
        }