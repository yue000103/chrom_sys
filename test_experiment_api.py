#!/usr/bin/env python3
"""
测试实验创建API的脚本
Test script for experiment creation API
"""

import requests
import json
from datetime import datetime

def test_experiment_creation():
    """测试实验创建功能"""

    # 测试数据 - 模拟前端发送的数据
    test_data = {
        "experiment_name": "测试实验001",
        "experiment_type": "standard",
        "method_id": "METHOD_001",
        "operator": "张三",
        "purge_system": True,
        "purge_column": True,
        "purge_column_time_min": 5,
        "column_balance": True,
        "column_balance_time_min": 10,
        "is_peak_driven": False,
        "collection_volume_ml": 2.0,
        "wash_volume_ml": 1.0,
        "wash_cycles": 3,
        "priority": 1,
        "description": "标准测试实验"
    }

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {
        "Content-Type": "application/json"
    }

    print("=" * 50)
    print("Testing experiment creation API")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Method: POST")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print("=" * 50)

    try:
        response = requests.post(url, json=test_data, headers=headers)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 422:
            print("ERROR: 422 Unprocessable Entity!")
            try:
                error_detail = response.json()
                print(f"Error Detail: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"Response Text: {response.text}")
        else:
            print("SUCCESS!")
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print(f"Response Text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

def test_api_health():
    """测试API健康状态"""
    url = "http://0.0.0.0:8008/api/experiment-data/health"

    print("=" * 50)
    print("Testing API health status")
    print("=" * 50)

    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("API health status OK!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("API health check failed!")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Cannot connect to API: {e}")

if __name__ == "__main__":
    # 首先测试健康状态
    test_api_health()
    print("\n")

    # 然后测试实验创建
    test_experiment_creation()