#!/usr/bin/env python3
"""
Test script to verify the CF_API_TOKEN works for GitHub Actions
"""

import os
import requests

def test_github_token():
    """Test the token that will be used in GitHub Actions"""
    token = 'ab51389ad88c525b53ece0c6461526f4a66fa46c58694a866ff6f47f7edfda0f'
    
    print("Testing CF_API_TOKEN for GitHub Actions...")
    print(f"Token: {token[:10]}...{token[-10:]}")
    
    try:
        url = "https://beach-api.terrencefradet.workers.dev/get-subscribers"
        headers = {"X-API-Token": token}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            subscribers = data.get("subscribers", [])
            print(f"✅ SUCCESS! Found {len(subscribers)} subscribers")
            print(f"Subscribers: {subscribers}")
            return True
        else:
            print(f"❌ FAILED! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_github_token() 