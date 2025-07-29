"""
Example usage script for logWise backend API.
"""
import json
import time

import requests

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_containers():
    """Test containers endpoint."""
    print("Testing containers endpoint...")
    response = requests.get(f"{BASE_URL}/api/containers")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        containers = response.json()
        print(f"Found {len(containers)} containers")
        for container in containers[:3]:  # Show first 3
            print(f"  - {container['name']} ({container['status']})")
    else:
        print(f"Error: {response.text}")
    print()

def test_query_suggestions():
    """Test query suggestions."""
    print("Testing query suggestions...")
    container_id = "example_container"
    response = requests.get(f"{BASE_URL}/api/logs/query/suggestions?container_id={container_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        suggestions = response.json()
        print("Suggested questions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
    else:
        print(f"Error: {response.text}")
    print()

def test_query():
    """Test query endpoint."""
    print("Testing query endpoint...")
    query_data = {
        "container_id": "example_container",
        "question": "What errors occurred in the logs?",
        "k": 5
    }
    response = requests.post(f"{BASE_URL}/api/logs/query", json=query_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Query result:")
        print(f"  Answer: {result['answer']}")
        print(f"  References: {len(result['references'])} found")
    else:
        print(f"Error: {response.text}")
    print()

def main():
    """Run all tests."""
    print("logWise Backend API Example Usage")
    print("=" * 40)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    test_health()
    test_containers()
    test_query_suggestions()
    test_query()
    
    print("Example usage completed!")

if __name__ == "__main__":
    main() 