#!/usr/bin/env python3
"""
测试API日志功能
"""
import requests
import time

def test_api_logging():
    base_url = "http://localhost:8008"

    print("Testing API logging functionality...")

    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"Error calling root endpoint: {e}")

    time.sleep(1)

    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint: {response.status_code}")
    except Exception as e:
        print(f"Error calling health endpoint: {e}")

    time.sleep(1)

    # 测试一个色谱仪API
    try:
        response = requests.get(f"{base_url}/api/chromatography/methods")
        print(f"Chromatography methods endpoint: {response.status_code}")
    except Exception as e:
        print(f"Error calling chromatography endpoint: {e}")

    print("API logging test completed.")

if __name__ == "__main__":
    test_api_logging()