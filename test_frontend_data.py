#!/usr/bin/env python3
"""
测试前端发送的实际数据格式
Test the actual data format sent by frontend
"""

import requests
import json

def test_frontend_experiment_data():
    """测试前端实际发送的数据格式"""

    # 模拟前端ExperimentManagement.vue中createExperiment函数发送的数据
    frontend_data = {
        "experiment_name": "测试实验001",
        "experiment_type": "standard",
        "method_id": "METHOD_001",
        "operator": "unknown",
        "purge_system": False,
        "purge_column": False,
        "purge_column_time_min": 0,
        "column_balance": False,
        "column_balance_time_min": 0,
        "is_peak_driven": True,  # 从前端逻辑来看，这可能是true
        "collection_volume_ml": 2.0,
        "wash_volume_ml": 1.0,
        "wash_cycles": 3,
        "priority": 1,  # 这里可能是问题所在 - 前端转换的优先级
        "description": None  # 可能是None而不是字符串
    }

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    print("=" * 50)
    print("Testing frontend-style experiment data")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Data: {json.dumps(frontend_data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=frontend_data, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            print("ERROR: 422 Unprocessable Entity!")
            error_detail = response.json()
            print(f"Error Detail: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
        elif response.status_code == 200:
            print("SUCCESS!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

def test_problematic_cases():
    """测试可能导致422的问题情况"""

    test_cases = [
        {
            "name": "Missing required field - experiment_name",
            "data": {
                "experiment_type": "standard",
                "method_id": "METHOD_001"
            }
        },
        {
            "name": "Missing required field - method_id",
            "data": {
                "experiment_name": "测试实验",
                "experiment_type": "standard"
            }
        },
        {
            "name": "Invalid priority value",
            "data": {
                "experiment_name": "测试实验",
                "method_id": "METHOD_001",
                "priority": 15  # 超出范围 (1-10)
            }
        },
        {
            "name": "Invalid time values",
            "data": {
                "experiment_name": "测试实验",
                "method_id": "METHOD_001",
                "purge_column_time_min": -5  # 负值
            }
        }
    ]

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    for case in test_cases:
        print("=" * 50)
        print(f"Testing: {case['name']}")
        print("=" * 50)
        print(f"Data: {json.dumps(case['data'], indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(url, json=case['data'], headers=headers)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 422:
                print("Expected 422 error!")
                error_detail = response.json()
                print(f"Error Detail: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            else:
                print(f"Unexpected result: {response.text}")

        except Exception as e:
            print(f"Error: {e}")

        print()

if __name__ == "__main__":
    test_frontend_experiment_data()
    print("\n" + "=" * 60 + "\n")
    test_problematic_cases()