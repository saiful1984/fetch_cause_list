#!/usr/bin/env python3
"""
Test script for the High Court Cause List API
"""

import requests
import json
import os

# Configuration
API_BASE_URL = "http://localhost:5001"
API_KEY = os.environ.get('API_KEY', 'your-secret-api-key-here')

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")

    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_fetch_cause_list():
    """Test the fetch cause list endpoint."""
    print("🔍 Testing fetch cause list...")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    data = {
        "date": "23052025",
        "side": "Appellate Side",
        "advocate": "Syed Nurul Arefin"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/fetch-cause-list",
                               json=data, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"Date: {result.get('Date')}")
            print(f"Side: {result.get('Side')}")
            print(f"Advocate: {result.get('Advocate')}")
            print(f"Found {len(result.get('Output', []))} cases")

            # Pretty print the full response
            print("\n📋 Full Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ API call failed: {response.json()}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_invalid_api_key():
    """Test with invalid API key."""
    print("🔍 Testing invalid API key...")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "invalid-key"
    }

    data = {
        "date": "23052025",
        "side": "Appellate Side",
        "advocate": "Syed Nurul Arefin"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/fetch-cause-list",
                               json=data, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 401:
            print("✅ Invalid API key correctly rejected")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Unexpected response: {response.json()}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    print()

def test_missing_fields():
    """Test with missing required fields."""
    print("🔍 Testing missing required fields...")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    # Missing advocate field
    data = {
        "date": "23052025",
        "side": "Appellate Side"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/fetch-cause-list",
                               json=data, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 400:
            print("✅ Missing fields correctly rejected")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Unexpected response: {response.json()}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    print()


def test_weekend_or_unavailable_date():
    """Test with a date that should fail (weekend/holiday)."""
    print("🔍 Testing weekend or unavailable date...")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    # Using a date that should fail (24052025 as per user example)
    data = {
        "date": "24052025",
        "side": "Appellate Side",
        "advocate": "Syed Nurul Arefin"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/fetch-cause-list",
                               json=data, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if "Unable to fetch cause_list details due to weekends or failed to fetch cause list" in result.get('Output', []):
                print("✅ Weekend/unavailable date correctly handled")
                print(f"Response: {result}")
            else:
                print(f"❌ Unexpected response: {result}")
        else:
            print(f"❌ Unexpected status code: {response.json()}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    print()


def main():
    """Run all tests."""
    print("🚀 Starting API tests...\n")

    # Test health check first
    if not test_health_check():
        print("❌ Server appears to be down. Make sure the Flask app is running.")
        return

    # Test main functionality
    test_fetch_cause_list()
    print()

    # Test error cases
    test_invalid_api_key()
    test_missing_fields()

    # Test weekend/unavailable date handling
    test_weekend_or_unavailable_date()

    print("🏁 Tests completed!")

if __name__ == "__main__":
    main()
