#!/usr/bin/env python3
"""
AI Buddy Memory Service Test Script

This script demonstrates the memory service functionality including:
- Storing emotional messages
- Finding similar messages
- Getting emotional insights
- Memory statistics

Run this script to test the memory service with sample data.
"""

import os
import sys
import uuid
from datetime import datetime
import json

# Add the current directory to Python path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sample emotional messages for testing
SAMPLE_MESSAGES = [
    "I'm feeling really happy today! The weather is beautiful and I accomplished my goals.",
    "I had a wonderful conversation with my friend about our shared dreams.",
    "I'm a bit anxious about the presentation tomorrow, but I know I've prepared well.",
    "Today was tough. I'm feeling overwhelmed with all the work I have to do.",
    "I'm grateful for my family's support during this challenging time.",
    "I'm excited about starting my new project! It feels like a fresh beginning.",
    "I feel lonely sometimes, especially in the evenings when I'm alone.",
    "I'm proud of myself for overcoming that fear and taking action.",
    "I'm frustrated with how slowly things are progressing in my career.",
    "I feel peaceful when I spend time in nature, it calms my mind.",
    "I'm worried about my friend who's going through a difficult time.",
    "I feel joyful when I listen to my favorite music and dance.",
    "I'm stressed about the upcoming deadline but trying to stay positive.",
    "I'm angry about the injustice I witnessed today, it's not fair.",
    "I feel content with the simple pleasures in life, like a good cup of tea."
]

