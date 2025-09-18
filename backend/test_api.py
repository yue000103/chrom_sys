"""
Test API endpoints for detector data
"""
import requests
import json
from time import sleep

base_url = "http://localhost:8008"

print("=" * 60)
print("Testing Detector Data API Endpoints")
print("=" * 60)

# Wait for server to stabilize
sleep(2)

# Test endpoints
endpoints = [
    "/api/data/status",
    "/api/data/latest",
    "/api/data/detector",
    "/api/data/detector/detector_1",
    "/api/data/all-devices",
    "/api/data/publishing-status"
]

for endpoint in endpoints:
    url = base_url + endpoint
    print(f"\nTesting: {endpoint}")
    print("-" * 40)

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print(f"[OK] Status: {response.status_code}")
            data = response.json()

            # Pretty print the response
            if "signal" in str(data):
                print("Response contains signal data:")
                if isinstance(data, dict):
                    if "signal" in data:
                        print(f"  Signal: {data['signal']}")
                    if "wavelength" in data:
                        print(f"  Wavelength: {data['wavelength']}")
                    if "channel_a" in data:
                        print(f"  Channel A: wavelength={data['channel_a']['wavelength']}nm, signal={data['channel_a']['signal']}")
                    if "channel_b" in data:
                        print(f"  Channel B: wavelength={data['channel_b']['wavelength']}nm, signal={data['channel_b']['signal']}")
            else:
                print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Request failed: {e}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)