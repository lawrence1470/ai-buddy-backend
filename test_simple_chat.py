#!/usr/bin/env python3

import requests
import json
import time

def test_chat_endpoint():
    """Test the chat endpoint"""
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    # Test cases
    test_cases = [
        {
            "name": "Simple greeting",
            "data": {
                "text": "Hello! How are you?"
            }
        },
        {
            "name": "Voice message",
            "data": {
                "text": "Tell me a joke",
                "is_voice": True
            }
        },
        {
            "name": "With user ID",
            "data": {
                "text": "What's your favorite color?",
                "user_id": "test-user-123"
            }
        }
    ]
    
    print("🚀 Testing Simple Chat Server")
    print("=" * 50)
    
    # Test health endpoint first
    try:
        health_response = requests.get("http://localhost:8080/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Server is healthy!")
            print(f"OpenAI Status: {health_data.get('services', {}).get('openai', 'unknown')}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:8080")
        print("Make sure the server is running with: python3 simple_chat_server.py")
        return
    
    # Test chat endpoint
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                "http://localhost:8080/chat", 
                json=test_case['data'], 
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Success!")
                    print(f"User: {test_case['data']['text']}")
                    print(f"AI:   {data.get('response', 'No response')}")
                    if data.get('tokens_used'):
                        print(f"Tokens: {data['tokens_used']}")
                else:
                    print(f"❌ Failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Error: {response.text}")
                    
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    test_chat_endpoint() 