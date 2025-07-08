#!/usr/bin/env python3
"""
Test script for AI Personality Backend API
This script demonstrates how to use all the API endpoints
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

# Sample transcript for testing
SAMPLE_TRANSCRIPT = [
    {
        "speaker": "User",
        "content": "Hi there! I'm excited to start my new job next week. I've been planning everything out and I have a detailed schedule.",
        "timestamp": "2024-01-01T10:00:00Z"
    },
    {
        "speaker": "AI",
        "content": "That's wonderful! It sounds like you're well-prepared. What are you most looking forward to?",
        "timestamp": "2024-01-01T10:00:05Z"
    },
    {
        "speaker": "User",
        "content": "I love meeting new people and collaborating on projects. I think the team environment will be perfect for me. I tend to think out loud and brainstorm with others.",
        "timestamp": "2024-01-01T10:00:15Z"
    },
    {
        "speaker": "AI",
        "content": "That's great! You seem like a natural collaborator.",
        "timestamp": "2024-01-01T10:00:20Z"
    },
    {
        "speaker": "User",
        "content": "Yeah, I prefer making decisions quickly based on facts and data. I don't like to overthink things - just get the job done efficiently.",
        "timestamp": "2024-01-01T10:00:30Z"
    }
]

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_process_session(user_id="test-user-123"):
    """Test processing a session"""
    print("\n=== Testing Session Processing ===")
    try:
        data = {
            "user_id": user_id,
            "session_id": f"session-{int(time.time())}",
            "transcript": SAMPLE_TRANSCRIPT
        }
        
        response = requests.post(f"{BASE_URL}/api/sessions/process", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Session Summary: {result.get('session_summary', '')[:200]}...")
            print(f"Personality Update: {json.dumps(result.get('personality_update', {}), indent=2)}")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_personality_insights(user_id="test-user-123"):
    """Test getting personality insights"""
    print("\n=== Testing Personality Insights ===")
    try:
        response = requests.get(f"{BASE_URL}/api/personality/{user_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            insights = response.json()
            print(f"MBTI Type: {insights.get('mbti_type')}")
            print(f"Description: {insights.get('type_description')}")
            print(f"Overall Confidence: {insights.get('confidence', {}).get('overall', 0):.2f}")
            print(f"Sessions Analyzed: {insights.get('sessions_analyzed', 0)}")
            print(f"Facet Bars: {json.dumps(insights.get('facet_bars', []), indent=2)}")
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code in [200, 404]  # 404 is OK if no profile exists yet
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_personality_type(user_id="test-user-123"):
    """Test getting just the personality type"""
    print("\n=== Testing Personality Type ===")
    try:
        response = requests.get(f"{BASE_URL}/api/personality/{user_id}/type")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            type_info = response.json()
            print(f"MBTI Type: {type_info.get('mbti_type')}")
            print(f"Description: {type_info.get('type_description')}")
            print(f"Confidence: {type_info.get('overall_confidence', 0):.2f}")
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_facets(user_id="test-user-123"):
    """Test getting personality facets"""
    print("\n=== Testing Personality Facets ===")
    try:
        response = requests.get(f"{BASE_URL}/api/personality/{user_id}/facets")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            facets = response.json()
            print(f"MBTI Type: {facets.get('mbti_type')}")
            for bar in facets.get('facet_bars', []):
                print(f"  {bar['name']}: {bar['score']:.2f} ({bar['label']}) - Confidence: {bar['confidence']:.2f}")
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generate_summary():
    """Test generating a summary"""
    print("\n=== Testing Summary Generation ===")
    try:
        data = {"transcript": SAMPLE_TRANSCRIPT}
        response = requests.post(f"{BASE_URL}/api/analytics/summary", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Summary: {result.get('summary', '')[:200]}...")
            print(f"Sentiment: {json.dumps(result.get('sentiment', {}), indent=2)}")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_recent_memory(user_id="test-user-123"):
    """Test getting recent memory"""
    print("\n=== Testing Recent Memory ===")
    try:
        response = requests.get(f"{BASE_URL}/api/memory/{user_id}/recent?hours=72")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            memory = response.json()
            print(f"Personality Type: {memory.get('personality_type')}")
            print(f"Recent Sessions: {len(memory.get('recent_sessions', []))}")
            print(f"Recent Evidence: {len(memory.get('recent_evidence', []))}")
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting AI Personality Backend API Tests")
    print("=" * 50)
    
    user_id = f"test-user-{int(time.time())}"
    tests = [
        ("Health Check", lambda: test_health_check()),
        ("Process Session", lambda: test_process_session(user_id)),
        ("Get Personality Insights", lambda: test_get_personality_insights(user_id)),
        ("Get Personality Type", lambda: test_get_personality_type(user_id)),
        ("Get Personality Facets", lambda: test_get_facets(user_id)),
        ("Generate Summary", lambda: test_generate_summary()),
        ("Get Recent Memory", lambda: test_get_recent_memory(user_id)),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        success = test_func()
        results.append((test_name, success))
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AI Personality Backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs and configuration.")

if __name__ == "__main__":
    run_all_tests() 