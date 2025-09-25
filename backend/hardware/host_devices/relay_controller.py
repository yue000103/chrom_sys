"""
继电器控制器
控制双2(低压电磁阀)、双1(高压电磁阀)、泵2(气泵)
"""

from typing import Dict, Any, Optional
import asyncio
try:
    from smbus2 import SMBus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
from ..hardware_config import MockDataGenerator, is_mock_mode


class RelayController:
    """继电器控制器类"""

    def __init__(self, mock: Optional[bool] = None):
        self.device_id = 'relay_controller'
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)
        self.connection = None
        self.relays = {
            '双2': {'name': '低压电磁阀', 'status': False, 'param': 1},  # 参数1
            '双1': {'name': '高压电磁阀', 'status': False, 'param': 2},  # 参数2
            '泵2': {'name': '气泵', 'status': False, 'param': 3}        # 参数3
        }

        # MCP23017 I2C配置
        self.i2c_bus = 1
        self.mcp_addr = 0x20
        self.iodira = 0x00    # A端口方向寄存器
        self.iodirb = 0x01    # B端口方向寄存器
        self.gpioa = 0x12     # A端口GPIO输入
        self.gpiob = 0x13     # B端口GPIO输入
        self.olatb = 0x15     # B端口输出锁存器
        self.bus = None
        self.current_state = 0

        # 继电器参数映射表
        self.relay_mapping = {
            '双2': 1,  # 低压电磁阀
            '双1': 2,  # 高压电磁阀
            '泵2': 3   # 气泵
        }

    def _init_i2c(self) -> bool:
        """初始化I2C总线和MCP23017"""
        if not SMBUS_AVAILABLE or self.mock:
            return True

        try:
            if self.bus is None:
                self.bus = SMBus(self.i2c_bus)
                # 配置 A 为输入, B 为输出
                self.bus.write_byte_data(self.mcp_addr, self.iodira, 0xFF)  # 1 = 输入
                self.bus.write_byte_data(self.mcp_addr, self.iodirb, 0x00)  # 0 = 输出
            return True
        except Exception:
            return False

    def _write_open(self, relay_id: int) -> bool:
        """设置指定位为1，保持其他位不变"""
        if relay_id < 1 or relay_id > 8:
            return False

        try:
            if self.mock:
                # Mock模式下，直接修改内部状态
                bit_mask = 1 << (relay_id - 1)
                self.current_state |= bit_mask
                return True
            else:
                if not self._init_i2c():
                    return False

                # 硬件模式下，先读取当前状态，然后修改
                current = self.bus.read_byte_data(self.mcp_addr, self.olatb)
                bit_mask = 1 << (relay_id - 1)
                new_state = current | bit_mask
                self.bus.write_byte_data(self.mcp_addr, self.olatb, new_state)
                self.current_state = new_state
                return True
        except Exception:
            return False

    def _write_close(self, relay_id: int) -> bool:
        """设置指定位为0，保持其他位不变"""
        if relay_id < 1 or relay_id > 8:
            return False

        try:
            if self.mock:
                # Mock模式下，直接修改内部状态
                bit_mask = ~(1 << (relay_id - 1)) & 0xFF
                self.current_state &= bit_mask
                return True
            else:
                if not self._init_i2c():
                    return False

                # 硬件模式下，先读取当前状态，然后修改
                current = self.bus.read_byte_data(self.mcp_addr, self.olatb)
                bit_mask = ~(1 << (relay_id - 1)) & 0xFF
                new_state = current & bit_mask
                self.bus.write_byte_data(self.mcp_addr, self.olatb, new_state)
                self.current_state = new_state
                return True
        except Exception:
            return False

    def _read_relay_state(self, relay_id: int) -> bool:
        """读取指定位的状态"""
        if relay_id < 1 or relay_id > 8:
            return False

        try:
            if self.mock:
                # Mock模式下，从内部状态读取
                return bool((self.current_state >> (relay_id - 1)) & 1)
            else:
                if not self._init_i2c():
                    return False

                # 硬件模式下，从设备读取
                state = self.bus.read_byte_data(self.mcp_addr, self.olatb)
                self.current_state = state
                return bool((state >> (relay_id - 1)) & 1)
        except Exception:
            return False

    async def initialize(self) -> bool:
        """初始化继电器"""
        if self.mock:
            # Mock模式下直接返回成功
            await asyncio.sleep(0.1)  # 模拟初始化延时
            return True
        else:
            # 实际硬件初始化
            init_success = self._init_i2c()
            await asyncio.sleep(0.1)
            return init_success

    async def control_relay(self, relay_id: str, action: str) -> bool:
        """
        控制继电器
        :param relay_id: 继电器ID(双2/双1/泵2)
        :param action: 操作(on/off)
        :return: 操作结果
        """
        if self.mock:
            # Mock模式下模拟控制
            if relay_id in self.relays:
                self.relays[relay_id]['status'] = (action == 'on')
                await asyncio.sleep(0.05)  # 模拟控制延时
                return MockDataGenerator.generate_success_status()
            return False
        else:
            # 实际硬件控制
            if relay_id not in self.relays:
                return False

            param_id = self.relay_mapping.get(relay_id)
            if param_id is None:
                return False

            success = False
            if action == 'on':
                success = self._write_open(param_id)
                if success:
                    self.relays[relay_id]['status'] = True
            elif action == 'off':
                success = self._write_close(param_id)
                if success:
                    self.relays[relay_id]['status'] = False

            await asyncio.sleep(0.05)  # 模拟控制延时
            return success

    async def get_status(self) -> Dict[str, Any]:
        """获取所有继电器状态"""
        if self.mock:
            # Mock模式下返回当前状态
            return {
                'device_id': self.device_id,
                'mode': 'mock',
                'relays': self.relays.copy(),
                'status': MockDataGenerator.generate_device_status()
            }
        else:
            # 实际硬件状态读取
            # 从硬件读取当前所有继电器状态并更新内部状态
            for relay_id, param_id in self.relay_mapping.items():
                if relay_id in self.relays:
                    hardware_status = self._read_relay_state(param_id)
                    self.relays[relay_id]['status'] = hardware_status

            return {
                'device_id': self.device_id,
                'mode': 'hardware',
                'relays': self.relays.copy(),
                'i2c_status': self.current_state,
                'connection_ok': self._init_i2c()
            }

    async def emergency_stop(self) -> bool:
        """紧急停止所有继电器"""
        if self.mock:
            # Mock模式下关闭所有继电器
            for relay_id in self.relays:
                self.relays[relay_id]['status'] = False
            await asyncio.sleep(0.1)  # 模拟操作延时
            return True
        else:
            # 实际硬件紧急停止
            success_count = 0
            total_relays = len(self.relays)

            for relay_id in self.relays:
                try:
                    success = await self.control_relay(relay_id, 'off')
                    if success:
                        success_count += 1
                except Exception:
                    continue

            await asyncio.sleep(0.1)  # 模拟操作延时
            return success_count == total_relays

    def close_connection(self):
        """关闭I2C连接"""
        if not self.mock and hasattr(self, 'bus') and self.bus:
            try:
                self.bus.close()
                self.bus = None
            except Exception:
                pass

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock