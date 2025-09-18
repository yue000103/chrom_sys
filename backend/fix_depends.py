"""
修复所有FastAPI Depends问题
Fix all FastAPI Depends issues
"""

import os
import re

def fix_depends_in_file(file_path):
    """修复文件中的Depends使用"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否需要修复
    if 'Depends()' not in content:
        return False

    modified = False

    # 替换各种管理器的Depends()使用
    replacements = [
        (r'ExperimentFunctionManager\s*=\s*Depends\(\)', '= Depends(get_experiment_manager)'),
        (r'InitializationManager\s*=\s*Depends\(\)', '= Depends(get_init_manager)'),
        (r'DatabaseManager\s*=\s*Depends\(\)', '= Depends(get_db_manager)'),
        (r'ExperimentDataManager\s*=\s*Depends\(\)', '= Depends(get_data_manager)'),
        (r'MethodManager\s*=\s*Depends\(\)', '= Depends(get_method_manager)'),
        (r'TubeManager\s*=\s*Depends\(\)', '= Depends(get_tube_manager)'),
    ]

    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content

    # 确保导入了依赖工厂
    if modified and 'from api.dependencies import' not in content:
        # 在其他导入之后添加依赖导入
        import_section = """
from api.dependencies import (
    get_experiment_manager,
    get_init_manager,
    get_db_manager,
    get_data_manager,
    get_method_manager,
    get_tube_manager
)
"""
        # 找到第一个router定义之前插入
        router_pos = content.find('router = APIRouter')
        if router_pos > 0:
            content = content[:router_pos] + import_section + '\n' + content[router_pos:]

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    return False

def fix_all_routes():
    """修复所有路由文件"""
    fixed_count = 0

    # 修复api目录下的所有routes.py文件
    for root, dirs, files in os.walk('api'):
        for file in files:
            if file == 'routes.py':
                file_path = os.path.join(root, file)
                if fix_depends_in_file(file_path):
                    fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    print("Fixing FastAPI Depends usage...")
    fix_all_routes()
    print("Done!")