#!/usr/bin/env python3
"""
最终实验API测试
Final comprehensive test for experiment API
"""

import requests
import json

def test_complete_experiment_flow():
    """测试完整的实验流程"""

    base_url = "http://0.0.0.0:8008/api/experiment-data"
    headers = {"Content-Type": "application/json"}

    print("=" * 60)
    print("完整实验API流程测试")
    print("=" * 60)

    # 步骤1: 创建实验
    print("\n1. 创建新实验...")
    create_data = {
        "experiment_name": "API测试实验_最终",
        "experiment_type": "standard",
        "method_id": "TEST_METHOD_001",
        "operator": "测试员",
        "purge_system": True,
        "purge_column": True,
        "purge_column_time_min": 5,
        "column_balance": True,
        "column_balance_time_min": 10,
        "is_peak_driven": False,
        "collection_volume_ml": 2.5,
        "wash_volume_ml": 1.5,
        "wash_cycles": 2,
        "priority": 5,
        "description": "最终API测试实验"
    }

    try:
        response = requests.post(f"{base_url}/", json=create_data, headers=headers)
        print(f"创建状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            experiment_id = result['experiment']['experiment_id']
            print(f"✓ 创建成功! 实验ID: {experiment_id}")
            print(f"实验名称: {result['experiment']['experiment_name']}")

            # 步骤2: 获取实验列表
            print("\n2. 获取实验列表...")
            list_response = requests.get(f"{base_url}/")
            if list_response.status_code == 200:
                list_result = list_response.json()
                print(f"✓ 获取实验列表成功! 总数: {list_result['total_count']}")

                # 步骤3: 根据ID获取实验详情
                print(f"\n3. 获取实验详情 (ID: {experiment_id})...")
                detail_response = requests.get(f"{base_url}/{experiment_id}")
                if detail_response.status_code == 200:
                    detail_result = detail_response.json()
                    print("✓ 获取实验详情成功!")
                    print(f"实验名称: {detail_result['experiment']['experiment_name']}")
                    print(f"状态: {detail_result['experiment']['status']}")
                else:
                    print(f"✗ 获取详情失败: {detail_response.status_code}")
                    print(detail_response.text)
            else:
                print(f"✗ 获取列表失败: {list_response.status_code}")

            # 步骤4: 更新实验
            print(f"\n4. 更新实验 (ID: {experiment_id})...")
            update_data = {
                "experiment_name": "API测试实验_已更新",
                "operator": "更新测试员",
                "priority": 7,
                "status": "running"
            }
            update_response = requests.put(f"{base_url}/{experiment_id}", json=update_data, headers=headers)
            if update_response.status_code == 200:
                update_result = update_response.json()
                print("✓ 更新实验成功!")
                print(f"新名称: {update_result['experiment']['experiment_name']}")
                print(f"新状态: {update_result['experiment']['status']}")
            else:
                print(f"✗ 更新失败: {update_response.status_code}")
                print(update_response.text)

            # 步骤5: 删除实验
            print(f"\n5. 删除实验 (ID: {experiment_id})...")
            delete_response = requests.delete(f"{base_url}/{experiment_id}")
            if delete_response.status_code == 200:
                delete_result = delete_response.json()
                print("✓ 删除实验成功!")
                print(f"消息: {delete_result['message']}")
            else:
                print(f"✗ 删除失败: {delete_response.status_code}")
                print(delete_response.text)

        else:
            print(f"✗ 创建失败: {response.status_code}")
            if response.status_code == 422:
                error_detail = response.json()
                print("验证错误详情:")
                for error in error_detail['detail']:
                    print(f"  - 字段: {error['loc']}, 错误: {error['msg']}")
            else:
                print(response.text)

    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("边界情况测试")
    print("=" * 60)

    base_url = "http://0.0.0.0:8008/api/experiment-data"
    headers = {"Content-Type": "application/json"}

    edge_cases = [
        {
            "name": "最小有效数据",
            "data": {
                "experiment_name": "最小测试",
                "method_id": "MIN_METHOD"
            },
            "expect_success": True
        },
        {
            "name": "优先级边界值 - 最小",
            "data": {
                "experiment_name": "优先级测试1",
                "method_id": "PRIORITY_METHOD",
                "priority": 1
            },
            "expect_success": True
        },
        {
            "name": "优先级边界值 - 最大",
            "data": {
                "experiment_name": "优先级测试10",
                "method_id": "PRIORITY_METHOD",
                "priority": 10
            },
            "expect_success": True
        },
        {
            "name": "优先级越界 - 过大",
            "data": {
                "experiment_name": "优先级测试越界",
                "method_id": "PRIORITY_METHOD",
                "priority": 11
            },
            "expect_success": False
        }
    ]

    for case in edge_cases:
        print(f"\n测试: {case['name']}")
        try:
            response = requests.post(f"{base_url}/", json=case['data'], headers=headers)
            if case['expect_success']:
                if response.status_code == 200:
                    result = response.json()
                    experiment_id = result['experiment']['experiment_id']
                    print(f"✓ 成功创建 (ID: {experiment_id})")
                    # 清理
                    requests.delete(f"{base_url}/{experiment_id}")
                else:
                    print(f"✗ 预期成功但失败: {response.status_code}")
                    print(response.text)
            else:
                if response.status_code == 422:
                    print("✓ 正确返回验证错误")
                else:
                    print(f"✗ 预期422但得到: {response.status_code}")
        except Exception as e:
            print(f"✗ 测试错误: {e}")

if __name__ == "__main__":
    test_complete_experiment_flow()
    test_edge_cases()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)