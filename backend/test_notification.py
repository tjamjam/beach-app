#!/usr/bin/env python3
"""
Simple test script to verify the notification system works.
"""

import os
import requests

# Set the token
os.environ['CF_API_TOKEN'] = 'ab51389ad88c525b53ece0c6461526f4a66fa46c58694a866ff6f47f7edfda0f'

def test_get_subscribers():
    """Test fetching subscribers"""
    print("Testing subscriber fetch...")
    try:
        url = "https://beach-api.terrencefradet.workers.dev/get-subscribers"
        headers = {"X-API-Token": os.environ['CF_API_TOKEN']}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        subscribers = data.get("subscribers", [])
        print(f"✅ Found {len(subscribers)} subscribers: {subscribers}")
        return subscribers
    except Exception as e:
        print(f"❌ Failed to fetch subscribers: {e}")
        return []

def test_notification():
    """Test sending a notification"""
    print("\nTesting notification sending...")
    subscribers = test_get_subscribers()
    
    if subscribers:
        message = "TEST: Lakewood Beach status changed from YELLOW to GREEN. Note: Open"
        print(f"Sending test message: {message}")
        
        # Test ntfy.sh notification
        try:
            response = requests.post(
                "https://ntfy.sh/lakewood-beach-water-quality-report",
                data=message.encode('utf-8'),
                headers={"Title": "Beach Status Change!"}
            )
            print(f"✅ Ntfy.sh notification sent (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Failed to send ntfy.sh notification: {e}")
    else:
        print("❌ No subscribers to test with")

if __name__ == "__main__":
    test_notification() 