def test_memory_service():
    """Test the memory service with sample data"""
    
    print("🧠 AI Buddy Memory Service Test")
    print("=" * 50)
    
    try:
        # Import the memory service
        from services.memory_service import memory_service
        
        # Generate a test user ID
        test_user_id = str(uuid.uuid4())
        print(f"📝 Test User ID: {test_user_id}")
        print()
        
        # Step 1: Store sample messages
        print("1️⃣ Storing sample emotional messages...")
        stored_count = 0
        for i, message in enumerate(SAMPLE_MESSAGES, 1):
            print(f"   Storing message {i}/{len(SAMPLE_MESSAGES)}: {message[:50]}...")
            
            result = memory_service.store_message(test_user_id, message)
            
            if result.get('success'):
                stored_count += 1
                print(f"   ✅ Stored successfully (ID: {result['message_id'][:8]}...)")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
        print(f"\n📊 Stored {stored_count}/{len(SAMPLE_MESSAGES)} messages successfully\n")
        
        # Step 2: Test similarity search
        print("2️⃣ Testing similarity search...")
        test_queries = [
            "I'm feeling sad and down",
            "I'm excited about new opportunities",
            "I feel anxious and nervous",
            "I'm grateful for good things"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            result = memory_service.find_similar_messages(test_user_id, query, top_k=3)
            
            if result.get('success'):
                similar_messages = result.get('similar_messages', [])
                print(f"   Found {len(similar_messages)} similar messages:")
                
                for msg in similar_messages:
                    similarity = msg.get('similarity_score', 0)
                    message_text = msg.get('message', '')
                    print(f"   📝 [{similarity:.3f}] {message_text[:60]}...")
            else:
                print(f"   ❌ Error: {result.get('error')}")
        
        # Step 3: Test emotional insights
        print("\n\n3️⃣ Testing emotional insights...")
        
        insights_result = memory_service.get_emotional_insights(test_user_id)
        
        if insights_result.get('success'):
            emotional_messages = insights_result.get('emotional_messages', [])
            print(f"   Found {len(emotional_messages)} emotional messages:")
            
            for msg in emotional_messages[:5]:  # Show top 5
                emotion = msg.get('detected_emotion', 'unknown')
                similarity = msg.get('similarity_score', 0)
                message_text = msg.get('message', '')
                print(f"   😊 [{emotion}] [{similarity:.3f}] {message_text[:50]}...")
        else:
            print(f"   ❌ Error: {insights_result.get('error')}")
        
        # Step 4: Test recent messages
        print("\n\n4️⃣ Testing recent messages retrieval...")
        
        recent_result = memory_service.get_recent_messages(test_user_id, limit=5)
        
        if recent_result.get('success'):
            recent_messages = recent_result.get('messages', [])
            print(f"   Retrieved {len(recent_messages)} recent messages:")
            
            for msg in recent_messages:
                created_at = msg.get('created_at', '')
                message_text = msg.get('message', '')
                print(f"   📅 [{created_at[:19]}] {message_text[:50]}...")
        else:
            print(f"   ❌ Error: {recent_result.get('error')}")
        
        # Step 5: Test memory statistics
        print("\n\n5️⃣ Testing memory statistics...")
        
        stats_result = memory_service.get_memory_stats(test_user_id)
        
        if stats_result.get('success'):
            database_count = stats_result.get('supabase_message_count', 0)
            chroma_count = stats_result.get('chroma_embedding_count', 0)
            storage_sync = stats_result.get('storage_sync', False)
            
            print(f"   📊 Database messages: {database_count}")
            print(f"   🧠 ChromaDB embeddings: {chroma_count}")
            print(f"   🔄 Storage sync: {'✅ Synced' if storage_sync else '❌ Out of sync'}")
        else:
            print(f"   ❌ Error: {stats_result.get('error')}")
        
        print("\n" + "=" * 50)
        print("✨ Memory service test completed!")
        print(f"🎯 Test user ID: {test_user_id}")
        print("   Use this ID to test API endpoints manually")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("   Check your configuration and try again")

def test_api_endpoints():
    """Test the API endpoints with sample requests"""
    
    print("\n🌐 API Endpoints Test")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8080"
        test_user_id = str(uuid.uuid4())
        
        print(f"📝 Test User ID: {test_user_id}")
        print(f"🌍 Base URL: {base_url}")
        print()
        
        # Test storing a message via API
        print("1️⃣ Testing /memory/store endpoint...")
        
        store_data = {
            "user_id": test_user_id,
            "message": "I'm feeling excited about testing this new memory system!"
        }
        
        try:
            response = requests.post(f"{base_url}/memory/store", json=store_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ Message stored successfully!")
                    print(f"   📄 Message ID: {result['message_id']}")
                else:
                    print(f"   ❌ Failed: {result.get('error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Connection Error: {e}")
            print("   Make sure the API server is running on localhost:8080")
        
        # Test memory recall via API
        print("\n2️⃣ Testing /memory/recall endpoint...")
        
        recall_data = {
            "message": "I feel happy and excited",
            "top_k": 3
        }
        
        try:
            response = requests.post(f"{base_url}/memory/recall/{test_user_id}", json=recall_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    similar_messages = result.get('similar_messages', [])
                    print(f"   ✅ Found {len(similar_messages)} similar messages")
                    
                    for msg in similar_messages:
                        similarity = msg.get('similarity_score', 0)
                        message_text = msg.get('message', '')
                        print(f"      📝 [{similarity:.3f}] {message_text[:40]}...")
                else:
                    print(f"   ❌ Failed: {result.get('error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Connection Error: {e}")
        
        print("\n" + "=" * 50)
        print("🌐 API test completed!")
        
    except ImportError:
        print("   ⚠️ requests library not installed")
        print("   Install with: pip install requests")
        print("   Skipping API tests...")

if __name__ == "__main__":
    print("🚀 Starting AI Buddy Memory Service Tests...\n")
    
    # Test 1: Direct service testing
    test_memory_service()
    
    # Test 2: API endpoint testing
    test_api_endpoints()
    
    print("\n🎉 All tests completed!")
    print("\n💡 Next steps:")
    print("   1. Run the API server: python api_docs_app.py")
    print("   2. Visit http://localhost:8080/scalar for API docs")
    print("   3. Test the memory endpoints with your own data") 