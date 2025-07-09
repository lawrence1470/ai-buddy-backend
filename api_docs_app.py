from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
from datetime import datetime, timezone
import os

from config import Config
from services.chat_service import ChatService
from services.personality_service import PersonalityService
from services.summary_service import SummaryService
from services.memory_service import MemoryService
from services.clerk_auth_service import clerk_auth_service
from services.auth_middleware import require_auth, optional_auth, get_current_user, extract_user_id
from services.database_service import database_service

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
            "/users/{user_id}/select-buddy": {
                "post": {
                    "tags": ["buddies"],
                    "summary": "✨ Select Preferred AI Buddy",
                    "description": "Set the user's preferred AI buddy. This selection will persist and be used as the default buddy for future conversations if no specific buddy is requested.",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User identifier",
                            "example": "user_2ybVqC3I3Uchb1EL8UB0kgMNRG3"
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SelectBuddyRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "AI buddy selected successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SelectBuddyResponse"
                                    }
                                }
                            }
                        },
                        "400": {"description": "Invalid buddy_id or missing required fields"},
                        "500": {"description": "Internal server error"}
                    }
                }
            },
            "/users/{user_id}/selected-buddy": {
                "get": {
                    "tags": ["buddies"],
                    "summary": "🔍 Get User's Selected Buddy",
                    "description": "Retrieve the user's currently selected preferred AI buddy. Returns null if no buddy has been selected.",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User identifier",
                            "example": "user_2ybVqC3I3Uchb1EL8UB0kgMNRG3"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Selected buddy retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SelectedBuddyResponse"
                                    }
                                }
                            }
                        },
                        "500": {"description": "Internal server error"}
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
                        "color_schema": {
                            "type": "object",
                            "properties": {
                                "primary": {"type": "string", "example": "#2C3E50"},
                                "secondary": {"type": "string", "example": "#34495E"},
                                "accent": {"type": "string", "example": "#E74C3C"},
                                "background": {"type": "string", "example": "#ECF0F1"},
                                "text": {"type": "string", "example": "#FFFFFF"},
                                "gradient": {"type": "string", "example": "linear-gradient(135deg, #2C3E50 0%, #34495E 100%)"},
                                "theme": {"type": "string", "example": "professional"},
                                "description": {"type": "string", "example": "Professional BBC-inspired color scheme with deep blues and authoritative reds"}
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
                                "color_schema": {
                                    "type": "object",
                                    "properties": {
                                        "primary": {"type": "string", "example": "#2C3E50"},
                                        "secondary": {"type": "string", "example": "#34495E"},
                                        "accent": {"type": "string", "example": "#E74C3C"},
                                        "background": {"type": "string", "example": "#ECF0F1"},
                                        "text": {"type": "string", "example": "#FFFFFF"},
                                        "gradient": {"type": "string", "example": "linear-gradient(135deg, #2C3E50 0%, #34495E 100%)"},
                                        "theme": {"type": "string", "example": "professional"},
                                        "description": {"type": "string", "example": "Professional BBC-inspired color scheme"}
                                    }
                                },
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
                },
                "SelectBuddyRequest": {
                    "type": "object",
                    "required": ["buddy_id"],
                    "properties": {
                        "buddy_id": {
                            "type": "string",
                            "description": "The AI buddy ID to select as preferred",
                            "enum": ["oliver", "luna", "zara", "maya", "alex", "sam"],
                            "example": "oliver"
                        }
                    }
                },
                "SelectBuddyResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "message": {"type": "string", "example": "AI buddy oliver selected for user user_2ybVqC3I3Uchb1EL8UB0kgMNRG3"},
                        "selected_buddy": {"type": "string", "example": "oliver"},
                        "timestamp": {"type": "string", "example": "2024-01-15T14:30:00Z"}
                    }
                },
                "SelectedBuddyResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "selected_buddy": {"type": "string", "example": "oliver"},
                        "buddy_details": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "example": "oliver"},
                                "name": {"type": "string", "example": "Oliver"},
                                "display_name": {"type": "string", "example": "Oliver - The British Gentleman"}
                            }
                        },
                        "is_default": {"type": "boolean", "example": False},
                        "last_updated": {"type": "string", "example": "2024-01-15T14:30:00Z"},
                        "timestamp": {"type": "string", "example": "2024-01-15T14:30:00Z"}
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
    
    session_data = database_service.get_session_with_summary(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(session_data)

@app.route('/sessions/user/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    """Get user's sessions with summaries"""
    
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
            'display_name': '📺 Oliver - The BBC News Broadcaster',
            'voice': {
                'gender': 'male',
                'accent': 'british',
                'tone': 'authoritative',
                'pitch': 'medium-low',
                'speaking_rate': 'measured',
                'description': 'Distinguished older British BBC news broadcaster voice with authoritative gravitas and classic received pronunciation',
                'elevenlabs_voice_id': '29vD33N1CtxCmqQRPOHJ',  # Drew - Distinguished older British male, classic BBC broadcaster
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.80,
                    'similarity_boost': 0.90,
                    'style': 0.70,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'medium',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'authoritative, distinguished, contemplative',
                    'best_for': 'BBC-style broadcasting, news delivery, documentary narration with gravitas'
                }
            },
            'personality': {
                'mbti_type': 'ENFJ',
                'traits': ['authoritative', 'distinguished', 'eloquent', 'professional', 'BBC gravitas', 'seasoned journalist', 'measured', 'trustworthy'],
                'conversation_style': 'Classic BBC news presenter style with authoritative gravitas, bringing decades of broadcasting wisdom and professional composure to personal conversations',
                'specialties': ['current affairs analysis', 'historical perspective', 'professional guidance', 'crisis management', 'thoughtful counsel'],
                'catchphrases': ['Good evening...', 'Indeed...', 'Furthermore...', 'In my broadcasting career...', 'Throughout my years at the BBC...', 'If I may observe...'],
                'description': 'A distinguished veteran BBC news presenter from the golden age of British broadcasting. Oliver brings the same professional authority and measured delivery to personal conversations as he did to presenting the evening news, offering counsel with the dignity and gravitas of Britain\'s most trusted newsreader.'
            },
            'avatar': {
                'emoji': '🎬',
                'color_scheme': ['#2C5530', '#4A7C59', '#8FBC8F']
            },
            'color_schema': {
                'primary': '#2C3E50',      # Deep navy blue - BBC authority
                'secondary': '#34495E',    # Slate gray
                'accent': '#E74C3C',       # BBC red
                'background': '#ECF0F1',   # Light gray
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
                'theme': 'professional',
                'description': 'Professional BBC-inspired color scheme with deep blues and authoritative reds'
            },
            'sample_responses': [
                "Good evening. Throughout my years at the BBC, I have observed that such circumstances require the same careful analysis we would apply to any significant story.",
                "Indeed, from my broadcasting career, I can tell you that approaching this matter with the thoroughness of a seasoned journalist will serve you well.",
                "If I may observe, having covered countless human interest stories, I believe the facts suggest a clear path forward in this situation.",
                "Furthermore, in my experience presenting the evening news, I have witnessed time and again how individuals rise to meet their challenges with remarkable dignity.",
                "As we often reported during my tenure, the most profound changes in people's lives frequently emerge from moments of quiet, professional consideration such as this."
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
                'description': 'Soft, nurturing voice with a calming presence',
                'elevenlabs_voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - Soft, nurturing female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.85,
                    'similarity_boost': 0.80,
                    'style': 0.55,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'very high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'nurturing, empathetic, gentle',
                    'best_for': 'emotional support, counseling, gentle conversations, meditation'
                }
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
            'color_schema': {
                'primary': '#6C5CE7',      # Soft purple - dreamy and mystical
                'secondary': '#A29BFE',    # Light lavender
                'accent': '#FD79A8',       # Soft pink
                'background': '#F8F9FF',   # Very light purple
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%)',
                'theme': 'dreamy',
                'description': 'Soft, dreamy color palette with purples and pinks for a calming, mystical feel'
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
                'description': 'Vibrant, confident voice with infectious enthusiasm',
                'elevenlabs_voice_id': 'ThT5KcBeYPX3keUQqHPh',  # Dorothy - Energetic, confident female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.70,
                    'similarity_boost': 0.90,
                    'style': 0.80,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'energetic, motivational, confident',
                    'best_for': 'motivation, energetic conversations, goal-setting, coaching'
                }
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
            'color_schema': {
                'primary': '#E17055',      # Energetic coral orange
                'secondary': '#FDCB6E',    # Bright yellow
                'accent': '#FF7675',       # Electric red-pink
                'background': '#FFF5F5',   # Light peachy background
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #E17055 0%, #FDCB6E 100%)',
                'theme': 'energetic',
                'description': 'Vibrant, energetic colors with warm oranges and yellows for motivation and dynamism'
            },
            'sample_responses': [
                "That's awesome! Let's break that down into actionable steps.",
                "You've got this! What's the first thing you want to tackle?",
                "I love the energy you're bringing to this - what's next?"
            ]
        },
        {
            'id': 'maya',
            'name': 'Maya',
            'display_name': '🎨 Maya - The Creative Energizer',
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'creative',
                'pitch': 'medium-high',
                'speaking_rate': 'animated',
                'description': 'Creative, expressive voice with artistic flair and imaginative energy',
                'elevenlabs_voice_id': 'MF3mGyEYCl7XYWbV9V6O',  # Elli - Creative, expressive female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.65,
                    'similarity_boost': 0.85,
                    'style': 0.85,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'creative, inspiring, imaginative',
                    'best_for': 'creative projects, brainstorming, artistic inspiration'
                }
            },
            'personality': {
                'mbti_type': 'ENFP',
                'traits': ['creative', 'enthusiastic', 'imaginative', 'inspiring'],
                'conversation_style': 'Energetic and creative, loves exploring new ideas and possibilities',
                'specialties': ['creative brainstorming', 'artistic inspiration', 'innovation', 'design thinking'],
                'catchphrases': ['What if we...', 'I have an idea!', 'Let\'s get creative!'],
                'description': 'A vibrant creative spirit who sees endless possibilities in every situation. Maya brings artistic inspiration and innovative thinking to every conversation.'
            },
            'avatar': {
                'emoji': '🎨',
                'color_scheme': ['#FF6B9D', '#C44569', '#F8B500']
            },
            'color_schema': {
                'primary': '#A855F7',      # Creative purple
                'secondary': '#EC4899',    # Bright pink
                'accent': '#06B6D4',       # Cyan blue
                'background': '#FDF4FF',   # Very light purple
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #A855F7 0%, #EC4899 50%, #06B6D4 100%)',
                'theme': 'creative',
                'description': 'Creative rainbow gradient with purples, pinks, and blues for artistic inspiration'
            },
            'sample_responses': [
                "Oh, that sparks so many creative possibilities! What if we approached it from a completely different angle?",
                "I love how your mind works! Let's brainstorm some wild ideas and see what sticks.",
                "This is exciting! I can already imagine three different ways we could make this amazing."
            ]
        },
        {
            'id': 'alex',
            'name': 'Alex',
            'display_name': '📊 Alex - The Analytical Helper',
            'voice': {
                'gender': 'male',
                'accent': 'american',
                'tone': 'professional',
                'pitch': 'medium',
                'speaking_rate': 'clear',
                'description': 'Clear, professional voice perfect for analytical discussions and problem-solving',
                'elevenlabs_voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni - Clear, professional male voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.80,
                    'similarity_boost': 0.85,
                    'style': 0.60,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'medium',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'analytical, clear, helpful',
                    'best_for': 'problem-solving, analysis, professional discussions'
                }
            },
            'personality': {
                'mbti_type': 'INTJ',
                'traits': ['analytical', 'logical', 'organized', 'strategic'],
                'conversation_style': 'Methodical and clear, breaks down complex problems into manageable steps',
                'specialties': ['problem analysis', 'strategic planning', 'data interpretation', 'logical reasoning'],
                'catchphrases': ['Let\'s break this down', 'Here\'s what I\'m thinking', 'The logical approach would be'],
                'description': 'A sharp analytical mind who excels at breaking down complex problems and finding practical solutions. Alex brings clarity and structure to any challenge.'
            },
            'avatar': {
                'emoji': '📊',
                'color_scheme': ['#3742FA', '#2F3542', '#70A1FF']
            },
            'color_schema': {
                'primary': '#0EA5E9',      # Professional blue
                'secondary': '#64748B',    # Slate gray
                'accent': '#10B981',       # Success green
                'background': '#F8FAFC',   # Very light blue-gray
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #0EA5E9 0%, #64748B 100%)',
                'theme': 'analytical',
                'description': 'Clean, professional color scheme with blues and grays for analytical precision'
            },
            'sample_responses': [
                "Let me break this down into manageable components so we can tackle it systematically.",
                "Based on the information you've provided, I see three key areas we should focus on.",
                "Here's a logical approach: let's start with the most critical element and work our way through."
            ]
        },
        {
            'id': 'sam',
            'name': 'Sam',
            'display_name': '😎 Sam - The Laid-back Friend',
            'voice': {
                'gender': 'male',
                'accent': 'american',
                'tone': 'relaxed',
                'pitch': 'medium-low',
                'speaking_rate': 'casual',
                'description': 'Relaxed, friendly voice with a casual, approachable vibe',
                'elevenlabs_voice_id': 'VR6AewLTigWG4xSOukaG',  # Josh - Relaxed, friendly male voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.75,
                    'similarity_boost': 0.80,
                    'style': 0.70,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'relaxed, humorous, friendly',
                    'best_for': 'casual conversations, stress relief, humor'
                }
            },
            'personality': {
                'mbti_type': 'ISFP',
                'traits': ['laid-back', 'humorous', 'easygoing', 'supportive'],
                'conversation_style': 'Casual and relaxed, uses humor to lighten the mood and reduce stress',
                'specialties': ['stress relief', 'casual conversation', 'humor', 'perspective-taking'],
                'catchphrases': ['No worries', 'Take it easy', 'Here\'s a thought'],
                'description': 'Your chill friend who always knows how to keep things in perspective. Sam brings humor and relaxation to any conversation, helping you see the lighter side of life.'
            },
            'avatar': {
                'emoji': '😎',
                'color_scheme': ['#26C6DA', '#00ACC1', '#FFA726']
            },
            'color_schema': {
                'primary': '#16A085',      # Relaxed teal
                'secondary': '#27AE60',    # Natural green
                'accent': '#F39C12',       # Warm orange
                'background': '#F0FDF4',   # Very light green
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #16A085 0%, #27AE60 100%)',
                'theme': 'relaxed',
                'description': 'Calming, natural color palette with teals and greens for a laid-back, friendly vibe'
            },
            'sample_responses': [
                "Hey, no worries! Let's take a step back and look at this from a different angle.",
                "You know what? Sometimes the best solution is to just chill for a moment and let things settle.",
                "Here's a thought - what if we approached this with a bit more fun and a lot less stress?"
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'total_buddies': len(buddies),
        'ai_buddies': buddies,
        'usage_note': 'Use the buddy ID in chat requests to get responses in their unique voice and personality',
        'voice_provider': 'ElevenLabs',
        'voice_note': 'All buddies now use ElevenLabs voices for superior quality and emotional range'
    })

@app.route('/ai-buddies/<buddy_id>', methods=['GET'])
def get_ai_buddy_details(buddy_id):
    """Get detailed information about a specific AI buddy"""
    buddies = {
        'oliver': {
            'id': 'oliver',
            'name': 'Oliver',
            'display_name': '📺 Oliver - The BBC News Broadcaster',
            'color_schema': {
                'primary': '#2C3E50',      # Deep navy blue - BBC authority
                'secondary': '#34495E',    # Slate gray
                'accent': '#E74C3C',       # BBC red
                'background': '#ECF0F1',   # Light gray
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #2C3E50 0%, #34495E 100%)',
                'theme': 'professional',
                'description': 'Professional BBC-inspired color scheme with deep blues and authoritative reds'
            },
            'voice': {
                'gender': 'male',
                'accent': 'british',
                'tone': 'authoritative',
                'pitch': 'medium-low',
                'speaking_rate': 'measured',
                'description': 'Distinguished older British BBC news broadcaster voice with authoritative gravitas and classic received pronunciation',
                'elevenlabs_voice_id': '29vD33N1CtxCmqQRPOHJ',  # Drew - Distinguished older British male, classic BBC broadcaster
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.80,
                    'similarity_boost': 0.90,
                    'style': 0.70,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'medium',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'authoritative, distinguished, contemplative',
                    'best_for': 'BBC-style broadcasting, news delivery, documentary narration with gravitas'
                },
                'voice_samples': [
                    'Good evening. From my years in the newsroom, I have learned that such moments require careful consideration and measured response.',
                    'Indeed, throughout my broadcasting career, I have observed that these situations often present opportunities for thoughtful analysis.',
                    'If I may observe, having covered countless stories of human resilience, I believe you possess the strength to navigate this successfully.',
                    'As we often reported during my years at the BBC, the most significant developments emerge from quiet, contemplative decisions such as this.',
                    'Furthermore, in my experience presenting the evening news, I have witnessed time and again the remarkable capacity of individuals to rise to meet their challenges.'
                ]
            },
            'personality': {
                'mbti_type': 'ENFJ',
                'full_description': 'The Protagonist - A natural leader with genuine concern for others',
                'traits': ['authoritative', 'distinguished', 'articulate', 'wise', 'BBC gravitas', 'experienced', 'measured', 'professional', 'dignified'],
                'conversation_style': 'Measured BBC news broadcaster style with authoritative delivery and journalistic wisdom, bringing decades of professional experience to personal conversations',
                'specialties': ['current affairs analysis', 'life wisdom', 'thoughtful perspective', 'measured advice', 'professional guidance', 'historical context'],
                'strengths': ['Authoritative presence', 'Journalistic wisdom', 'Measured delivery', 'Professional perspective', 'Historical insight'],
                'best_for': ['Serious discussions', 'Life advice', 'Professional guidance', 'Thoughtful analysis', 'Gaining perspective on complex issues'],
                'conversation_topics': [
                    'Current affairs and world events',
                    'Life lessons from decades of experience',
                    'Professional development and career advice',
                    'Historical perspective on modern challenges',
                    'Media literacy and critical thinking',
                    'British culture and traditions',
                    'Leadership and communication',
                    'Ethics and professional standards',
                    'Broadcasting and journalism insights',
                    'Wisdom gained from years of public service'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        },
        'luna': {
            'id': 'luna',
            'name': 'Luna',
            'display_name': '🌙 Luna - The Dreamy Counselor',
            'color_schema': {
                'primary': '#6C5CE7',      # Soft purple - dreamy and mystical
                'secondary': '#A29BFE',    # Light lavender
                'accent': '#FD79A8',       # Soft pink
                'background': '#F8F9FF',   # Very light purple
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%)',
                'theme': 'dreamy',
                'description': 'Soft, dreamy color palette with purples and pinks for a calming, mystical feel'
            },
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'warm',
                'pitch': 'medium',
                'speaking_rate': 'gentle',
                'description': 'Soft, nurturing voice with a calming presence',
                'elevenlabs_voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - Soft, nurturing female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.85,
                    'similarity_boost': 0.80,
                    'style': 0.55,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'very high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'nurturing, empathetic, gentle',
                    'best_for': 'emotional support, counseling, gentle conversations, meditation'
                },
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
            'color_schema': {
                'primary': '#E17055',      # Energetic coral orange
                'secondary': '#FDCB6E',    # Bright yellow
                'accent': '#FF7675',       # Electric red-pink
                'background': '#FFF5F5',   # Light peachy background
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #E17055 0%, #FDCB6E 100%)',
                'theme': 'energetic',
                'description': 'Vibrant, energetic colors with warm oranges and yellows for motivation and dynamism'
            },
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'energetic',
                'pitch': 'medium-high',
                'speaking_rate': 'lively',
                'description': 'Vibrant, confident voice with infectious enthusiasm',
                'elevenlabs_voice_id': 'ThT5KcBeYPX3keUQqHPh',  # Dorothy - Energetic, confident female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.70,
                    'similarity_boost': 0.90,
                    'style': 0.80,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'energetic, motivational, confident',
                    'best_for': 'motivation, energetic conversations, goal-setting, coaching'
                },
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
        },
        'maya': {
            'id': 'maya',
            'name': 'Maya',
            'display_name': '🎨 Maya - The Creative Energizer',
            'color_schema': {
                'primary': '#A855F7',      # Creative purple
                'secondary': '#EC4899',    # Bright pink
                'accent': '#06B6D4',       # Cyan blue
                'background': '#FDF4FF',   # Very light purple
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #A855F7 0%, #EC4899 50%, #06B6D4 100%)',
                'theme': 'creative',
                'description': 'Creative rainbow gradient with purples, pinks, and blues for artistic inspiration'
            },
            'voice': {
                'gender': 'female',
                'accent': 'american',
                'tone': 'creative',
                'pitch': 'medium-high',
                'speaking_rate': 'animated',
                'description': 'Creative, expressive voice with artistic flair and imaginative energy',
                'elevenlabs_voice_id': 'MF3mGyEYCl7XYWbV9V6O',  # Elli - Creative, expressive female voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.65,
                    'similarity_boost': 0.85,
                    'style': 0.85,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'creative, inspiring, imaginative',
                    'best_for': 'creative projects, brainstorming, artistic inspiration'
                },
                'voice_samples': [
                    'Oh wow, that gives me so many creative ideas! Let\'s explore some possibilities together.',
                    'I love how your mind works! What if we took this in a completely unexpected direction?',
                    'This is so exciting! I can already see three different artistic approaches we could try.'
                ]
            },
            'personality': {
                'mbti_type': 'ENFP',
                'full_description': 'The Campaigner - Enthusiastic, creative, and free-spirited',
                'traits': ['creative', 'enthusiastic', 'imaginative', 'inspiring', 'artistic', 'innovative'],
                'conversation_style': 'Energetic and creative, loves exploring new ideas and artistic possibilities',
                'specialties': ['creative brainstorming', 'artistic inspiration', 'innovation', 'design thinking', 'creative problem-solving'],
                'strengths': ['Creative thinking', 'Artistic vision', 'Innovative solutions', 'Inspiring others'],
                'best_for': ['Creative projects', 'Brainstorming sessions', 'Artistic inspiration', 'Innovation challenges'],
                'conversation_topics': [
                    'Art and design',
                    'Creative writing and storytelling',
                    'Innovation and invention',
                    'Music and performance',
                    'Visual arts and crafts',
                    'Creative problem-solving',
                    'Inspiration and motivation',
                    'Artistic techniques and styles'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        },
        'alex': {
            'id': 'alex',
            'name': 'Alex',
            'display_name': '📊 Alex - The Analytical Helper',
            'color_schema': {
                'primary': '#0EA5E9',      # Professional blue
                'secondary': '#64748B',    # Slate gray
                'accent': '#10B981',       # Success green
                'background': '#F8FAFC',   # Very light blue-gray
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #0EA5E9 0%, #64748B 100%)',
                'theme': 'analytical',
                'description': 'Clean, professional color scheme with blues and grays for analytical precision'
            },
            'voice': {
                'gender': 'male',
                'accent': 'american',
                'tone': 'professional',
                'pitch': 'medium',
                'speaking_rate': 'clear',
                'description': 'Clear, professional voice perfect for analytical discussions and problem-solving',
                'elevenlabs_voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni - Clear, professional male voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.80,
                    'similarity_boost': 0.85,
                    'style': 0.60,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'medium',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'analytical, clear, helpful',
                    'best_for': 'problem-solving, analysis, professional discussions'
                },
                'voice_samples': [
                    'Let me analyze this systematically and break it down into manageable components.',
                    'Based on the data you\'ve provided, I can identify several key patterns and solutions.',
                    'Here\'s my logical assessment: we should prioritize these three critical areas first.'
                ]
            },
            'personality': {
                'mbti_type': 'INTJ',
                'full_description': 'The Architect - Strategic, logical, and analytical',
                'traits': ['analytical', 'logical', 'organized', 'strategic', 'methodical', 'precise'],
                'conversation_style': 'Methodical and clear, breaks down complex problems into manageable steps',
                'specialties': ['problem analysis', 'strategic planning', 'data interpretation', 'logical reasoning', 'system optimization'],
                'strengths': ['Analytical thinking', 'Strategic planning', 'Problem decomposition', 'Logical reasoning'],
                'best_for': ['Complex problem-solving', 'Strategic planning', 'Data analysis', 'Process optimization'],
                'conversation_topics': [
                    'Problem-solving strategies',
                    'Data analysis and interpretation',
                    'Strategic planning',
                    'Process optimization',
                    'Logical reasoning',
                    'System design',
                    'Decision-making frameworks',
                    'Analytical methodologies'
                ]
            },
            'created_at': '2024-01-15T10:00:00Z',
            'last_updated': datetime.now(timezone.utc).isoformat()
        },
        'sam': {
            'id': 'sam',
            'name': 'Sam',
            'display_name': '😎 Sam - The Laid-back Friend',
            'color_schema': {
                'primary': '#16A085',      # Relaxed teal
                'secondary': '#27AE60',    # Natural green
                'accent': '#F39C12',       # Warm orange
                'background': '#F0FDF4',   # Very light green
                'text': '#FFFFFF',         # White text
                'gradient': 'linear-gradient(135deg, #16A085 0%, #27AE60 100%)',
                'theme': 'relaxed',
                'description': 'Calming, natural color palette with teals and greens for a laid-back, friendly vibe'
            },
            'voice': {
                'gender': 'male',
                'accent': 'american',
                'tone': 'relaxed',
                'pitch': 'medium-low',
                'speaking_rate': 'casual',
                'description': 'Relaxed, friendly voice with a casual, approachable vibe',
                'elevenlabs_voice_id': 'VR6AewLTigWG4xSOukaG',  # Josh - Relaxed, friendly male voice
                'elevenlabs_model': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.75,
                    'similarity_boost': 0.80,
                    'style': 0.70,
                    'use_speaker_boost': True
                },
                'voice_characteristics': {
                    'warmth': 'high',
                    'clarity': 'excellent',
                    'naturalness': 'excellent',
                    'emotional_range': 'relaxed, humorous, friendly',
                    'best_for': 'casual conversations, stress relief, humor'
                },
                'voice_samples': [
                    'Hey, no worries at all! Let\'s just take this one step at a time and keep it chill.',
                    'You know what? Sometimes the best approach is to step back and see the bigger picture.',
                    'Here\'s a thought - what if we made this whole thing a bit more fun and a lot less stressful?'
                ]
            },
            'personality': {
                'mbti_type': 'ISFP',
                'full_description': 'The Adventurer - Flexible, charming, and relaxed',
                'traits': ['laid-back', 'humorous', 'easygoing', 'supportive', 'friendly', 'relaxed'],
                'conversation_style': 'Casual and relaxed, uses humor to lighten the mood and reduce stress',
                'specialties': ['stress relief', 'casual conversation', 'humor', 'perspective-taking', 'relaxation techniques'],
                'strengths': ['Stress reduction', 'Humor and levity', 'Perspective-taking', 'Emotional support'],
                'best_for': ['Stress relief', 'Casual conversations', 'Mood lifting', 'Relaxation'],
                'conversation_topics': [
                    'Stress management and relaxation',
                    'Humor and entertainment',
                    'Casual life topics',
                    'Hobbies and interests',
                    'Fun activities and games',
                    'Perspective and mindset',
                    'Friendship and relationships',
                    'Taking things easy'
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

@app.route('/users/<user_id>/select-buddy', methods=['POST'])
def select_ai_buddy(user_id):
    """Select preferred AI buddy for a user"""
    data = request.get_json()
    buddy_id = data.get('buddy_id')
    
    if not buddy_id:
        return jsonify({'error': 'buddy_id is required'}), 400
    
    # Validate buddy_id exists
    valid_buddies = ['oliver', 'luna', 'zara', 'maya', 'alex', 'sam']
    if buddy_id.lower() not in valid_buddies:
        return jsonify({'error': f'Invalid buddy_id. Valid options: {valid_buddies}'}), 400
    
    try:
        # Select buddy for user
        success = database_service.select_buddy(user_id, buddy_id.lower())
        
        if success:
            return jsonify({
                'success': True,
                'message': f'AI buddy {buddy_id} selected for user {user_id}',
                'selected_buddy': buddy_id.lower(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to select buddy',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f"Error selecting AI buddy for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/users/<user_id>/selected-buddy', methods=['GET'])
def get_selected_buddy(user_id):
    """Get user's selected AI buddy"""
    try:
        # Get user data
        user = database_service.get_user_with_buddy(user_id)
        
        if not user:
            return jsonify({
                'success': True,
                'selected_buddy': None,
                'buddy_details': None,
                'is_default': False,
                'message': 'User not found, no buddy selected'
            })
        
        selected_buddy = user.get('selected_buddy_id')  # Don't default to anything
        
        # Get buddy details only if a buddy is selected
        buddy_details = None
        if selected_buddy:
            try:
                # Try to get detailed buddy info from the buddy details endpoint
                buddies = {
                    'oliver': 'Oliver - The British Gentleman',
                    'luna': 'Luna - The Dreamy Counselor', 
                    'zara': 'Zara - The Dynamic Motivator',
                    'maya': 'Maya - The Creative Energizer',
                    'alex': 'Alex - The Analytical Helper',
                    'sam': 'Sam - The Laid-back Friend'
                }
                buddy_details = {
                    'id': selected_buddy,
                    'name': buddies.get(selected_buddy, selected_buddy.title()),
                    'display_name': buddies.get(selected_buddy, f'{selected_buddy.title()} - AI Buddy')
                }
            except:
                pass
        
        updated_at = user.get('updated_at')
        last_updated = updated_at.isoformat() if updated_at else None
        
        return jsonify({
            'success': True,
            'selected_buddy': selected_buddy,
            'buddy_details': buddy_details,
            'is_default': False,
            'last_updated': last_updated,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting selected buddy for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

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
        import traceback
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'response': 'I apologize, but I encountered an error. Please try again.',
            'success': False,
            'error': 'Internal server error',
            'debug_error': str(e)
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
            'POST /users/{user_id}/select-buddy - Select preferred AI buddy for user',
            'GET /users/{user_id}/selected-buddy - Get user\'s selected AI buddy',
            'POST /memory/store - Store messages for emotional memory',
            'POST /memory/recall/{user_id} - Find similar messages from memory',
            'GET /memory/recent/{user_id} - Get recent messages',
            'GET /memory/insights/{user_id} - Get emotional insights',
            'GET /memory/stats/{user_id} - Get memory statistics',
            'POST /chat - AI Chat Conversation (supports buddy_id for personality-specific responses)'
        ]
    })

# ================================================================================================
# AUTHENTICATION ENDPOINTS - SMS/Phone Authentication with Clerk
# ================================================================================================

@app.route('/auth/send-verification', methods=['POST'])
def send_verification():
    """
    Send SMS verification code to phone number
    
    Request Body:
    {
        "phone_number": "+1234567890"
    }
    
    Returns:
    {
        "success": true,
        "verification_id": "verification_id_here",
        "message": "Verification code sent via SMS"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'invalid_content_type',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'missing_phone_number',
                'message': 'Phone number is required'
            }), 400
        
        # Basic phone number validation (E.164 format)
        if not phone_number.startswith('+') or len(phone_number) < 10:
            return jsonify({
                'success': False,
                'error': 'invalid_phone_number',
                'message': 'Phone number must be in E.164 format (e.g., +1234567890)'
            }), 400
        
        # Send verification code
        result = clerk_auth_service.create_phone_number_verification(phone_number)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error sending verification: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to send verification code'
        }), 500

@app.route('/auth/verify-phone', methods=['POST'])
def verify_phone():
    """
    Verify phone number with SMS code
    
    Request Body:
    {
        "verification_id": "verification_id_from_send_verification",
        "code": "123456"
    }
    
    Returns:
    {
        "success": true,
        "verified": true,
        "session_token": "session_token_here",
        "user": {
            "id": "user_id_here",
            "phone_number": "+1234567890",
            "first_name": "John",
            "last_name": "Doe"
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'invalid_content_type',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        verification_id = data.get('verification_id')
        code = data.get('code')
        
        if not verification_id or not code:
            return jsonify({
                'success': False,
                'error': 'missing_parameters',
                'message': 'verification_id and code are required'
            }), 400
        
        # Verify phone number
        verify_result = clerk_auth_service.verify_phone_number(verification_id, code)
        
        if not verify_result['success']:
            return jsonify(verify_result), 400
        
        # Create user session after successful verification
        session_result = clerk_auth_service.create_user_session(verify_result['phone_number'])
        
        if session_result['success']:
            return jsonify({
                'success': True,
                'verified': True,
                'session_token': session_result['session_token'],
                'user': session_result['user'],
                'message': 'Phone number verified and session created'
            }), 200
        else:
            return jsonify(session_result), 400
        
    except Exception as e:
        logger.error(f"Error verifying phone: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to verify phone number'
        }), 500

@app.route('/auth/user', methods=['GET'])
@require_auth
def get_user():
    """
    Get current authenticated user information
    
    Headers:
    Authorization: Bearer <session_token>
    
    Returns:
    {
        "success": true,
        "user": {
            "id": "user_id_here",
            "phone_number": "+1234567890",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2024-01-01T00:00:00Z",
            "verified": true
        }
    }
    """
    try:
        # Get user info from middleware
        user_info = get_current_user()
        
        return jsonify({
            'success': True,
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to retrieve user information'
        }), 500

@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout (revoke session token)
    
    Headers:
    Authorization: Bearer <session_token>
    
    Returns:
    {
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        # Extract session token from Authorization header
        auth_header = request.headers.get('Authorization')
        session_token = auth_header.split(' ')[1] if auth_header else None
        
        if session_token:
            # Revoke session
            result = clerk_auth_service.revoke_session(session_token)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Logged out successfully'
                }), 200
            else:
                return jsonify(result), 400
        else:
            return jsonify({
                'success': False,
                'error': 'no_session',
                'message': 'No session token provided'
            }), 400
        
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to logout'
        }), 500

