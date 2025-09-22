#!/usr/bin/env python3
"""
测试新添加的scheduled_start_time和experiment_description字段
Test the newly added scheduled_start_time and experiment_description fields
"""

import requests
import json
from datetime import datetime, timedelta

def test_new_fields():
    """测试新添加的字段"""

    # 测试数据包含新字段
    test_data = {
        "experiment_name": "新字段测试实验",
        "experiment_type": "standard",
        "method_id": "NEW_FIELD_TEST_001",
        "operator": "测试员",
        "purge_system": True,
        "purge_column": True,
        "purge_column_time_min": 5,
        "column_balance": True,
        "column_balance_time_min": 10,
        "is_peak_driven": False,
        "collection_volume_ml": 2.0,
        "wash_volume_ml": 1.0,
        "wash_cycles": 3,
        # 新添加的字段
        "scheduled_start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "priority": 5,
        "description": "简要描述：这是一个测试实验",
        "experiment_description": "详细描述：这个实验用于测试新添加的scheduled_start_time和experiment_description字段是否正常工作。实验目的是验证API能够正确接收和存储这些字段的数据。"
    }

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    print("=" * 70)
    print("测试新添加的字段 (scheduled_start_time & experiment_description)")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"测试数据包含的新字段:")
    print(f"  - scheduled_start_time: {test_data['scheduled_start_time']}")
    print(f"  - experiment_description: {test_data['experiment_description'][:50]}...")
    print("=" * 70)

    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            experiment = result['experiment']
            experiment_id = experiment['experiment_id']

            print("创建成功!")
            print(f"实验ID: {experiment_id}")
            print(f"实验名称: {experiment['experiment_name']}")
            print(f"计划开始时间: {experiment.get('scheduled_start_time', 'None')}")
            print(f"简要描述: {experiment.get('description', 'None')}")
            print(f"详细描述: {experiment.get('experiment_description', 'None')}")

            # 验证字段是否正确保存
            success = True
            if experiment.get('scheduled_start_time') != test_data['scheduled_start_time']:
                print("ERROR: scheduled_start_time 字段不匹配!")
                success = False

            if experiment.get('description') != test_data['description']:
                print("ERROR: description 字段不匹配!")
                success = False

            if experiment.get('experiment_description') != test_data['experiment_description']:
                print("ERROR: experiment_description 字段不匹配!")
                success = False

            if success:
                print("\n✓ 所有新字段都正确保存!")

            # 清理：删除测试实验
            print(f"\n清理测试数据...")
            delete_response = requests.delete(f"{url}{experiment_id}")
            if delete_response.status_code == 200:
                print("✓ 测试数据清理完成")
            else:
                print(f"✗ 清理失败: {delete_response.status_code}")

        elif response.status_code == 422:
            print("验证错误!")
            error_detail = response.json()
            print("错误详情:")
            for error in error_detail['detail']:
                field = '.'.join(str(loc) for loc in error['loc'])
                print(f"  - 字段 {field}: {error['msg']}")
        else:
            print(f"意外的状态码: {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")

def test_without_new_fields():
    """测试不包含新字段的情况"""

    print("\n" + "=" * 70)
    print("测试不包含新字段的向后兼容性")
    print("=" * 70)

    # 测试数据不包含新字段
    test_data = {
        "experiment_name": "向后兼容测试",
        "experiment_type": "standard",
        "method_id": "BACKWARD_COMPAT_001",
        "operator": "测试员",
        "priority": 3,
        "description": "测试向后兼容性"
        # 注意：没有 scheduled_start_time 和 experiment_description
    }

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            experiment = result['experiment']
            experiment_id = experiment['experiment_id']

            print("✓ 向后兼容性测试成功!")
            print(f"实验ID: {experiment_id}")
            print(f"scheduled_start_time: {experiment.get('scheduled_start_time', 'null (默认值)')}")
            print(f"experiment_description: {experiment.get('experiment_description', 'null (默认值)')}")

            # 清理
            delete_response = requests.delete(f"{url}{experiment_id}")
            if delete_response.status_code == 200:
                print("✓ 测试数据清理完成")

        else:
            print(f"✗ 向后兼容性测试失败: {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    test_new_fields()
    test_without_new_fields()

    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)