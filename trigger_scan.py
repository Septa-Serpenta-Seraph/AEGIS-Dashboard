import requests
import sys

URL = "https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard" if len(sys.argv) < 2 else sys.argv[1]
ENDPOINT = "http://localhost:5000/api/vision/scan"

try:
    print(f"Targeting: {URL}...")
    response = requests.post(ENDPOINT, json={"url": URL})
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("Scan confirmed ✅ delivered to webhook.")
        else:
            print(f"Scan failed ❌ error: {data.get('error')}")
    else:
        print(f"Scan failed ❌ HTTP {response.status_code}")
except Exception as e:
    print(f"Connection failed ❌ {e}")
