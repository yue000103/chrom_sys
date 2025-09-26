#!/usr/bin/env python3
"""
Simple test script for method API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8008"

def test_method_endpoints():
    """Test method API endpoints"""

    # Test 1: Get methods list
    print("=== Testing GET /api/methods/ ===")
    try:
        response = requests.get(f"{BASE_URL}/api/methods/?limit=10")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Create a new method
    print("\n=== Testing POST /api/methods/ ===")
    create_data = {
        "method_name": "测试方法API",
        "column_id": 1,
        "flow_rate_ml_min": 10,
        "run_time_min": 30,
        "detector_wavelength": "254nm",
        "peak_driven": False,
        "gradient_elution_mode": "manual",
        "gradient_time_table": "0:100,30:0",
        "auto_gradient_params": ""
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/methods/",
            json=create_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

            # Get the new method ID for further tests
            if data.get('success') and data.get('method'):
                method_id = data['method'].get('method_id')
                if method_id:
                    test_method_operations(method_id)
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_method_operations(method_id):
    """Test method CRUD operations with a specific method ID"""

    # Test 3: Get method by ID
    print(f"\n=== Testing GET /api/methods/{method_id} ===")
    try:
        response = requests.get(f"{BASE_URL}/api/methods/{method_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 4: Update method
    print(f"\n=== Testing PUT /api/methods/{method_id} ===")
    update_data = {
        "method_name": "测试方法API_更新版",
        "flow_rate_ml_min": 15,
        "run_time_min": 45
    }

    try:
        response = requests.put(
            f"{BASE_URL}/api/methods/{method_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 5: Delete method
    print(f"\n=== Testing DELETE /api/methods/{method_id} ===")
    try:
        response = requests.delete(f"{BASE_URL}/api/methods/{method_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_method_endpoints()