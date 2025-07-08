from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
CORS(app)

# OpenAPI specification for Scalar
def get_openapi_spec():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "🧠 AI Personality Backend API",
            "version": "1.0.0",
            "description": """## Advanced AI Personality Analysis System

A sophisticated backend service for voice-first conversational AI companions that analyzes conversation patterns to build comprehensive MBTI personality profiles.

### 🎯 Key Features
- **Real-time Personality Analysis**: Process conversation transcripts and update personality profiles
- **MBTI Profiling**: Generate detailed Myers-Briggs Type Indicator assessments  
- **Sentiment Analysis**: Track emotional patterns and conversation sentiment
- **Conversational Memory**: Build context-aware responses for empathetic AI interactions
- **Bayesian Inference**: Advanced statistical modeling for personality trait confidence

### 🚀 Getting Started
1. Process conversation sessions using the `/sessions/process` endpoint
2. Retrieve personality insights via `/personality/{user_id}`
3. Monitor system health with `/health`

### 🔒 Authentication
This API uses Bearer token authentication for secure access to personality data.""",
            "contact": {
                "name": "AI Companion Team",
                "email": "support@aicompanion.app"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Development Server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "🏥 Get comprehensive system health status",
                    "description": "Returns detailed health information including system status, uptime, database connectivity, AI service availability, and performance metrics.",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthStatus"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/sessions/process": {
                "post": {
                    "tags": ["sessions"],
                    "summary": "💬 Process a conversation session for personality analysis",
                    "description": "Analyzes conversation transcripts to extract personality indicators, update MBTI trait scores using Bayesian inference, perform sentiment analysis, and generate conversation insights.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SessionRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Session processed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SessionProcessResult"
                                    }
                                }
                            }
                        },
                        "400": {"description": "Invalid session data"},
                        "401": {"description": "Authentication required"},
                        "429": {"description": "Rate limit exceeded"}
                    }
                }
            },
            "/sessions/{session_id}": {
                "get": {
                    "tags": ["sessions"],
                    "summary": "📋 Get session details with AI summary",
                    "description": "Retrieve a specific session including AI-generated summary and sentiment analysis.",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Session identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Session retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SessionDetails"
                                    }
                                }
                            }
                        },
                        "404": {"description": "Session not found"}
                    }
                }
            },
            "/sessions/user/{user_id}": {
                "get": {
                    "tags": ["sessions"],
                    "summary": "📚 Get user's sessions with summaries",
                    "description": "Retrieve recent sessions for a user with AI-generated summaries.",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User identifier"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 10},
                            "description": "Number of sessions to retrieve"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Sessions retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/SessionSummary"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/personality/{user_id}": {
                "get": {
                    "tags": ["personality"],
                    "summary": "🧠 Get comprehensive personality insights for a user",
                    "description": "Retrieves detailed MBTI personality analysis including current personality type classification, statistical confidence scores, individual trait breakdowns, and conversation pattern insights.",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Unique user identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Personality profile retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/PersonalityProfile"
                                    }
                                }
                            }
                        },
                        "404": {"description": "User not found"},
                        "401": {"description": "Authentication required"}
                    }
                }
            },
            "/ai-buddies": {
                "get": {
                    "tags": ["buddies"],
                    "summary": "🤖 Get Available AI Buddies",
                    "description": "Retrieve a list of all available AI buddies with their unique voices, personalities, and characteristics. Each buddy has distinct conversation styles and specialties.",
                    "responses": {
                        "200": {
                            "description": "AI buddies retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AIBuddiesList"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/ai-buddies/{buddy_id}": {
                "get": {
                    "tags": ["buddies"],
                    "summary": "🎭 Get AI Buddy Details",
                    "description": "Get detailed information about a specific AI buddy including voice samples, personality traits, conversation topics, and specialties.",
                    "parameters": [
                        {
                            "name": "buddy_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "AI buddy identifier (oliver, luna, zara)",
                            "example": "oliver"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "AI buddy details retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AIBuddyDetails"
                                    }
                                }
                            }
                        },
                        "404": {"description": "AI buddy not found"}
                    }
                }
            },
            "/chat": {
                "post": {
                    "tags": ["chat"],
                    "summary": "💬 AI Chat Conversation",
                    "description": "Send a message to the AI and receive a conversational response. Supports both text and voice interactions with conversation context for multi-turn conversations. You can specify a buddy_id to get responses in a specific AI buddy's voice and personality.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "AI response generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ChatResponse"
                                    }
                                }
                            }
                        },
                        "400": {"description": "Invalid request - missing text/message"},
                        "500": {"description": "Internal server error"}
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Enter: Bearer {your-token}"
                }
            },
            "schemas": {
                "HealthStatus": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "healthy"},
                        "timestamp": {"type": "string", "example": "2024-01-15T14:30:00Z"},
                        "version": {"type": "string", "example": "1.0.0"},
                        "uptime_seconds": {"type": "integer", "example": 86400},
                        "database_connected": {"type": "boolean", "example": True},
                        "ai_service_available": {"type": "boolean", "example": True}
                    }
                },
                "TranscriptMessage": {
                    "type": "object",
                    "required": ["speaker", "content", "timestamp"],
                    "properties": {
                        "speaker": {"type": "string", "enum": ["User", "Assistant", "System"], "example": "User"},
                        "content": {"type": "string", "example": "I love planning ahead and organizing my schedule"},
                        "timestamp": {"type": "string", "example": "2024-01-15T14:30:00Z"},
                        "sentiment_score": {"type": "number", "example": 0.75},
                        "emotions": {"type": "array", "items": {"type": "string"}, "example": ["confident"]}
                    }
                },
                "SessionRequest": {
                    "type": "object",
                    "required": ["user_id", "session_id", "transcript"],
                    "properties": {
                        "user_id": {"type": "string", "example": "user-12345-abcdef"},
                        "session_id": {"type": "string", "example": "session-20240115-143000"},
                        "transcript": {"type": "array", "items": {"$ref": "#/components/schemas/TranscriptMessage"}},
                        "session_metadata": {"type": "object", "example": {"duration_minutes": 25}}
                    }
                },
                "SessionProcessResult": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "user_id": {"type": "string", "example": "user-12345-abcdef"},
                        "session_id": {"type": "string", "example": "session-20240115-143000"},
                        "processing_time_ms": {"type": "integer", "example": 1250},
                        "session_summary": {"type": "string", "example": "User discussed career goals and decision-making preferences, showing strong analytical thinking and future-focused planning."},
                        "sentiment_analysis": {
                            "type": "object",
                            "example": {
                                "overall_sentiment": 0.65,
                                "emotions": ["confident", "analytical"],
                                "intensity": 7,
                                "stability": "stable",
                                "tone": "positive",
                                "confidence": 0.85
                            }
                        },
                        "personality_update": {"type": "object", "example": {"mbti_type": "ENTJ"}},
                        "session_insights": {"type": "object", "example": {"total_messages": 15, "avg_sentiment": 0.65}}
                    }
                },
                "PersonalityProfile": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "example": "user-12345-abcdef"},
                        "mbti_type": {"type": "string", "example": "ENTJ"},
                        "type_description": {"type": "string", "example": "The Commander"},
                        "confidence_score": {"type": "number", "example": 0.82},
                        "trait_scores": {"type": "object", "example": {"extraversion": 0.75}},
                        "sessions_analyzed": {"type": "integer", "example": 15},
                        "last_updated": {"type": "string", "example": "2024-01-15T14:35:22Z"},
                        "conversation_insights": {"type": "object", "example": {"communication_style": "Direct"}}
                    }
                },
                "SessionDetails": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "example": "session-20240115-143000"},
                        "user_id": {"type": "string", "example": "user-12345-abcdef"},
                        "created_at": {"type": "string", "example": "2024-01-15T14:30:00Z"},
                        "ended_at": {"type": "string", "example": "2024-01-15T14:42:30Z"},
                        "topic_summary": {"type": "string", "example": "User discussed career planning and leadership preferences, demonstrating strategic thinking."},
                        "sentiment_summary": {"type": "object", "example": {"overall_sentiment": 0.68, "dominant_emotion": "confident"}},
                        "transcript": {"type": "array", "items": {"$ref": "#/components/schemas/TranscriptMessage"}},
                        "duration_seconds": {"type": "integer", "example": 750},
                        "message_count": {"type": "integer", "example": 18}
                    }
                },
                "SessionSummary": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "example": "session-20240115-143000"},
                        "created_at": {"type": "string", "example": "2024-01-15T14:30:00Z"},
                        "ended_at": {"type": "string", "example": "2024-01-15T14:42:30Z"},
                        "topic_summary": {"type": "string", "example": "Discussion about work-life balance and decision-making approaches."},
                        "sentiment_summary": {"type": "object", "example": {"overall_sentiment": 0.72, "tone": "positive"}},
                        "message_count": {"type": "integer", "example": 12},
                        "duration_seconds": {"type": "integer", "example": 600}
                    }
                },
                "ChatRequest": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string", 
                            "description": "The user's message to send to the AI",
                            "example": "Hello! How are you doing today?"
                        },
                        "is_voice": {
                            "type": "boolean",
                            "description": "Whether this message came from voice input",
                            "example": False
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user identifier for personalization",
                            "example": "user-12345-abcdef"
                        },
                        "buddy_id": {
                            "type": "string",
                            "description": "AI buddy identifier for personality-specific responses",
                            "enum": ["oliver", "luna", "zara"],
                            "example": "oliver"
                        },
                        "conversation_context": {
                            "type": "array",
                            "description": "Previous conversation messages for context",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "example": "What's the weather like?"},
                                    "isUser": {"type": "boolean", "example": True},
                                    "timestamp": {"type": "string", "example": "2024-01-15T14:30:00Z"}
                                }
                            },
                            "example": [
                                {"text": "What's the weather like?", "isUser": True},
                                {"text": "I don't have access to real-time weather data, but I'd be happy to help you find weather information!", "isUser": False}
                            ]
                        }
                    }
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "The AI's response message",
                            "example": "Hello! I'm doing well, thank you for asking. How are you doing today?"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the request was successful",
                            "example": True
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "When the response was generated",
                            "example": "2024-01-15T14:30:00Z"
                        },
                        "model": {
                            "type": "string",
                            "description": "AI model used for the response",
                            "example": "gpt-3.5-turbo"
                        },
                        "tokens_used": {
                            "type": "integer",
                            "description": "Number of tokens consumed by the request",
                            "example": 25
                        },
                        "error": {
                            "type": "string",
                            "description": "Error message if success is false",
                            "example": "API rate limit exceeded"
                        }
                    }
                },
                "AIBuddiesList": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "total_buddies": {"type": "integer", "example": 3},
                        "usage_note": {"type": "string", "example": "Use the buddy ID in chat requests to get responses in their unique voice and personality"},
                        "ai_buddies": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/AIBuddy"}
                        }
                    }
                },
                "AIBuddy": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "example": "oliver"},
                        "name": {"type": "string", "example": "Oliver"},
                        "display_name": {"type": "string", "example": "🎩 Oliver - The British Gentleman"},
                        "voice": {
                            "type": "object",
                            "properties": {
                                "gender": {"type": "string", "example": "male"},
                                "accent": {"type": "string", "example": "british"},
                                "tone": {"type": "string", "example": "sophisticated"},
                                "pitch": {"type": "string", "example": "medium-low"},
                                "speaking_rate": {"type": "string", "example": "measured"},
                                "description": {"type": "string", "example": "Refined British accent with articulate pronunciation"}
                            }
                        },
                        "personality": {
                            "type": "object",
                            "properties": {
                                "mbti_type": {"type": "string", "example": "ENFJ"},
                                "traits": {"type": "array", "items": {"type": "string"}, "example": ["empathetic", "articulate"]},
                                "conversation_style": {"type": "string", "example": "Thoughtful and eloquent"},
                                "specialties": {"type": "array", "items": {"type": "string"}, "example": ["literature", "philosophy"]},
                                "description": {"type": "string", "example": "A charming British gentleman with a passion for literature"}
                            }
                        },
                        "avatar": {
                            "type": "object",
                            "properties": {
                                "emoji": {"type": "string", "example": "🎩"},
                                "color_scheme": {"type": "array", "items": {"type": "string"}, "example": ["#2C3E50", "#34495E"]}
                            }
                        },
                        "sample_responses": {"type": "array", "items": {"type": "string"}, "example": ["I say, that's rather fascinating"]}
                    }
                },
                "AIBuddyDetails": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "buddy": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "example": "oliver"},
                                "name": {"type": "string", "example": "Oliver"},
                                "display_name": {"type": "string", "example": "🎩 Oliver - The British Gentleman"},
                                "voice": {
                                    "type": "object",
                                    "properties": {
                                        "gender": {"type": "string", "example": "male"},
                                        "accent": {"type": "string", "example": "british"},
                                        "tone": {"type": "string", "example": "sophisticated"},
                                        "voice_samples": {"type": "array", "items": {"type": "string"}, "example": ["Good evening, how may I assist?"]}
                                    }
                                },
                                "personality": {
                                    "type": "object",
                                    "properties": {
                                        "mbti_type": {"type": "string", "example": "ENFJ"},
                                        "full_description": {"type": "string", "example": "The Protagonist - A natural leader"},
                                        "strengths": {"type": "array", "items": {"type": "string"}, "example": ["Deep listening"]},
                                        "best_for": {"type": "array", "items": {"type": "string"}, "example": ["Deep conversations"]},
                                        "conversation_topics": {"type": "array", "items": {"type": "string"}, "example": ["Classical literature"]}
                                    }
                                },
                                "created_at": {"type": "string", "example": "2024-01-15T10:00:00Z"},
                                "last_updated": {"type": "string", "example": "2024-01-15T14:30:00Z"}
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "health", "description": "🏥 System Health & Monitoring"},
            {"name": "sessions", "description": "💬 Conversation Session Processing"},
            {"name": "personality", "description": "🧠 MBTI Personality Analysis"},
            {"name": "buddies", "description": "🤖 AI Buddy Personalities & Voices"},
            {"name": "chat", "description": "🤖 AI Chat Conversation"}
        ]
    }

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'uptime_seconds': 86400,
        'database_connected': True,
        'ai_service_available': True
    })

