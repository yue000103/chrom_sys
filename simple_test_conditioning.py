#!/usr/bin/env python3
"""
简化版润柱溶液测试
Simple test for column conditioning solution
"""

import requests
import json

def simple_test():
    """简化测试润柱溶液功能"""

    url = "http://0.0.0.0:8008/api/experiment-data/"
    headers = {"Content-Type": "application/json"}

    print("Testing Column Conditioning Solution Functionality")
    print("=" * 60)

    # 测试所有四种溶液
    solutions = [1, 2, 3, 4]  # A, B, C, D
    successful_tests = 0
    created_experiments = []

    for solution in solutions:
        test_data = {
            "experiment_name": f"Conditioning Solution Test {solution}",
            "experiment_type": "standard",
            "method_id": solution,  # 使用不同的method_id避免重复
            "operator": "Auto Test",
            "column_balance": True,
            "column_balance_time_min": 10,
            "column_conditioning_solution": solution,
            "priority": 3,
            "description": f"Test solution {solution}"
        }

        try:
            response = requests.post(url, json=test_data, headers=headers)
            print(f"Solution {solution}: Status {response.status_code}", end="")

            if response.status_code == 200:
                result = response.json()
                experiment_id = result['experiment']['experiment_id']
                saved_solution = result['experiment'].get('column_conditioning_solution')

                if saved_solution == solution:
                    print(f" - SUCCESS (ID: {experiment_id}, Saved: {saved_solution})")
                    successful_tests += 1
                    created_experiments.append(experiment_id)
                else:
                    print(f" - FAILED (Expected: {solution}, Got: {saved_solution})")
            else:
                print(f" - FAILED")

        except Exception as e:
            print(f"Solution {solution}: ERROR - {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {successful_tests}/4 successful")

    # 清理测试数据
    if created_experiments:
        print("Cleaning up test data...")
        for exp_id in created_experiments:
            try:
                delete_response = requests.delete(f"{url}{exp_id}")
                if delete_response.status_code == 200:
                    print(f"Deleted experiment {exp_id}")
            except:
                pass

    return successful_tests == 4

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\nAll tests passed! Column conditioning solution feature is working correctly.")
    else:
        print("\nSome tests failed. Please check the implementation.")