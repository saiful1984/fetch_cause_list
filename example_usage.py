#!/usr/bin/env python3
"""
Example usage of the High Court Cause List API
"""

import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:5001"
API_KEY = "your-secret-api-key-here"

def fetch_cause_list(date, side, advocate, base_url=None):
    """
    Fetch cause list for a specific advocate.
    
    Args:
        date (str): Date in DDMMYYYY format (e.g., "23052025")
        side (str): Either "Original Side" or "Appellate Side"
        advocate (str): Full name of the advocate
        base_url (str, optional): Court website base URL
    
    Returns:
        dict: API response containing case data
    """
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    data = {
        "date": date,
        "side": side,
        "advocate": advocate
    }
    
    if base_url:
        data["base_url"] = base_url
    
    try:
        response = requests.post(f"{API_BASE_URL}/fetch-cause-list", 
                               json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error ({response.status_code}): {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Example usage of the API."""
    
    print("📋 High Court Cause List API - Example Usage\n")
    
    # Example 1: Fetch cause list for Syed Nurul Arefin
    print("🔍 Example 1: Fetching cause list for Syed Nurul Arefin")
    result = fetch_cause_list(
        date="23052025",
        side="Appellate Side", 
        advocate="Syed Nurul Arefin"
    )
    
    if result:
        print(f"✅ Found {len(result['Output'])} cases")
        print(f"📅 Date: {result['Date']}")
        print(f"⚖️  Side: {result['Side']}")
        print(f"👨‍💼 Advocate: {result['Advocate']}")
        print(f"🌐 Court URL: {result['Court_URL']}")
        
        print("\n📄 Cases:")
        for i, case in enumerate(result['Output'], 1):
            print(f"\n--- Case {i} ---")
            print(case)
    
    print("\n" + "="*50)
    
    # Example 2: Try with a different advocate (likely no results)
    print("\n🔍 Example 2: Trying with a different advocate")
    result2 = fetch_cause_list(
        date="23052025",
        side="Original Side",
        advocate="John Doe"
    )
    
    if result2:
        if result2['Output']:
            print(f"✅ Found {len(result2['Output'])} cases for John Doe")
        else:
            print("ℹ️  No cases found for John Doe")
    
    print("\n🏁 Example completed!")

if __name__ == "__main__":
    main()
