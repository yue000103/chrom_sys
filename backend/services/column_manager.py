"""
色谱柱管理器
Column Manager
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from data.database_utils import ChromatographyDB

logger = logging.getLogger(__name__)


class ColumnManager:
    """色谱柱管理器"""

    def __init__(self):
        self.db = ChromatographyDB()

    def get_all_columns(self) -> List[Dict[str, Any]]:
        """获取所有色谱柱信息"""
        try:
            logger.info("获取所有色谱柱信息")
            columns = self.db.get_column_info()
            logger.info(f"获取色谱柱信息成功，共 {len(columns)} 条记录")
            return columns
        except Exception as e:
            logger.error(f"获取色谱柱信息失败: {e}")
            return []

    def get_column_by_id(self, column_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取特定色谱柱信息"""
        try:
            logger.info(f"获取色谱柱信息: {column_id}")
            columns = self.db.get_column_info(column_id=column_id)
            if columns:
                logger.info(f"获取色谱柱信息成功: {columns[0].get('column_code', 'N/A')}")
                return columns[0]
            else:
                logger.warning(f"未找到色谱柱: {column_id}")
                return None
        except Exception as e:
            logger.error(f"获取色谱柱信息失败: {e}")
            return None

    def create_column(self, column_data: Dict[str, Any]) -> bool:
        """创建新的色谱柱记录"""
        try:
            column_code = column_data.get('column_code', 'N/A')
            logger.info(f"创建新色谱柱: {column_code}")

            # 构建插入数据 - 只使用数据库中存在的字段
            insert_data = {
                'column_code': column_data.get('column_code'),
                'specification_g': column_data.get('specification_g'),
                'max_pressure_bar': column_data.get('max_pressure_bar'),
                'flow_rate_ml_min': column_data.get('flow_rate_ml_min'),
                'column_volume_cv_ml': column_data.get('column_volume_cv_ml'),
                'sample_load_amount': column_data.get('sample_load_amount')
            }

            success = self.db.insert_data('column_info', insert_data)

            if success:
                logger.info(f"色谱柱创建成功: {column_code}")
            else:
                logger.error(f"色谱柱创建失败: {column_code}")

            return success

        except Exception as e:
            logger.error(f"创建色谱柱时出错: {e}")
            return False

    def update_column(self, column_id: int, updates: Dict[str, Any]) -> bool:
        """更新色谱柱信息"""
        try:
            logger.info(f"更新色谱柱: {column_id}")

            # 检查色谱柱是否存在
            column = self.get_column_by_id(column_id)
            if not column:
                raise ValueError(f"色谱柱不存在: {column_id}")

            # 添加更新时间
            updates['updated_at'] = datetime.now().isoformat()

            # 更新数据库
            affected_rows = self.db.update_data(
                'column_info',
                updates,
                'column_id = ?',
                (column_id,)
            )

            success = affected_rows > 0

            if success:
                logger.info(f"色谱柱更新成功: {column_id}")
            else:
                logger.error(f"色谱柱更新失败: {column_id}")

            return success

        except Exception as e:
            logger.error(f"更新色谱柱时出错: {e}")
            return False

    def delete_column(self, column_id: int) -> bool:
        """删除色谱柱"""
        try:
            logger.info(f"删除色谱柱: {column_id}")

            # 检查色谱柱是否存在
            column = self.get_column_by_id(column_id)
            if not column:
                raise ValueError(f"色谱柱不存在: {column_id}")

            # 检查是否有方法正在使用此色谱柱
            methods = self.db.get_methods()
            using_methods = [m for m in methods if m.get('column_id') == column_id]

            if using_methods:
                method_names = [m.get('method_name', 'N/A') for m in using_methods]
                raise ValueError(f"色谱柱正在被以下方法使用，无法删除: {', '.join(method_names)}")

            # 删除色谱柱
            deleted_rows = self.db.delete_data(
                'column_info',
                'column_id = ?',
                (column_id,)
            )

            success = deleted_rows > 0

            if success:
                logger.info(f"色谱柱删除成功: {column_id}")
            else:
                logger.error(f"色谱柱删除失败: {column_id}")

            return success

        except Exception as e:
            logger.error(f"删除色谱柱时出错: {e}")
            return False

    def get_column_usage_info(self, column_id: int) -> Dict[str, Any]:
        """获取色谱柱使用情况"""
        try:
            logger.info(f"获取色谱柱使用情况: {column_id}")

            column = self.get_column_by_id(column_id)
            if not column:
                raise ValueError(f"色谱柱不存在: {column_id}")

            # 获取使用此色谱柱的方法
            methods = self.db.get_methods()
            using_methods = [m for m in methods if m.get('column_id') == column_id]

            usage_info = {
                'column_id': column_id,
                'column_code': column.get('column_code', 'N/A'),
                'max_pressure_bar': column.get('max_pressure_bar', 0),
                'methods_using_this_column': len(using_methods),
                'method_names': [m.get('method_name', 'N/A') for m in using_methods],
                'created_at': column.get('created_at')
            }

            logger.info(f"获取色谱柱使用情况成功: {column_id}")
            return usage_info

        except Exception as e:
            logger.error(f"获取色谱柱使用情况失败: {e}")
            return {}

    def search_columns(self, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索色谱柱"""
        try:
            logger.info(f"搜索色谱柱: term={search_term}")

            # 获取所有色谱柱
            all_columns = self.get_all_columns()

            # 应用过滤条件
            filtered_columns = all_columns

            if search_term:
                search_term_lower = search_term.lower()
                filtered_columns = [
                    col for col in filtered_columns
                    if (search_term_lower in col.get('column_code', '').lower() or
                        search_term_lower in str(col.get('specification_g', '')).lower() or
                        search_term_lower in col.get('sample_load_amount', '').lower())
                ]

            logger.info(f"搜索色谱柱完成，找到 {len(filtered_columns)} 条记录")
            return filtered_columns

        except Exception as e:
            logger.error(f"搜索色谱柱失败: {e}")
            return []

    def get_column_statistics(self) -> Dict[str, Any]:
        """获取色谱柱统计信息"""
        try:
            logger.info("获取色谱柱统计信息")

            all_columns = self.get_all_columns()

            # 统计各种规格的色谱柱数量
            spec_counts = {}
            pressure_counts = {}

            for column in all_columns:
                # 规格统计
                spec = column.get('specification_g', 'unknown')
                spec_counts[str(spec)] = spec_counts.get(str(spec), 0) + 1

                # 压力统计
                pressure = column.get('max_pressure_bar', 0)
                if pressure:
                    if pressure < 100:
                        pressure_range = "0-100"
                    elif pressure < 300:
                        pressure_range = "100-300"
                    elif pressure < 500:
                        pressure_range = "300-500"
                    else:
                        pressure_range = "500+"
                    pressure_counts[pressure_range] = pressure_counts.get(pressure_range, 0) + 1

            # 获取方法使用情况
            methods = self.db.get_methods()
            column_usage = {}
            for method in methods:
                col_id = method.get('column_id')
                if col_id:
                    column_usage[col_id] = column_usage.get(col_id, 0) + 1

            statistics = {
                'total_columns': len(all_columns),
                'specification_distribution': spec_counts,
                'pressure_distribution': pressure_counts,
                'columns_in_use': len(column_usage),
                'most_used_column_id': max(column_usage.items(), key=lambda x: x[1])[0] if column_usage else None,
                'timestamp': datetime.now().isoformat()
            }

            logger.info("获取色谱柱统计信息成功")
            return statistics

        except Exception as e:
            logger.error(f"获取色谱柱统计信息失败: {e}")
            return {}