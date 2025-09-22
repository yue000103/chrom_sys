"""
SMILES分子管理器
SMILES Molecule Manager
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from data.database_utils import ChromatographyDB

logger = logging.getLogger(__name__)


class SMILESManager:
    """SMILES分子管理器"""

    def __init__(self):
        self.db = ChromatographyDB()

    def get_all_smiles(self) -> List[Dict[str, Any]]:
        """获取所有SMILES分子信息"""
        try:
            logger.info("获取所有SMILES分子信息")
            smiles_list = self.db.get_smiles_data()
            logger.info(f"获取SMILES分子信息成功，共 {len(smiles_list)} 条记录")
            return smiles_list
        except Exception as e:
            logger.error(f"获取SMILES分子信息失败: {e}")
            return []

    def get_smiles_by_id(self, smiles_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取特定SMILES分子信息"""
        try:
            logger.info(f"获取SMILES分子信息: {smiles_id}")
            smiles_list = self.db.get_smiles_data(smiles_id=smiles_id)
            if smiles_list:
                logger.info(f"获取SMILES分子信息成功: {smiles_list[0].get('compound_name', 'N/A')}")
                return smiles_list[0]
            else:
                logger.warning(f"未找到SMILES分子: {smiles_id}")
                return None
        except Exception as e:
            logger.error(f"获取SMILES分子信息失败: {e}")
            return None

    def create_smiles(self, smiles_data: Dict[str, Any]) -> bool:
        """创建新的SMILES分子记录"""
        try:
            description = smiles_data.get('smiles_description', 'N/A')
            logger.info(f"创建新SMILES分子: {description}")

            # 构建插入数据
            insert_data = {
                'smiles_description': smiles_data.get('smiles_description'),
                'smiles_string': smiles_data.get('smiles_string'),
                'molecular_formula': smiles_data.get('molecular_formula'),
                'molecular_weight': smiles_data.get('molecular_weight'),
                'compound_name': smiles_data.get('compound_name'),
                'cas_number': smiles_data.get('cas_number'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            success = self.db.add_smiles_record(
                smiles_description=insert_data['smiles_description'],
                smiles_string=insert_data['smiles_string'],
                molecular_formula=insert_data['molecular_formula'],
                molecular_weight=insert_data['molecular_weight'],
                compound_name=insert_data['compound_name'],
                cas_number=insert_data['cas_number']
            )

            if success:
                logger.info(f"SMILES分子创建成功: {description}")
            else:
                logger.error(f"SMILES分子创建失败: {description}")

            return success

        except Exception as e:
            logger.error(f"创建SMILES分子时出错: {e}")
            return False

    def update_smiles(self, smiles_id: int, updates: Dict[str, Any]) -> bool:
        """更新SMILES分子信息"""
        try:
            logger.info(f"更新SMILES分子: {smiles_id}")

            # 检查SMILES分子是否存在
            smiles = self.get_smiles_by_id(smiles_id)
            if not smiles:
                raise ValueError(f"SMILES分子不存在: {smiles_id}")

            # 使用数据库工具类的更新方法
            success = self.db.update_smiles_record(smiles_id, **updates)

            if success:
                logger.info(f"SMILES分子更新成功: {smiles_id}")
            else:
                logger.error(f"SMILES分子更新失败: {smiles_id}")

            return success

        except Exception as e:
            logger.error(f"更新SMILES分子时出错: {e}")
            return False

    def delete_smiles(self, smiles_id: int) -> bool:
        """删除SMILES分子"""
        try:
            logger.info(f"删除SMILES分子: {smiles_id}")

            # 检查SMILES分子是否存在
            smiles = self.get_smiles_by_id(smiles_id)
            if not smiles:
                raise ValueError(f"SMILES分子不存在: {smiles_id}")

            # 这里可以检查是否有其他地方引用此SMILES分子
            # 暂时直接删除
            deleted_rows = self.db.delete_data(
                'smiles_management',
                'smiles_id = ?',
                (smiles_id,)
            )

            success = deleted_rows > 0

            if success:
                logger.info(f"SMILES分子删除成功: {smiles_id}")
            else:
                logger.error(f"SMILES分子删除失败: {smiles_id}")

            return success

        except Exception as e:
            logger.error(f"删除SMILES分子时出错: {e}")
            return False

    def search_smiles(self, search_term: Optional[str] = None,
                     compound_name: Optional[str] = None,
                     cas_number: Optional[str] = None,
                     has_smiles_string: Optional[bool] = None,
                     has_molecular_formula: Optional[bool] = None,
                     min_molecular_weight: Optional[float] = None,
                     max_molecular_weight: Optional[float] = None) -> List[Dict[str, Any]]:
        """搜索SMILES分子"""
        try:
            logger.info(f"搜索SMILES分子: term={search_term}, compound={compound_name}")

            # 获取所有SMILES分子
            all_smiles = self.get_all_smiles()

            # 应用过滤条件
            filtered_smiles = all_smiles

            if search_term:
                search_term_lower = search_term.lower()
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if (search_term_lower in smiles.get('smiles_description', '').lower() or
                        search_term_lower in smiles.get('compound_name', '').lower() or
                        search_term_lower in smiles.get('molecular_formula', '').lower())
                ]

            if compound_name:
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if compound_name.lower() in smiles.get('compound_name', '').lower()
                ]

            if cas_number:
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if cas_number == smiles.get('cas_number', '')
                ]

            if has_smiles_string is not None:
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if (smiles.get('smiles_string') is not None and smiles.get('smiles_string').strip()) == has_smiles_string
                ]

            if has_molecular_formula is not None:
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if (smiles.get('molecular_formula') is not None and smiles.get('molecular_formula').strip()) == has_molecular_formula
                ]

            if min_molecular_weight is not None or max_molecular_weight is not None:
                min_weight = min_molecular_weight or 0
                max_weight = max_molecular_weight or float('inf')
                filtered_smiles = [
                    smiles for smiles in filtered_smiles
                    if smiles.get('molecular_weight') is not None and min_weight <= smiles.get('molecular_weight') <= max_weight
                ]

            logger.info(f"搜索SMILES分子完成，找到 {len(filtered_smiles)} 条记录")
            return filtered_smiles

        except Exception as e:
            logger.error(f"搜索SMILES分子失败: {e}")
            return []

    def get_smiles_statistics(self) -> Dict[str, Any]:
        """获取SMILES分子统计信息"""
        try:
            logger.info("获取SMILES分子统计信息")

            all_smiles = self.get_all_smiles()

            # 基本统计
            total_smiles = len(all_smiles)
            has_smiles_string = len([s for s in all_smiles if s.get('smiles_string')])
            has_molecular_formula = len([s for s in all_smiles if s.get('molecular_formula')])
            has_molecular_weight = len([s for s in all_smiles if s.get('molecular_weight')])
            has_cas_number = len([s for s in all_smiles if s.get('cas_number')])

            # 分子量统计
            molecular_weights = [s.get('molecular_weight') for s in all_smiles
                               if s.get('molecular_weight') is not None]
            average_molecular_weight = sum(molecular_weights) / len(molecular_weights) if molecular_weights else None

            # 分子量分布统计
            molecular_weight_distribution = {
                "0-100": 0,
                "100-300": 0,
                "300-500": 0,
                "500-1000": 0,
                "1000+": 0
            }

            for weight in molecular_weights:
                if weight < 100:
                    molecular_weight_distribution["0-100"] += 1
                elif weight < 300:
                    molecular_weight_distribution["100-300"] += 1
                elif weight < 500:
                    molecular_weight_distribution["300-500"] += 1
                elif weight < 1000:
                    molecular_weight_distribution["500-1000"] += 1
                else:
                    molecular_weight_distribution["1000+"] += 1

            # 最近30天新增统计
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            recent_additions = len([
                s for s in all_smiles
                if s.get('created_at') and s.get('created_at') > thirty_days_ago
            ])

            statistics = {
                'total_smiles': total_smiles,
                'has_smiles_string': has_smiles_string,
                'has_molecular_formula': has_molecular_formula,
                'has_molecular_weight': has_molecular_weight,
                'has_cas_number': has_cas_number,
                'average_molecular_weight': round(average_molecular_weight, 2) if average_molecular_weight else None,
                'molecular_weight_distribution': molecular_weight_distribution,
                'recent_additions': recent_additions,
                'timestamp': datetime.now().isoformat()
            }

            logger.info("获取SMILES分子统计信息成功")
            return statistics

        except Exception as e:
            logger.error(f"获取SMILES分子统计信息失败: {e}")
            return {}

    def batch_delete_smiles(self, smiles_ids: List[int]) -> Dict[str, Any]:
        """批量删除SMILES分子"""
        try:
            logger.info(f"批量删除SMILES分子: {len(smiles_ids)} 个")

            processed_count = 0
            failed_count = 0
            failed_items = []

            for smiles_id in smiles_ids:
                try:
                    if self.delete_smiles(smiles_id):
                        processed_count += 1
                    else:
                        failed_count += 1
                        failed_items.append({
                            'smiles_id': smiles_id,
                            'error': '删除失败'
                        })
                except Exception as e:
                    failed_count += 1
                    failed_items.append({
                        'smiles_id': smiles_id,
                        'error': str(e)
                    })

            result = {
                'processed_count': processed_count,
                'failed_count': failed_count,
                'failed_items': failed_items
            }

            logger.info(f"批量删除SMILES分子完成: 成功{processed_count}个，失败{failed_count}个")
            return result

        except Exception as e:
            logger.error(f"批量删除SMILES分子失败: {e}")
            return {
                'processed_count': 0,
                'failed_count': len(smiles_ids),
                'failed_items': [{'error': str(e)}]
            }

    def get_smiles_by_compound_name(self, compound_name: str) -> List[Dict[str, Any]]:
        """根据化合物名称获取SMILES分子"""
        try:
            logger.info(f"根据化合物名称查找SMILES分子: {compound_name}")
            return self.db.get_smiles_data(compound_name=compound_name)
        except Exception as e:
            logger.error(f"根据化合物名称查找SMILES分子失败: {e}")
            return []

    def validate_smiles_string(self, smiles_string: str) -> Dict[str, Any]:
        """验证SMILES字符串"""
        try:
            logger.info(f"验证SMILES字符串: {smiles_string}")

            # 基本格式验证
            import re
            if not re.match(r'^[A-Za-z0-9\[\]()=#+\-\\/@.]*$', smiles_string):
                return {
                    'is_valid': False,
                    'error': 'SMILES字符串包含无效字符'
                }

            # 这里可以集成化学库进行更深入的验证
            # 例如使用rdkit等化学信息学库
            # 暂时返回基本验证结果
            return {
                'is_valid': True,
                'canonical_smiles': smiles_string,  # 暂时返回原字符串
                'message': '基本格式验证通过'
            }

        except Exception as e:
            logger.error(f"验证SMILES字符串失败: {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }