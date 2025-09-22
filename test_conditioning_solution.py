#!/usr/bin/env python3
"""
测试润柱溶液功能
Test the column conditioning solution functionality
"""

import requests
import json
from datetime import datetime

def test_conditioning_solution_functionality():
    """测试润柱溶液功能"""

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    print("=" * 80)
    print("测试润柱溶液功能 (Column Conditioning Solution)")
    print("=" * 80)

    # 测试四种不同的润柱溶液
    test_cases = [
        {
            "name": "溶液A测试",
            "solution": 1,
            "solution_name": "溶液A"
        },
        {
            "name": "溶液B测试",
            "solution": 2,
            "solution_name": "溶液B"
        },
        {
            "name": "溶液C测试",
            "solution": 3,
            "solution_name": "溶液C"
        },
        {
            "name": "溶液D测试",
            "solution": 4,
            "solution_name": "溶液D"
        }
    ]

    successful_experiments = []

    for case in test_cases:
        print(f"\n{'-' * 40}")
        print(f"测试: {case['name']} (值: {case['solution']})")
        print(f"{'-' * 40}")

        # 创建测试数据
        test_data = {
            "experiment_name": f"润柱溶液测试_{case['solution_name']}",
            "experiment_type": "standard",
            "method_id": 1,
            "operator": "自动测试",
            "purge_system": False,
            "purge_column": False,
            "purge_column_time_min": 0,
            "column_balance": True,  # 启用柱平衡
            "column_balance_time_min": 15,
            "column_conditioning_solution": case['solution'],  # 测试的润柱溶液
            "is_peak_driven": False,
            "collection_volume_ml": 2.0,
            "wash_volume_ml": 1.0,
            "wash_cycles": 2,
            "priority": 5,
            "description": f"测试{case['solution_name']}润柱溶液功能",
            "experiment_description": f"这个实验用于测试{case['solution_name']}作为润柱溶液的功能。实验设置了15分钟的柱平衡时间，使用{case['solution_name']}进行润柱操作。"
        }

        try:
            response = requests.post(url, json=test_data, headers=headers)
            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                experiment = result['experiment']
                experiment_id = experiment['experiment_id']

                print(f"✓ 创建成功! 实验ID: {experiment_id}")
                print(f"实验名称: {experiment['experiment_name']}")
                print(f"柱平衡: {bool(experiment['column_balance'])}")
                print(f"平衡时间: {experiment['column_balance_time_min']}分钟")
                print(f"润柱溶液: {experiment.get('column_conditioning_solution', 'None')}")

                # 验证润柱溶液值是否正确保存
                saved_solution = experiment.get('column_conditioning_solution')
                if saved_solution == case['solution']:
                    print(f"✓ 润柱溶液值正确保存: {saved_solution}")
                    successful_experiments.append({
                        'id': experiment_id,
                        'name': experiment['experiment_name'],
                        'solution': saved_solution
                    })
                else:
                    print(f"✗ 润柱溶液值不匹配! 期望: {case['solution']}, 实际: {saved_solution}")

            elif response.status_code == 422:
                print("✗ 验证错误!")
                error_detail = response.json()
                print("错误详情:")
                for error in error_detail['detail']:
                    field = '.'.join(str(loc) for loc in error['loc'])
                    print(f"  - 字段 {field}: {error['msg']}")
            else:
                print(f"✗ 意外的状态码: {response.status_code}")
                print(f"响应: {response.text}")

        except Exception as e:
            print(f"✗ 测试过程中出现错误: {e}")

    # 总结测试结果
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print(f"测试用例总数: {len(test_cases)}")
    print(f"成功创建的实验: {len(successful_experiments)}")

    if successful_experiments:
        print("\n成功的实验:")
        for exp in successful_experiments:
            print(f"  - ID {exp['id']}: {exp['name']} (溶液: {exp['solution']})")

    # 清理测试数据
    if successful_experiments:
        print(f"\n清理测试数据...")
        for exp in successful_experiments:
            try:
                delete_response = requests.delete(f"{url}{exp['id']}")
                if delete_response.status_code == 200:
                    print(f"✓ 已删除实验 ID {exp['id']}")
                else:
                    print(f"✗ 删除实验 ID {exp['id']} 失败: {delete_response.status_code}")
            except Exception as e:
                print(f"✗ 删除实验 ID {exp['id']} 时出错: {e}")

def test_without_column_balance():
    """测试未启用柱平衡时的情况"""

    print("\n" + "=" * 80)
    print("测试未启用柱平衡的情况")
    print("=" * 80)

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    # 测试数据：column_balance = false，但仍提供 column_conditioning_solution
    test_data = {
        "experiment_name": "未启用柱平衡测试",
        "experiment_type": "standard",
        "method_id": 1,
        "operator": "自动测试",
        "column_balance": False,  # 未启用柱平衡
        "column_balance_time_min": 0,
        "column_conditioning_solution": 2,  # 仍然提供润柱溶液值
        "priority": 3,
        "description": "测试未启用柱平衡时润柱溶液的处理"
    }

    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            experiment = result['experiment']
            experiment_id = experiment['experiment_id']

            print(f"✓ 创建成功! 实验ID: {experiment_id}")
            print(f"柱平衡: {bool(experiment['column_balance'])}")
            print(f"润柱溶液: {experiment.get('column_conditioning_solution', 'None')}")

            # 清理
            delete_response = requests.delete(f"{url}{experiment_id}")
            if delete_response.status_code == 200:
                print(f"✓ 测试数据已清理")

        else:
            print(f"✗ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    test_conditioning_solution_functionality()
    test_without_column_balance()

    print("\n" + "=" * 80)
    print("润柱溶液功能测试完成!")
    print("=" * 80)