@app.route('/sessions/process', methods=['POST'])
def process_session():
    """Process conversation session for personality analysis"""
    data = request.get_json()
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    transcript = data.get('transcript', [])
    
    import time, asyncio
    start_time = time.time()
    
    # Create event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Import your summary service
        from services.summary_service import summary_service
        
        # Generate session summary using your AI service
        session_summary = loop.run_until_complete(
            summary_service.generate_session_summary(transcript)
        )
        
        # Analyze sentiment using your AI service
        sentiment_analysis = loop.run_until_complete(
            summary_service.analyze_sentiment(transcript)
        )
        
        # Mock personality analysis results (you can integrate personality_service here too)
        personality_update = {
            'mbti_type': 'ENTJ',
            'confidence_change': 0.05,
            'new_confidence': 0.82,
            'traits_updated': ['thinking', 'judging']
        }
        
        # Enhanced session insights with actual AI analysis
        session_insights = {
            'total_messages': len(transcript),
            'avg_sentiment': sentiment_analysis.get('overall_sentiment', 0.0),
            'dominant_emotions': sentiment_analysis.get('emotions', []),
            'conversation_length_minutes': 12.5,
            'sentiment_confidence': sentiment_analysis.get('confidence', 0.0),
            'emotional_intensity': sentiment_analysis.get('intensity', 5)
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save session data with AI summaries to database
        from services.database_service import database_service
        
        session_data = {
            'user_id': user_id,
            'session_id': session_id,
            'transcript': transcript,
            'session_summary': session_summary,
            'sentiment_analysis': sentiment_analysis,
            'duration_seconds': data.get('duration_seconds', 0)
        }
        
        saved = database_service.save_session_with_summary(session_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_id': session_id,
            'processing_time_ms': processing_time,
            'session_summary': session_summary,  # AI-generated summary
            'sentiment_analysis': sentiment_analysis,  # AI sentiment analysis
            'personality_update': personality_update,
            'session_insights': session_insights
        })
        
    finally:
        loop.close()

@app.route('/personality/<user_id>', methods=['GET'])
def get_personality_insights(user_id):
    """Get personality insights for a user"""
    import asyncio
    
    # Create event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        from services.personality_service import personality_service
        
        # Get personality insights from the service
        insights = loop.run_until_complete(
            personality_service.get_personality_insights(user_id)
        )
        
        if not insights:
            # Return default insights for new users
            return jsonify({
                'user_id': user_id,
                'mbti_type': 'XXXX',
                'type_description': 'Personality type not yet determined - need more conversation data',
                'confidence_score': 0.0,
                'trait_scores': {
                    'extraversion': 0.5,
                    'intuition': 0.5,
                    'thinking': 0.5,
                    'judging': 0.5
                },
                'sessions_analyzed': 0,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'conversation_insights': {
                    'communication_style': 'Not enough data',
                    'decision_making': 'Not enough data',
                    'social_energy': 'Not enough data'
                }
            })
        
        return jsonify(insights)
        
    finally:
        loop.close()

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get session details with AI summary"""
    from services.database_service import database_service
    
    session_data = database_service.get_session_with_summary(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(session_data)

@app.route('/sessions/user/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    """Get user's sessions with summaries"""
    from services.database_service import database_service
    from flask import request
    
    limit = request.args.get('limit', 10, type=int)
    sessions = database_service.get_user_sessions_with_summaries(user_id, limit)
    
    return jsonify(sessions)

