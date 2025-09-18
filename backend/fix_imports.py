"""
修复所有相对导入问题
Fix all relative import issues
"""

import os
import re

def fix_relative_imports(file_path):
    """修复文件中的相对导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换相对导入为绝对导入
    replacements = [
        (r'from \.\.\.models', 'from models'),
        (r'from \.\.\.services', 'from services'),
        (r'from \.\.\.core', 'from core'),
        (r'from \.\.\.hardware', 'from hardware'),
        (r'from \.\.models', 'from models'),
        (r'from \.\.services', 'from services'),
        (r'from \.\.core', 'from core'),
        (r'from \.\.hardware', 'from hardware'),
    ]

    modified = False
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    return False

def fix_all_imports():
    """修复所有Python文件的导入"""
    fixed_count = 0

    # 修复api目录
    for root, dirs, files in os.walk('api'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_relative_imports(file_path):
                    fixed_count += 1

    # 修复services目录
    for root, dirs, files in os.walk('services'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_relative_imports(file_path):
                    fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    print("Fixing relative imports...")
    fix_all_imports()
    print("Done!")