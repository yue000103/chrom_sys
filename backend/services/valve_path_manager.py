"""
试管阀门路径管理服务
Tube Valve Path Management Service
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from data.database_utils import ChromatographyDB
from models.valve_path_models import (
    TubeValvePath, DeviceMapping, PathExecutionStep,
    DeviceType, ActionType, ControllerType
)
from hardware.collect_devices.valve_controller import ValveController
from hardware.collect_devices.multi_valve import MultiValveController

logger = logging.getLogger(__name__)


class ValvePathManager:
    """试管阀门路径管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """初始化路径管理器"""
        self.db = ChromatographyDB(db_path)
        self.valve_controller = None
        self.multi_valve_controller = None
        self.device_mappings = {}
        self._load_device_mappings()

    def _load_device_mappings(self):
        """加载设备映射配置"""
        try:
            print(f"正在加载设备映射配置...")
            mappings = self.db.query_data(
                "device_mapping",
                where_condition="is_active = ?",
                where_params=(1,)
            )

            self.device_mappings = {
                mapping['device_code']: mapping for mapping in mappings
            }

            logger.info(f"加载设备映射配置: {len(self.device_mappings)} 个设备")
            print(f"成功加载设备映射: {len(self.device_mappings)} 个设备")

            if self.device_mappings:
                print("设备映射详情:")
                for device_code, mapping in self.device_mappings.items():
                    print(f"  {device_code} -> {mapping.get('physical_id')} ({mapping.get('controller_type')})")

        except Exception as e:
            logger.error(f"加载设备映射配置失败: {e}")
            print(f"加载设备映射配置失败: {e}")
            import traceback
            traceback.print_exc()
            self.device_mappings = {}

    def _get_controller(self, controller_type: str):
        """获取控制器实例"""
        if controller_type == "valve_controller":
            if self.valve_controller is None:
                self.valve_controller = ValveController(mock=True)
            return self.valve_controller
        elif controller_type == "multi_valve_controller":
            if self.multi_valve_controller is None:
                self.multi_valve_controller = MultiValveController(mock=True)
            return self.multi_valve_controller
        else:
            raise ValueError(f"未知的控制器类型: {controller_type}")

    # ===== 试管路径管理 =====

    def get_tube_path(self, module_number: int, tube_number: int) -> List[Dict[str, Any]]:
        """获取指定试管的路径"""
        try:
            print(f"查询试管路径: 模块{module_number}, 试管{tube_number}")
            paths = self.db.query_data(
                "tube_valve_path",
                where_condition="module_number = ? AND tube_number = ?",
                where_params=(module_number, tube_number),
                order_by="sequence_order ASC"
            )

            print(f"找到路径步骤: {len(paths)} 个")
            if paths:
                print("路径详情:")
                for i, path in enumerate(paths):
                    print(f"  步骤{i+1}: {path.get('device_code')} -> {path.get('action_type')} (位置: {path.get('target_position')})")

            return paths

        except Exception as e:
            logger.error(f"获取试管路径失败 (模块{module_number}, 试管{tube_number}): {e}")
            print(f"获取试管路径失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_tube_paths(self, module_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有试管路径"""
        try:
            if module_number:
                where_condition = "module_number = ?"
                where_params = (module_number,)
            else:
                where_condition = None
                where_params = ()

            paths = self.db.query_data(
                "tube_valve_path",
                where_condition=where_condition,
                where_params=where_params,
                order_by="module_number, tube_number, sequence_order ASC"
            )

            return paths

        except Exception as e:
            logger.error(f"获取所有试管路径失败: {e}")
            return []

    def create_tube_path(self, module_number: int, tube_number: int,
                        path_steps: List[Dict[str, Any]]) -> bool:
        """创建试管路径"""
        try:
            # 先删除现有路径
            self.delete_tube_path(module_number, tube_number)

            # 插入新路径步骤
            path_data = []
            for step in path_steps:
                step_data = {
                    'module_number': module_number,
                    'tube_number': tube_number,
                    'sequence_order': step.get('sequence_order'),
                    'device_code': step.get('device_code'),
                    'device_type': step.get('device_type'),
                    'action_type': step.get('action_type'),
                    'target_position': step.get('target_position'),
                    'description': step.get('description'),
                    'is_required': step.get('is_required', True)
                }
                path_data.append(step_data)

            success = self.db.insert_data("tube_valve_path", path_data)

            if success:
                logger.info(f"创建试管路径成功 (模块{module_number}, 试管{tube_number}): {len(path_data)} 步骤")

            return success

        except Exception as e:
            logger.error(f"创建试管路径失败 (模块{module_number}, 试管{tube_number}): {e}")
            return False

    def update_tube_path(self, module_number: int, tube_number: int,
                        path_steps: List[Dict[str, Any]]) -> bool:
        """更新试管路径"""
        return self.create_tube_path(module_number, tube_number, path_steps)

    def delete_tube_path(self, module_number: int, tube_number: int) -> bool:
        """删除试管路径"""
        try:
            deleted = self.db.delete_data(
                "tube_valve_path",
                "module_number = ? AND tube_number = ?",
                (module_number, tube_number)
            )

            if deleted > 0:
                logger.info(f"删除试管路径成功 (模块{module_number}, 试管{tube_number}): {deleted} 步骤")

            return deleted > 0

        except Exception as e:
            logger.error(f"删除试管路径失败 (模块{module_number}, 试管{tube_number}): {e}")
            return False

    # ===== 设备映射管理 =====

    def get_all_device_mappings(self) -> List[Dict[str, Any]]:
        """获取所有设备映射"""
        try:
            mappings = self.db.query_data(
                "device_mapping",
                order_by="device_code ASC"
            )
            return mappings

        except Exception as e:
            logger.error(f"获取设备映射失败: {e}")
            return []

    def get_device_mapping(self, device_code: str) -> Optional[Dict[str, Any]]:
        """获取指定设备映射"""
        try:
            mappings = self.db.query_data(
                "device_mapping",
                where_condition="device_code = ?",
                where_params=(device_code,)
            )

            return mappings[0] if mappings else None

        except Exception as e:
            logger.error(f"获取设备映射失败 ({device_code}): {e}")
            return None

    def create_device_mapping(self, mapping_data: Dict[str, Any]) -> bool:
        """创建设备映射"""
        try:
            success = self.db.insert_data("device_mapping", mapping_data)

            if success:
                logger.info(f"创建设备映射成功: {mapping_data['device_code']}")
                # 重新加载映射配置
                self._load_device_mappings()

            return success

        except Exception as e:
            logger.error(f"创建设备映射失败: {e}")
            return False

    def update_device_mapping(self, device_code: str, updates: Dict[str, Any]) -> bool:
        """更新设备映射"""
        try:
            if 'updated_at' not in updates:
                updates['updated_at'] = datetime.now().isoformat()

            affected = self.db.update_data(
                "device_mapping",
                updates,
                "device_code = ?",
                (device_code,)
            )

            if affected > 0:
                logger.info(f"更新设备映射成功: {device_code}")
                # 重新加载映射配置
                self._load_device_mappings()

            return affected > 0

        except Exception as e:
            logger.error(f"更新设备映射失败 ({device_code}): {e}")
            return False

    def delete_device_mapping(self, device_code: str) -> bool:
        """删除设备映射"""
        try:
            deleted = self.db.delete_data(
                "device_mapping",
                "device_code = ?",
                (device_code,)
            )

            if deleted > 0:
                logger.info(f"删除设备映射成功: {device_code}")
                # 重新加载映射配置
                self._load_device_mappings()

            return deleted > 0

        except Exception as e:
            logger.error(f"删除设备映射失败 ({device_code}): {e}")
            return False

    # ===== 统计信息 =====

    def get_path_statistics(self) -> Dict[str, Any]:
        """获取路径统计信息"""
        try:
            # 统计模块和试管数量
            module_stats = self.db.execute_custom_query("""
                SELECT
                    COUNT(DISTINCT module_number) as total_modules,
                    COUNT(DISTINCT module_number || '_' || tube_number) as total_tubes,
                    COUNT(*) as total_steps
                FROM tube_valve_path
            """)

            # 统计设备类型分布
            device_type_stats = self.db.execute_custom_query("""
                SELECT device_type, COUNT(*) as count
                FROM tube_valve_path
                GROUP BY device_type
                ORDER BY count DESC
            """)

            # 统计动作类型分布
            action_type_stats = self.db.execute_custom_query("""
                SELECT action_type, COUNT(*) as count
                FROM tube_valve_path
                GROUP BY action_type
                ORDER BY count DESC
            """)

            # 统计模块试管分布
            module_tube_stats = self.db.execute_custom_query("""
                SELECT
                    module_number,
                    COUNT(DISTINCT tube_number) as tube_count
                FROM tube_valve_path
                GROUP BY module_number
                ORDER BY module_number
            """)

            return {
                'total_modules': module_stats[0]['total_modules'] if module_stats else 0,
                'total_tubes': module_stats[0]['total_tubes'] if module_stats else 0,
                'total_steps': module_stats[0]['total_steps'] if module_stats else 0,
                'device_type_distribution': {
                    item['device_type']: item['count'] for item in device_type_stats
                },
                'action_type_distribution': {
                    item['action_type']: item['count'] for item in action_type_stats
                },
                'module_tube_distribution': {
                    f"模块{item['module_number']}": item['tube_count']
                    for item in module_tube_stats
                }
            }

        except Exception as e:
            logger.error(f"获取路径统计信息失败: {e}")
            return {}


class ValvePathExecutor:
    """试管阀门路径执行器"""

    def __init__(self, path_manager: ValvePathManager):
        """初始化路径执行器"""
        self.path_manager = path_manager
        self.valve_controller = None
        self.multi_valve_controller = None

    async def execute_tube_path(self, module_number: int, tube_number: int) -> Dict[str, Any]:
        """执行指定试管的路径"""
        start_time = time.time()

        try:
            # 获取路径配置
            path_steps = self.path_manager.get_tube_path(module_number, tube_number)

            if not path_steps:
                return {
                    'success': False,
                    'message': f'试管路径未找到: 模块{module_number}, 试管{tube_number}',
                    'module_number': module_number,
                    'tube_number': tube_number,
                    'total_steps': 0,
                    'success_steps': 0,
                    'step_results': []
                }

            # 执行路径步骤
            step_results = []
            success_count = 0

            for step in path_steps:
                step_result = await self._execute_single_step(step)
                step_results.append(step_result)

                if step_result['success']:
                    success_count += 1
                else:
                    # 如果某步失败且是必需步骤，停止执行
                    if step.get('is_required', True):
                        logger.warning(f"必需步骤失败，停止执行路径: {step_result['error_message']}")
                        break

            execution_time = time.time() - start_time

            result = {
                'success': success_count == len(path_steps),
                'message': f'路径执行完成: {success_count}/{len(path_steps)} 步骤成功',
                'module_number': module_number,
                'tube_number': tube_number,
                'total_steps': len(path_steps),
                'success_steps': success_count,
                'execution_time': round(execution_time, 3),
                'step_results': step_results
            }

            logger.info(f"试管路径执行完成 (模块{module_number}, 试管{tube_number}): "
                       f"{success_count}/{len(path_steps)} 成功, 耗时 {execution_time:.3f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行试管路径失败 (模块{module_number}, 试管{tube_number}): {e}")

            return {
                'success': False,
                'message': f'路径执行异常: {str(e)}',
                'module_number': module_number,
                'tube_number': tube_number,
                'total_steps': 0,
                'success_steps': 0,
                'execution_time': round(execution_time, 3),
                'step_results': []
            }

    async def _execute_single_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个路径步骤"""
        step_start_time = time.time()

        device_code = step['device_code']
        action_type = step['action_type']
        target_position = step.get('target_position')

        print(f"执行步骤: {device_code} -> {action_type} (位置: {target_position})")

        # 查找设备映射
        mapping = self.path_manager.device_mappings.get(device_code)
        if not mapping:
            error_msg = f'设备映射未找到: {device_code}'
            print(f"错误: {error_msg}")
            print(f"可用的设备映射: {list(self.path_manager.device_mappings.keys())}")
            return {
                'sequence_order': step['sequence_order'],
                'device_code': device_code,
                'device_type': step['device_type'],
                'action_type': action_type,
                'target_position': target_position,
                'success': False,
                'physical_id': None,
                'error_message': error_msg,
                'execution_time': 0
            }

        controller_type = mapping['controller_type']
        physical_id = mapping['physical_id']

        try:
            # 获取控制器并执行操作
            controller = self.path_manager._get_controller(controller_type)
            success = False

            if controller_type == "valve_controller":
                success = await self._execute_valve_action(controller, physical_id, action_type)
            elif controller_type == "multi_valve_controller":
                success = await self._execute_multi_valve_action(
                    controller, physical_id, action_type, target_position
                )

            execution_time = time.time() - step_start_time

            return {
                'sequence_order': step['sequence_order'],
                'device_code': device_code,
                'device_type': step['device_type'],
                'action_type': action_type,
                'target_position': target_position,
                'success': success,
                'physical_id': physical_id,
                'error_message': None if success else f'设备操作失败: {physical_id}',
                'execution_time': round(execution_time, 3)
            }

        except Exception as e:
            execution_time = time.time() - step_start_time
            logger.error(f"执行设备操作失败 ({device_code} -> {physical_id}): {e}")

            return {
                'sequence_order': step['sequence_order'],
                'device_code': device_code,
                'device_type': step['device_type'],
                'action_type': action_type,
                'target_position': target_position,
                'success': False,
                'physical_id': physical_id,
                'error_message': str(e),
                'execution_time': round(execution_time, 3)
            }

    async def _execute_valve_action(self, controller, valve_id: str, action: str) -> bool:
        """执行电磁阀/双向阀操作"""
        try:
            if action == 'open':
                result = await controller.control_valve(valve_id, 'open')
            elif action == 'close':
                result = await controller.control_valve(valve_id, 'close')
            elif action == 'start' and valve_id == '泵3':
                result = await controller.control_valve(valve_id, 'start')
            elif action == 'stop' and valve_id == '泵3':
                result = await controller.control_valve(valve_id, 'stop')
            else:
                logger.warning(f"不支持的阀门操作: {action} for {valve_id}")
                return False

            return bool(result)

        except Exception as e:
            logger.error(f"阀门操作异常 ({valve_id}, {action}): {e}")
            return False

    async def _execute_multi_valve_action(self, controller, valve_id: str,
                                        action: str, position: Optional[int]) -> bool:
        """执行多向阀操作"""
        try:
            if action == 'turn_to' and position is not None:
                result = await controller.set_position(valve_id, position)
                return bool(result)
            else:
                logger.warning(f"多向阀操作参数错误: {action}, position={position} for {valve_id}")
                return False

        except Exception as e:
            logger.error(f"多向阀操作异常 ({valve_id}, {action}, {position}): {e}")
            return False

    async def execute_multiple_tube_paths(self, tube_paths: List[Dict[str, int]]) -> Dict[str, Any]:
        """批量执行多个试管路径"""
        start_time = time.time()

        try:
            execution_results = []
            success_count = 0

            for tube_path in tube_paths:
                module_number = tube_path['module_number']
                tube_number = tube_path['tube_number']

                result = await self.execute_tube_path(module_number, tube_number)
                execution_results.append(result)

                if result['success']:
                    success_count += 1

            execution_time = time.time() - start_time

            return {
                'success': success_count == len(tube_paths),
                'message': f'批量路径执行完成: {success_count}/{len(tube_paths)} 路径成功',
                'total_paths': len(tube_paths),
                'success_paths': success_count,
                'failed_paths': len(tube_paths) - success_count,
                'execution_time': round(execution_time, 3),
                'execution_results': execution_results
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"批量执行试管路径失败: {e}")

            return {
                'success': False,
                'message': f'批量路径执行异常: {str(e)}',
                'total_paths': len(tube_paths),
                'success_paths': 0,
                'failed_paths': len(tube_paths),
                'execution_time': round(execution_time, 3),
                'execution_results': []
            }

def create_test_data(path_manager: ValvePathManager) -> bool:
    """创建测试数据"""
    print("创建测试数据...")

    try:
        # 创建设备映射测试数据
        test_mappings = [
            {
                'device_code': 'MV9',
                'device_name': '多向阀9',
                'device_type': 'multi_valve',
                'controller_type': 'multi_valve_controller',
                'physical_id': '多9',
                'is_active': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'device_code': 'V1',
                'device_name': '电磁阀1',
                'device_type': 'valve',
                'controller_type': 'valve_controller',
                'physical_id': '双1',
                'is_active': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'device_code': 'MV4',
                'device_name': '多向阀4',
                'device_type': 'multi_valve',
                'controller_type': 'multi_valve_controller',
                'physical_id': '多4',
                'is_active': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'device_code': 'MV1',
                'device_name': '多向阀1',
                'device_type': 'multi_valve',
                'controller_type': 'multi_valve_controller',
                'physical_id': '多1',
                'is_active': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'device_code': 'MV11',
                'device_name': '多向阀11',
                'device_type': 'multi_valve',
                'controller_type': 'multi_valve_controller',
                'physical_id': '多11',
                'is_active': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]

        for mapping in test_mappings:
            path_manager.create_device_mapping(mapping)

        # 创建试管路径测试数据 - 模块1试管1的动作序列
        test_path_steps = [
            {
                'sequence_order': 1,
                'device_code': 'MV9',
                'device_type': 'multi_valve',
                'action_type': 'turn_to',
                'target_position': 1,
                'description': '多向阀9转到1',
                'is_required': True
            },
            {
                'sequence_order': 2,
                'device_code': 'V1',
                'device_type': 'valve',
                'action_type': 'open',
                'target_position': None,
                'description': '电磁阀1开',
                'is_required': True
            },
            {
                'sequence_order': 3,
                'device_code': 'MV4',
                'device_type': 'multi_valve',
                'action_type': 'turn_to',
                'target_position': 1,
                'description': '多向阀4转到1',
                'is_required': True
            },
            {
                'sequence_order': 4,
                'device_code': 'MV1',
                'device_type': 'multi_valve',
                'action_type': 'turn_to',
                'target_position': 1,
                'description': '多向阀1转到1',
                'is_required': True
            },
            {
                'sequence_order': 5,
                'device_code': 'MV11',
                'device_type': 'multi_valve',
                'action_type': 'turn_to',
                'target_position': 1,
                'description': '多向阀11转到1',
                'is_required': True
            }
        ]

        path_manager.create_tube_path(1, 1, test_path_steps)
        print("测试数据创建完成")
        return True

    except Exception as e:
        print(f"创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import os

    print("开始测试 ValvePathManager...")

    # 检查数据库文件
    db_path = "D:/back/chromatography_system/backend/data/database/chromatography.db"
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")

        # 尝试创建数据库目录
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            print(f"创建数据库目录: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)

        print(f"将使用新建的数据库文件: {db_path}")

    print(f"数据库文件路径: {db_path}")

    try:
        # 初始化管理器和执行器
        print("\n初始化ValvePathManager...")
        path_manager = ValvePathManager(db_path=db_path)
        executor = ValvePathExecutor(path_manager)

        print(f"设备映射数量: {len(path_manager.device_mappings)}")

        # 检查数据库中的数据
        print("\n检查现有数据...")
        all_paths = path_manager.get_all_tube_paths()
        print(f"数据库中总路径数: {len(all_paths)}")

        # 如果没有数据，创建测试数据
        if len(all_paths) == 0 or len(path_manager.device_mappings) == 0:
            print("\n数据库中没有数据，创建测试数据...")
            if create_test_data(path_manager):
                # 重新检查数据
                all_paths = path_manager.get_all_tube_paths()
                print(f"创建测试数据后，路径数: {len(all_paths)}")
                print(f"设备映射数: {len(path_manager.device_mappings)}")

        if all_paths:
            print("前5个路径:")
            for path in all_paths[:5]:
                print(f"  模块{path['module_number']}, 试管{path['tube_number']}, 设备: {path['device_code']}")

        # 获取统计信息
        print("\n获取统计信息...")
        stats = path_manager.get_path_statistics()
        print(f"路径统计: {stats}")

        async def execute():
            print("\n开始执行试管路径测试...")
            result = await executor.execute_tube_path(1, 1)
            print(f"执行结果: {result}")

            # 如果模块1试管1不存在，尝试第一个可用的路径
            if not result['success'] and all_paths:
                first_path = all_paths[0]
                module_num = first_path['module_number']
                tube_num = first_path['tube_number']
                print(f"\n尝试执行第一个可用路径: 模块{module_num}, 试管{tube_num}")
                result2 = await executor.execute_tube_path(module_num, tube_num)
                print(f"执行结果: {result2}")

        # 执行异步测试
        print("\n执行异步测试...")
        asyncio.run(execute())

        print("\n测试完成！")

    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


