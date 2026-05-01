#!/usr/bin/env python3
"""Quick test script for API connection."""

import urllib.request
import json
import socket

# Set shorter timeout
socket.setdefaulttimeout(10)

# Setup proxy support
proxy_handler = urllib.request.ProxyHandler()
opener = urllib.request.build_opener(proxy_handler)

api_url = "https://dashboard-api.multimodal-house.fr"

print(f"Testing connection to: {api_url}")
print("-" * 50)

# Test 1: Health check
print("\n1. Testing /health endpoint...")
try:
    req = urllib.request.Request(f"{api_url}/health")
    with opener.open(req, timeout=10) as response:
        print(f"✓ Health check OK (status: {response.status})")
except Exception as e:
    print(f"✗ Health check failed: {e}")

# Test 2: Login
print("\n2. Testing login...")
try:
    data = {
        "email": "admin@admin.admin",
        "password": "admin123"
    }
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        f"{api_url}/api/auth/login",
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )
    with opener.open(req, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"✓ Login successful!")
        print(f"  Token: {result.get('accessToken', '')[:30]}...")
        print(f"  User ID: {result.get('userId')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"✗ Login failed ({e.code}): {error_body}")
except Exception as e:
    print(f"✗ Login error: {e}")

print("\n" + "-" * 50)
print("Test complete")
