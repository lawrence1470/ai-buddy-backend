#!/usr/bin/env python3

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test the chat endpoint
def test_chat_endpoint():
    """Test the chat endpoint with various inputs"""
    
    # API endpoint
    url = "http://localhost:8000/api/chat"
    
    # Test cases
    test_cases = [
        {
            "name": "Simple text message",
            "data": {
                "text": "Hello, how are you?"
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
            "name": "Message with user ID",
            "data": {
                "text": "What's the weather like?",
                "user_id": "test-user-123"
            }
        },
        {
            "name": "Message with conversation context",
            "data": {
                "text": "And what about tomorrow?",
                "conversation_context": [
                    {"text": "What's the weather like?", "isUser": True},
                    {"text": "I don't have access to real-time weather data, but I'd be happy to help you find weather information!", "isUser": False}
                ]
            }
        }
    ]
    
    print("🚀 Testing Chat Endpoint")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Make request
            response = requests.post(url, json=test_case['data'], timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Success!")
                    print(f"AI Response: {data.get('response', 'No response')}")
                    if data.get('tokens_used'):
                        print(f"Tokens Used: {data['tokens_used']}")
                else:
                    print(f"❌ Request failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Error: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error - Is the server running?")
            print("Start the server with: python3 app.py")
            return False
        except requests.exceptions.Timeout:
            print("❌ Timeout Error - Request took too long")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
    
    return True

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n🏥 Testing Health Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"Status: {data.get('status')}")
            print(f"OpenAI: {data.get('services', {}).get('openai', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Server is not running")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

def main():
    print("🤖 AI Chat Backend Test Suite")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("Make sure to set your OpenAI API key in a .env file")
        print("Example: OPENAI_API_KEY=your-api-key-here")
        return
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("\n🚨 Server appears to be offline")
        print("To start the server, run: python3 app.py")
        return
    
    # Test chat endpoint
    if test_chat_endpoint():
        print("\n🎉 All tests completed!")
        print("\nYour chat endpoint is ready to use!")
        print("Frontend integration example:")
        print("  POST http://localhost:8000/api/chat")
        print("  Body: {'text': 'Hello!', 'is_voice': false}")

if __name__ == "__main__":
    main() 