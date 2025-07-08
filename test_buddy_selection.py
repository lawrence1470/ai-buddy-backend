#!/usr/bin/env python3
"""
Simple test script to verify buddy selection functionality
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8080"
TEST_USER_ID = "test_user_123"

def test_buddy_selection():
    """Test buddy selection and retrieval"""
    print("Testing Buddy Selection Functionality")
    print("=" * 50)
    
    # Test 1: Select a buddy
    print("\n1. Testing buddy selection...")
    buddy_data = {"buddy_id": "oliver"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/{TEST_USER_ID}/select-buddy",
            json=buddy_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Buddy selection successful: {result}")
        else:
            print(f"✗ Buddy selection failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error selecting buddy: {e}")
        return False
    
    # Test 2: Get selected buddy
    print("\n2. Testing buddy retrieval...")
    
    try:
        response = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}/selected-buddy")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Buddy retrieval successful: {result}")
            
            # Verify the buddy was actually selected
            if result.get('selected_buddy') == 'oliver':
                print("✓ Buddy selection persisted correctly")
            else:
                print(f"✗ Buddy selection not persisted correctly. Expected 'oliver', got: {result.get('selected_buddy')}")
                return False
        else:
            print(f"✗ Buddy retrieval failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error retrieving buddy: {e}")
        return False
    
    # Test 3: Get available buddies
    print("\n3. Testing available buddies...")
    
    try:
        response = requests.get(f"{BASE_URL}/ai-buddies")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Available buddies retrieved: {len(result.get('ai_buddies', []))} buddies")
            
            # Print buddy names
            for buddy in result.get('ai_buddies', []):
                print(f"  - {buddy.get('id')}: {buddy.get('display_name')}")
        else:
            print(f"✗ Available buddies retrieval failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error retrieving available buddies: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All buddy selection tests passed!")
    return True

if __name__ == "__main__":
    success = test_buddy_selection()
    exit(0 if success else 1)