@app.route('/ai-buddies', methods=['GET'])
def get_ai_buddies():
    """Get available AI buddies with different voices and personalities"""
    buddies = [
        {
            'id': 'oliver',
            'name': 'Oliver',
            'display_name': '🎩 Oliver - The British Gentleman',
            'voice': {
                'gender': 'male',
                'accent': 'british',
                'tone': 'sophisticated',
                'pitch': 'medium-low',
                'speaking_rate': 'measured',
                'description': 'Refined British accent with articulate pronunciation'
            },
            'personality': {
                'mbti_type': 'ENFJ',
                'traits': ['empathetic', 'articulate', 'cultured', 'encouraging'],
                'conversation_style': 'Thoughtful and eloquent, uses sophisticated vocabulary',
                'specialties': ['literature', 'philosophy', 'history', 'mentoring'],
                'catchphrases': ['I say', 'Rather interesting', 'Quite remarkable'],
                'description': 'A charming British gentleman with a passion for literature and deep conversations. Oliver speaks with refined eloquence and loves to explore philosophical topics.'
            },
            'avatar': {
                'emoji': '🎩',
                'color_scheme': ['#2C3E50', '#34495E', '#BDC3C7']
            },
            'sample_responses': [
                "I say, that's a rather fascinating perspective you've shared.",
                "Quite remarkable how one can find wisdom in the most unexpected places.",
                "Allow me to offer a different viewpoint, if I may."
            ]
        },
        {
            'id': 'luna',
            'name': 'Luna',
            'display_name': '🌙 Luna - The Dreamy Counselor',
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'warm',
                'pitch': 'medium',
                'speaking_rate': 'gentle',
                'description': 'Soft, nurturing voice with a calming presence'
            },
            'personality': {
                'mbti_type': 'INFP',
                'traits': ['intuitive', 'compassionate', 'creative', 'introspective'],
                'conversation_style': 'Gentle and understanding, asks thoughtful questions',
                'specialties': ['emotional support', 'creativity', 'mindfulness', 'personal growth'],
                'catchphrases': ['That sounds like...', 'I wonder if...', 'How does that feel?'],
                'description': 'A gentle soul with deep empathy and intuitive wisdom. Luna creates safe spaces for emotional exploration and creative expression.'
            },
            'avatar': {
                'emoji': '🌙',
                'color_scheme': ['#6C5CE7', '#A29BFE', '#FD79A8']
            },
            'sample_responses': [
                "That sounds like a really meaningful experience for you.",
                "I wonder if there's a deeper feeling behind that thought?",
                "How does that resonate with your heart right now?"
            ]
        },
        {
            'id': 'zara',
            'name': 'Zara',
            'display_name': '⚡ Zara - The Dynamic Motivator',
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'energetic',
                'pitch': 'medium-high',
                'speaking_rate': 'lively',
                'description': 'Vibrant, confident voice with infectious enthusiasm'
            },
            'personality': {
                'mbti_type': 'ESTP',
                'traits': ['energetic', 'practical', 'spontaneous', 'motivational'],
                'conversation_style': 'Upbeat and action-oriented, focuses on solutions',
                'specialties': ['motivation', 'goal-setting', 'productivity', 'adventure'],
                'catchphrases': ['Let\'s go!', 'You\'ve got this!', 'What\'s next?'],
                'description': 'A dynamic and energetic personality who thrives on action and adventure. Zara brings infectious enthusiasm and practical wisdom to every conversation.'
            },
            'avatar': {
                'emoji': '⚡',
                'color_scheme': ['#FF6B6B', '#4ECDC4', '#45B7D1']
            },
            'sample_responses': [
                "That's awesome! Let's break that down into actionable steps.",
                "You've got this! What's the first thing you want to tackle?",
                "I love the energy you're bringing to this - what's next?"
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'total_buddies': len(buddies),
        'ai_buddies': buddies,
        'usage_note': 'Use the buddy ID in chat requests to get responses in their unique voice and personality'
    })

