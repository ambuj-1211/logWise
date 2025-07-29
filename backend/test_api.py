#!/usr/bin/env python3
"""
Comprehensive test script for logWise Backend
Run this after starting the backend: python test_backend.py
"""
import asyncio
import json
import time
from typing import Any, Dict

import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None) -> bool:
    """Test an API endpoint and print results"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🔍 Testing {method} {endpoint}")
    print("-" * 50)
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success!")
            try:
                result = response.json()
                print(json.dumps(result, indent=2))
                return True
            except:
                print(response.text)
                return True
        else:
            print("❌ Failed!")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the backend is running!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_backend_startup():
    """Test if backend starts properly"""
    print("🚀 Testing Backend Startup")
    print("=" * 50)
    
    # Test health endpoint
    if not test_endpoint("GET", "/health"):
        return False
    
    # Test root endpoint
    if not test_endpoint("GET", "/"):
        return False
    
    return True

def test_containers_api():
    """Test containers API endpoints"""
    print("\n🐳 Testing Containers API")
    print("=" * 50)
    
    # Test list containers
    if not test_endpoint("GET", "/api/containers"):
        return False
    
    return True

def test_logs_api():
    """Test logs API endpoints"""
    print("\n📝 Testing Logs API")
    print("=" * 50)
    
    # Test log stats
    if not test_endpoint("GET", "/api/logs/stats"):
        return False
    
    return True

def test_query_api():
    """Test query API endpoints"""
    print("\n🤖 Testing Query API")
    print("=" * 50)
    
    # Test log query
    query_data = {
        "container_id": "test_container",
        "question": "Show me recent logs",
        "k": 5
    }
    
    if not test_endpoint("POST", "/api/logs/query", query_data):
        return False
    
    return True

def test_docker_integration():
    """Test Docker integration"""
    print("\n🐳 Testing Docker Integration")
    print("=" * 50)
    
    try:
        import docker
        client = docker.from_env()
        
        # List containers
        containers = client.containers.list()
        print(f"✅ Found {len(containers)} running containers")
        
        for container in containers:
            print(f"  - {container.name} ({container.id[:12]}) - {container.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Docker integration test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Comprehensive logWise Backend Test")
    print("=" * 60)
    
    # Wait a moment for backend to fully start
    print("⏳ Waiting for backend to start...")
    time.sleep(2)
    
    tests = [
        ("Backend Startup", test_backend_startup),
        ("Docker Integration", test_docker_integration),
        ("Containers API", test_containers_api),
        ("Logs API", test_logs_api),
        ("Query API", test_query_api),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 