"""
四合一高压恒流泵控制器
ttyAMA2接口，波特率115200
"""

from typing import Dict, Any, Optional, List
import asyncio
import time
import serial
from ..hardware_config import MockDataGenerator, is_mock_mode


class PumpController:
    """高压恒流泵控制器类"""
    
    def __init__(self, port: str = '/dev/ttyAMA2', baudrate: int = 115200, mock: Optional[bool] = None):
        self.device_id = f'pump_controller_{port.split("/")[-1]}'
        self.port = port
        self.baudrate = baudrate
        self.mock = mock if mock is not None else is_mock_mode(self.device_id)

        # 串口连接
        self.ser = None
        self.is_connected = False

        # 泵状态缓存
        self.pumps = {
            'A': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'B': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'C': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'},
            'D': {'flow_rate': 0.0, 'pressure': 0.0, 'status': 'stopped'}
        }

        # 流动相入口状态 (二进制字符串，如 '1100' 表示 C和B开启)
        self.mobile_phase_inlets = '0000'

        # 四合一泵的ID映射 (A泵=0, B泵=1, C泵=2, D泵=3)
        self.pump_id_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    
    async def connect(self) -> bool:
        """连接泵控制器"""
        return await self._open_serial_port()
    
    async def set_flow_rate(self, pump_id: str, flow_rate: float) -> bool:
        """
        设置流速
        :param pump_id: 泵ID(A/B/C/D)
        :param flow_rate: 流速(mL/min)
        :return: 设置结果
        """
        if pump_id not in self.pumps:
            return False

        if self.mock:
            if 0 <= flow_rate <= 1000:  # 扩大流速范围
                self.pumps[pump_id]['flow_rate'] = flow_rate
                await asyncio.sleep(0.1)
                return True
            return False
        else:
            try:
                # 设定输液泵流量 (单位：ml/min，乘以100转为硬件单位)
                flow_rate_hex = f"{int(flow_rate * 100)}".rjust(6)
                command = b'!FA010' + flow_rate_hex.encode()
                crc = self._calculate_crc(list(command))
                full_command = command + crc.encode() + b'\n'
                response = await self._send_command(full_command)

                if response == b'#':
                    self.pumps[pump_id]['flow_rate'] = flow_rate
                    return True
                return False
            except Exception as e:
                print(f"设置{pump_id}泵流速失败: {e}")
                return False
    
    async def set_gradient(self, gradient_profile: Dict[str, Any]) -> bool:
        """
        设置梯度洗脱（设置流动相比例）
        :param gradient_profile: 梯度参数，格式如 {'A': 50.0, 'B': 30.0, 'C': 20.0, 'D': 0.0}
        :return: 设置结果
        """
        try:
            # 提取四个泵的比例
            proportions = [
                gradient_profile.get('A', 0.0),
                gradient_profile.get('B', 0.0),
                gradient_profile.get('C', 0.0),
                gradient_profile.get('D', 0.0)
            ]

            # 检查比例之和是否为100%
            total = sum(proportions)
            if abs(total - 100.0) > 0.1:  # 允许0.1%的误差
                print(f"梯度比例之和必须为100%，当前为{total}%")
                return False

            if self.mock:
                await asyncio.sleep(0.1)
                return True

            # 根据比例设置流动相入口
            inlets = ''.join(['1' if p > 0 else '0' for p in proportions])
            if not await self._select_mobile_phase_inlets(inlets):
                return False

            # 设置流动相比例
            return await self._set_mobile_phase_proportions(proportions)

        except Exception as e:
            print(f"设置梯度失败: {e}")
            return False
    
    async def start_pump(self, pump_id: str = None, auto_stop_time: int = 0) -> bool:
        """
        启动泵
        :param pump_id: 泵ID(A/B/C/D)，None表示启动所有泵
        :param auto_stop_time: 自动停止时间（秒）
        :return: 启动结果
        """
        if self.mock:
            if pump_id:
                if pump_id in self.pumps:
                    self.pumps[pump_id]['status'] = 'running'
                    self.pumps[pump_id]['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                    await asyncio.sleep(0.2)
                    return True
                return False
            else:
                # 启动所有泵
                for pid in self.pumps:
                    self.pumps[pid]['status'] = 'running'
                    self.pumps[pid]['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                await asyncio.sleep(0.2)
                return True
        else:
            try:
                # 启动泵命令
                command = b'!FA015' + f"{auto_stop_time}".rjust(6).encode()
                crc = self._calculate_crc(list(command))
                full_command = command + crc.encode() + b'\n'
                response = await self._send_command(full_command)

                if response == b'#':
                    if pump_id:
                        self.pumps[pump_id]['status'] = 'running'
                    else:
                        for pid in self.pumps:
                            self.pumps[pid]['status'] = 'running'
                    return True
                return False
            except Exception as e:
                print(f"启动泵失败: {e}")
                return False
    
    async def stop_pump(self, pump_id: str = None) -> bool:
        """
        停止泵
        :param pump_id: 泵ID(A/B/C/D)，None表示停止所有泵
        :return: 停止结果
        """
        if self.mock:
            if pump_id:
                if pump_id in self.pumps:
                    self.pumps[pump_id]['status'] = 'stopped'
                    self.pumps[pump_id]['pressure'] = 0.0
                    await asyncio.sleep(0.1)
                    return True
                return False
            else:
                # 停止所有泵
                for pid in self.pumps:
                    self.pumps[pid]['status'] = 'stopped'
                    self.pumps[pid]['pressure'] = 0.0
                await asyncio.sleep(0.1)
                return True
        else:
            try:
                # 停止泵命令
                command = b'!FA016'
                crc = self._calculate_crc(list(command))
                full_command = command + crc.encode() + b'\n'
                response = await self._send_command(full_command)

                if response == b'#':
                    if pump_id:
                        self.pumps[pump_id]['status'] = 'stopped'
                        self.pumps[pump_id]['pressure'] = 0.0
                    else:
                        for pid in self.pumps:
                            self.pumps[pid]['status'] = 'stopped'
                            self.pumps[pid]['pressure'] = 0.0
                    return True
                return False
            except Exception as e:
                print(f"停止泵失败: {e}")
                return False
    
    async def get_status(self, pump_id: Optional[str] = None) -> Dict[str, Any]:
        """获取泵状态"""
        if self.mock:
            if pump_id:
                if pump_id in self.pumps:
                    pump = self.pumps[pump_id].copy()
                    if pump['status'] == 'running':
                        pump['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                    return {'device_id': self.device_id, 'mode': 'mock', pump_id: pump}
                return {}
            else:
                pumps_status = {}
                for pid, pump in self.pumps.items():
                    pump_copy = pump.copy()
                    if pump_copy['status'] == 'running':
                        pump_copy['pressure'] = MockDataGenerator.generate_pressure(1, 30)
                    pumps_status[pid] = pump_copy
                return {'device_id': self.device_id, 'mode': 'mock', 'pumps': pumps_status}
        else:
            pass
    
    async def purge_system(self) -> bool:
        """系统清洗"""
        pass
    
    async def prime_pump(self, pump_id: str) -> bool:
        """泵预填充"""
        pass
    
    async def disconnect(self) -> bool:
        """断开连接"""
        # 先停止所有泵
        await self.stop_pump()

        # 关闭串口连接
        self._close_serial_port()
        return True

    async def stop_all_pumps(self) -> bool:
        """停止所有泵（向后兼容）"""
        return await self.stop_pump()

    def set_mock_mode(self, mock: bool):
        """设置mock模式"""
        self.mock = mock

    def is_mock_mode(self) -> bool:
        """检查是否为mock模式"""
        return self.mock

    def _calculate_crc(self, data: list) -> str:
        """
        计算CRC校验码
        :param data: 要计算CRC的字节列表
        :return: CRC校验码的ASCII字符串表示
        """
        # 记录缺少几个字符
        space_count = 12 - len(data)

        while len(data) < 12:
            data.append(32)

        total = sum(data)
        crc_value = total % 256
        crc_ascii = f"{crc_value:03}"

        # 添加相应数量的空格
        result = ' ' * space_count + crc_ascii

        return result

    async def _send_command(self, command: bytes) -> bytes:
        """
        发送命令并接收响应（异步版本）
        :param command: 要发送的命令
        :return: 设备的响应
        """
        if self.mock:
            # Mock模式返回成功响应
            await asyncio.sleep(0.01)
            return b'#'

        if not self.ser or not self.ser.is_open:
            raise Exception("串口未连接")

        try:
            # 使用asyncio.to_thread让串口操作异步化
            await asyncio.to_thread(self.ser.write, command)
            response = await asyncio.to_thread(self.ser.readline)
            return response
        except Exception as e:
            print(f"串口通信失败: {e}")
            return b''

    async def _open_serial_port(self) -> bool:
        """
        打开串口连接
        :return: 连接是否成功
        """
        if self.mock:
            self.is_connected = True
            return True

        try:
            self.ser = serial.Serial(
                self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"成功打开串口 {self.port}")
            self.is_connected = True
            return True
        except serial.SerialException as e:
            print(f"无法打开串口 {self.port}: {e}")
            self.is_connected = False
            return False

    def _close_serial_port(self):
        """关闭串口连接"""
        if self.mock:
            self.is_connected = False
            return

        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"成功关闭串口 {self.port}")
        self.is_connected = False

    async def read_product_id(self) -> str:
        """
        读取产品ID号
        :return: 产品ID信息
        """
        if self.mock:
            return "泵类型：四元泵  设备ID：01"

        try:
            command = b'!00001'
            crc = self._calculate_crc(list(command))
            full_command = command + crc.encode() + b'\n'
            response = await self._send_command(full_command)

            if response and response.startswith(b'!'):
                pump_type = response[4:6].decode('ascii').strip()
                product_id = response[10:12].decode('ascii').strip()

                if pump_type in ['01', '00']:
                    return_str = '泵类型：四元泵'
                else:
                    return_str = '泵类型：未知'

                return_str += f'  设备ID：{product_id}'
                return return_str
            else:
                return "读取产品ID失败"
        except Exception as e:
            print(f"读取产品ID失败: {e}")
            return "读取产品ID失败"

    async def _select_mobile_phase_inlets(self, inlets: str) -> bool:
        """
        选择流动相入口
        :param inlets: 流动相入口的二进制标识，例如 '1001' 表示 D和A 开启
        :return: 选择是否成功
        """
        if self.mock:
            self.mobile_phase_inlets = inlets
            await asyncio.sleep(0.05)
            return True

        try:
            decimal_value = int(inlets, 2)
            inlets_hex = hex(decimal_value)[2:].upper()

            self.mobile_phase_inlets = inlets

            command = b'!FA012' + f"{inlets_hex}".rjust(6).encode()
            crc = self._calculate_crc(list(command))
            full_command = command + crc.encode() + b'\n'
            response = await self._send_command(full_command)

            return response == b'#'
        except Exception as e:
            print(f"选择流动相入口失败: {e}")
            return False

    async def _set_mobile_phase_proportions(self, proportions: List[float]) -> bool:
        """
        设定流动相比例
        :param proportions: 流动相比例列表，包含四个0到100之间的数值，表示A、B、C、D泵的比例百分比
        :return: 设定是否成功
        """
        if self.mock:
            await asyncio.sleep(0.05)
            return True

        try:
            if len(proportions) != 4:
                print("错误：流动相比例必须包含4个数值（A、B、C、D）")
                return False

            if abs(sum(proportions) - 100) > 0.1:
                print("错误：流动相比例之和必须为100%")
                return False

            # 转换比例为十六进制格式（乘以10）
            proportions_hex = [f"{hex(int(prop * 10))[2:]}".zfill(3).upper() for prop in proportions]

            # 发送两个命令设置比例
            commands = [
                b'!FA011' + proportions_hex[0].encode() + proportions_hex[1].encode(),
                b'!FA111' + proportions_hex[2].encode() + proportions_hex[3].encode()
            ]

            responses = []
            for command in commands:
                crc = self._calculate_crc(list(command))
                full_command = command + crc.encode() + b'\n'
                response = await self._send_command(full_command)
                responses.append(response == b'#')

            return all(responses)

        except Exception as e:
            print(f"设置流动相比例失败: {e}")
            return False

    async def read_pump_status_hardware(self, pump_id: str) -> tuple:
        """
        从硬件读取泵状态
        :param pump_id: 泵ID(A/B/C/D)
        :return: (状态, 流速) 元组
        """
        if self.mock:
            if pump_id in self.pumps:
                pump = self.pumps[pump_id]
                status = 1 if pump['status'] == 'running' else 0
                return status, pump['flow_rate']
            return 0, 0.0

        try:
            # 将泵ID转换为硬件ID (A=0, B=1, C=2, D=3)
            hardware_id = self.pump_id_map.get(pump_id)
            if hardware_id is None:
                return 0, 0.0

            # 只支持A泵(0)和B泵(1)的状态读取，根据硬件接口文档
            if hardware_id > 1:
                # C和D泵从缓存返回
                pump = self.pumps[pump_id]
                status = 1 if pump['status'] == 'running' else 0
                return status, pump['flow_rate']

            command = b'!FA004'
            crc = self._calculate_crc(list(command))
            full_command = command + crc.encode() + b'\n'
            response = await self._send_command(full_command)

            if response and response.startswith(b'!'):
                if hardware_id == 0:  # A泵
                    status = 1 if int(response[5]) == 1 else 0
                    flow_rate = int(response[6:12].decode('ascii').strip(), 10) / 100
                    return status, flow_rate
                elif hardware_id == 1:  # B泵
                    status = 1 if int(response[12]) == 1 else 0
                    flow_rate = int(response[13:19].decode('ascii').strip(), 10) / 100
                    return status, flow_rate

            return 0, 0.0

        except Exception as e:
            print(f"读取{pump_id}泵状态失败: {e}")
            return 0, 0.0