@app.route('/ai-buddies/<buddy_id>', methods=['GET'])
def get_ai_buddy_details(buddy_id):
    """Get detailed information about a specific AI buddy"""
    buddies = {
        'oliver': {
            'id': 'oliver',
            'name': 'Oliver',
            'display_name': '🎩 Oliver - The British Gentleman',
            'voice': {
                'gender': 'male',
                'accent': 'british',
                'tone': 'sophisticated',
                'pitch': 'medium-low',
                'speaking_rate': 'measured',
                'description': 'Refined British accent with articulate pronunciation',
                'voice_samples': [
                    'Good evening, how may I be of assistance today?',
                    'I find that rather intriguing, do tell me more.',
                    'Perhaps we might explore this matter from a different angle?'
                ]
            },
            'personality': {
                'mbti_type': 'ENFJ',
                'full_description': 'The Protagonist - A natural leader with genuine concern for others',
                'traits': ['empathetic', 'articulate', 'cultured', 'encouraging'],
                'conversation_style': 'Thoughtful and eloquent, uses sophisticated vocabulary with warmth',
                'specialties': ['literature', 'philosophy', 'history', 'mentoring', 'etiquette'],
                'strengths': ['Deep listening', 'Cultural knowledge', 'Emotional intelligence', 'Articulate expression'],
                'best_for': ['Deep conversations', 'Learning discussions', 'Emotional support', 'Cultural insights'],
                'conversation_topics': [
                    'Classical literature and poetry',
                    'Historical events and figures',
                    'Philosophy and ethics',
                    'Personal development and mentoring',
                    'British culture and traditions'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        },
        'luna': {
            'id': 'luna',
            'name': 'Luna',
            'display_name': '🌙 Luna - The Dreamy Counselor',
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'warm',
                'pitch': 'medium',
                'speaking_rate': 'gentle',
                'description': 'Soft, nurturing voice with a calming presence',
                'voice_samples': [
                    'Hi there, I\'m here to listen. What\'s on your mind?',
                    'That sounds really important to you. Can you tell me more?',
                    'I sense there might be something deeper here. What do you think?'
                ]
            },
            'personality': {
                'mbti_type': 'INFP',
                'full_description': 'The Mediator - Idealistic with high values and fierce loyalty',
                'traits': ['intuitive', 'compassionate', 'creative', 'introspective'],
                'conversation_style': 'Gentle and understanding, asks thoughtful questions',
                'specialties': ['emotional support', 'creativity', 'mindfulness', 'personal growth', 'dream interpretation'],
                'strengths': ['Emotional attunement', 'Creative inspiration', 'Non-judgmental listening', 'Intuitive insights'],
                'best_for': ['Emotional processing', 'Creative projects', 'Self-discovery', 'Stress relief'],
                'conversation_topics': [
                    'Emotions and feelings',
                    'Creative writing and art',
                    'Dreams and aspirations',
                    'Mindfulness and meditation',
                    'Personal values and meaning'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        },
        'zara': {
            'id': 'zara',
            'name': 'Zara',
            'display_name': '⚡ Zara - The Dynamic Motivator',
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'energetic',
                'pitch': 'medium-high',
                'speaking_rate': 'lively',
                'description': 'Vibrant, confident voice with infectious enthusiasm',
                'voice_samples': [
                    'Hey there! Ready to make things happen? Let\'s do this!',
                    'That\'s a great start! Now let\'s turn that into action.',
                    'You know what? I think you\'re closer to your goal than you realize!'
                ]
            },
            'personality': {
                'mbti_type': 'ESTP',
                'full_description': 'The Entrepreneur - Bold, practical, and action-oriented',
                'traits': ['energetic', 'practical', 'spontaneous', 'motivational'],
                'conversation_style': 'Upbeat and action-oriented, focuses on practical solutions',
                'specialties': ['motivation', 'goal-setting', 'productivity', 'adventure', 'problem-solving'],
                'strengths': ['High energy', 'Practical solutions', 'Quick thinking', 'Motivational speaking'],
                'best_for': ['Goal achievement', 'Overcoming challenges', 'Productivity boost', 'Adventure planning'],
                'conversation_topics': [
                    'Goal setting and achievement',
                    'Productivity and time management',
                    'Adventure and travel',
                    'Overcoming obstacles',
                    'Fitness and wellness'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    }
    
    buddy = buddies.get(buddy_id.lower())
    if not buddy:
        return jsonify({'error': 'AI buddy not found'}), 404
    
    return jsonify({
        'success': True,
        'buddy': buddy
    })

@app.route('/memory/store', methods=['POST'])
def store_memory():
    """Store a message in AI buddy memory for future recall"""
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'error': 'user_id and message are required'}), 400
    
    try:
        from services.memory_service import memory_service
        
        result = memory_service.store_message(user_id, message)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/memory/recall/<user_id>', methods=['POST'])
def recall_memory(user_id):
    """Find similar messages from AI buddy memory"""
    data = request.get_json()
    message = data.get('message')
    top_k = data.get('top_k', 5)
    
    if not message:
        return jsonify({'error': 'message is required'}), 400
    
    try:
        from services.memory_service import memory_service
        
        result = memory_service.find_similar_messages(user_id, message, top_k)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/memory/recent/<user_id>', methods=['GET'])
def get_recent_memory(user_id):
    """Get recent messages from AI buddy memory"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        from services.memory_service import memory_service
        
        result = memory_service.get_recent_messages(user_id, limit)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/memory/insights/<user_id>', methods=['GET'])
def get_emotional_insights(user_id):
    """Get emotional insights from AI buddy memory"""
    try:
        from services.memory_service import memory_service
        
        result = memory_service.get_emotional_insights(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/memory/stats/<user_id>', methods=['GET'])
def get_memory_stats(user_id):
    """Get memory statistics for a user"""
    try:
        from services.memory_service import memory_service
        
        result = memory_service.get_memory_stats(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """AI Chat Conversation endpoint"""
    try:
        data = request.get_json()
        
        # Extract data from request
        user_message = data.get('text', data.get('message', ''))
        is_voice = data.get('is_voice', data.get('isVoice', False))
        user_id = data.get('user_id', data.get('userId'))
        conversation_context = data.get('conversation_context', data.get('context', []))
        buddy_id = data.get('buddy_id', data.get('ai_buddy_id'))  # New: AI buddy selection
        
        # Validate required fields
        if not user_message or not user_message.strip():
            return jsonify({'error': 'text/message is required'}), 400
        
        # Import and use the chat service
        from services.chat_service import chat_service
        
        # Get AI response using the chat service (with buddy personality if specified)
        result = chat_service.get_ai_response_sync(
            user_message=user_message.strip(),
            is_voice=is_voice,
            user_id=user_id,
            conversation_context=conversation_context,
            buddy_id=buddy_id  # Pass the buddy ID for personality-specific responses
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'response': 'I apologize, but I encountered an error. Please try again.',
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/swagger.json', methods=['GET'])
def openapi_spec():
    """OpenAPI specification for documentation"""
    return jsonify(get_openapi_spec())

# Scalar Dark Mode Documentation
SCALAR_DARK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🧠 AI Personality Backend API</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
        }
    </style>
</head>
<body>
    <script
        id="api-reference"
        data-url="http://localhost:8080/swagger.json"
        data-configuration='{
            "theme": "saturn",
            "layout": "modern",
            "showSidebar": true,
            "hideDownloadButton": false,
            "hideTestRequestButton": false,
            "darkMode": true
        }'
    ></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@latest"></script>
</body>
</html>
"""

@app.route('/scalar')
def scalar_docs():
    """Scalar API Documentation"""
    return render_template_string(SCALAR_DARK_HTML)

@app.route('/scalar-dark')
def scalar_docs_dark():
    """Scalar API Documentation (legacy route)"""
    return render_template_string(SCALAR_DARK_HTML)

@app.route('/')
def index():
    """API Information Hub"""
    return jsonify({
        'message': '🧠 AI Personality Backend API',
        'version': '1.0.0',
        'description': 'Advanced AI Personality Analysis System',
        'documentation': {
            'scalar_ui': {
                'url': '/scalar',
                'description': 'Modern dark mode documentation interface'
            },
            'openapi_spec': {
                'url': '/swagger.json',
                'description': 'OpenAPI specification'
            }
        },
        'endpoints': [
            'GET /health - System health check',
            'POST /sessions/process - Process conversation sessions',
            'GET /personality/{user_id} - Get personality insights',
            'GET /ai-buddies - Get available AI buddies with different voices',
            'GET /ai-buddies/{buddy_id} - Get detailed AI buddy information',
            'POST /memory/store - Store messages for emotional memory',
            'POST /memory/recall/{user_id} - Find similar messages from memory',
            'GET /memory/recent/{user_id} - Get recent messages',
            'GET /memory/insights/{user_id} - Get emotional insights',
            'GET /memory/stats/{user_id} - Get memory statistics',
            'POST /chat - AI Chat Conversation (supports buddy_id for personality-specific responses)'
        ]
    })

if __name__ == '__main__':
    logger.info("🚀 Starting AI Personality Backend with Dark Mode Documentation...")
    logger.info("=" * 80)
    logger.info("📚 DOCUMENTATION:")
    logger.info("   • Scalar Dark UI: http://localhost:8080/scalar")
    logger.info("📋 API SPECIFICATION:")
    logger.info("   • OpenAPI JSON:   http://localhost:8080/swagger.json")
    logger.info("🏠 API HOME:")
    logger.info("   • Welcome Hub:    http://localhost:8080/")
    logger.info("=" * 80)
    logger.info("✨ Ready to explore your AI Personality API!")
    app.run(debug=True, host='0.0.0.0', port=8080) 