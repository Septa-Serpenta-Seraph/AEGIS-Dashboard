#!/usr/bin/env python3
"""
Quick test of AEGIS Dashboard persistence endpoints.
"""
import requests
import json
import time

BASE = "http://localhost:5000"

def test_endpoint(method, path, expected_status=200, **kwargs):
    url = BASE + path
    try:
        if method == 'GET':
            r = requests.get(url, **kwargs)
        elif method == 'POST':
            r = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unknown method {method}")
        print(f"{method} {path} -> {r.status_code}")
        if r.status_code != expected_status:
            print(f"  ERROR: expected {expected_status}, got {r.status_code}")
            print(f"  Response: {r.text[:200]}")
            return False
        data = r.json()
        if not data.get('success', True):
            print(f"  WARNING: success=False, error: {data.get('error', 'unknown')}")
        return True
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return False

def main():
    print("=== AEGIS Dashboard Persistence Test ===")
    
    # Start Flask server if not already running? Assume it's up.
    
    # 1. Health check
    print("\n1. Health check")
    test_endpoint('GET', '/api/health')
    
    # 2. List containers (will trigger snapshot insertion)
    print("\n2. List containers")
    test_endpoint('GET', '/api/containers')
    
    # 3. Get container snapshots history
    print("\n3. Container snapshots history")
    test_endpoint('GET', '/api/persistence/containers/history')
    
    # 4. Get screenshot metadata (should be empty unless screenshots exist)
    print("\n4. Screenshot metadata")
    test_endpoint('GET', '/api/persistence/screenshots')
    
    # 5. If there is a container, get its stats
    print("\n5. Fetch container list to find ID")
    r = requests.get(BASE + '/api/containers')
    if r.status_code == 200:
        containers = r.json().get('containers', [])
        if containers:
            cid = containers[0]['id']
            print(f"   Found container {cid}")
            # Stats collection
            print(f"6. Stats for container {cid}")
            test_endpoint('GET', f'/api/containers/{cid}/stats')
            # Historical stats
            print(f"7. Historical stats for {cid}")
            test_endpoint('GET', f'/api/persistence/stats/{cid}')
        else:
            print("   No containers running, skipping stats tests.")
    
    # 8. TryHackMe mock endpoints
    print("\n8. TryHackMe mock endpoints")
    test_endpoint('GET', '/api/tryhackme/profile')
    test_endpoint('GET', '/api/tryhackme/rooms')
    test_endpoint('GET', '/api/tryhackme/progress')
    
    print("\n=== Test complete ===")

if __name__ == '__main__':
    main()