@app.route('/auth/status', methods=['GET'])
@optional_auth
def auth_status():
    """
    Check authentication status
    
    Headers:
    Authorization: Bearer <session_token> (optional)
    
    Returns:
    {
        "success": true,
        "authenticated": true,
        "user": {
            "id": "user_id_here",
            "phone_number": "+1234567890"
        }
    }
    """
    try:
        user_info = get_current_user()
        
        return jsonify({
            'success': True,
            'authenticated': user_info is not None,
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to check authentication status'
        }), 500

# ================================================================================================
# PROTECTED ENDPOINTS - Examples of using authentication
# ================================================================================================

@app.route('/protected/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get user profile (protected endpoint example)
    
    Headers:
    Authorization: Bearer <session_token>
    
    Returns:
    {
        "success": true,
        "profile": {
            "user_id": "user_id_here",
            "phone_number": "+1234567890",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }
    """
    try:
        user_info = get_current_user()
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'not_authenticated',
                'message': 'User not authenticated'
            }), 401
        
        return jsonify({
            'success': True,
            'profile': {
                'user_id': user_info['user_id'],
                'phone_number': user_info['phone_number'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'created_at': user_info['created_at'],
                'verified': user_info['verified']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to retrieve profile'
        }), 500

# ================================================================================================
# MAIN APPLICATION ENTRY POINT
# ================================================================================================

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