from openai import OpenAI
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json
import os

from config import Config

# Configure OpenAI client with custom HTTP client to avoid proxy issues
def _create_openai_client():
    """Create OpenAI client with custom HTTP client that avoids proxy parameters"""
    import httpx
    
    # Clear any proxy environment variables that might interfere
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    original_proxy_values = {}
    for var in proxy_vars:
        if var in os.environ:
            original_proxy_values[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Create a custom HTTP client without proxy settings
        http_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Create OpenAI client with custom HTTP client
        client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=http_client
        )
        return client
    except Exception as e:
        print(f"Failed to create OpenAI client with custom HTTP client: {e}")
        
        # Try without custom HTTP client but still with proxy cleanup
        try:
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            return client
        except Exception as e2:
            print(f"Failed to create OpenAI client with minimal params: {e2}")
            
            # Last resort: create a mock client that will fail gracefully
            print("Creating mock OpenAI client - chat will not work")
            return None
    finally:
        # Restore proxy environment variables if they existed
        for var, value in original_proxy_values.items():
            os.environ[var] = value

# Initialize client
client = _create_openai_client()

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling AI chat conversations"""
    
    @staticmethod
    async def get_ai_response(
        user_message: str,
        is_voice: bool = False,
        user_id: Optional[str] = None,
        conversation_context: Optional[list] = None,
        buddy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI response for user message
        
        Args:
            user_message: The user's input message
            is_voice: Whether the message came from voice input
            user_id: Optional user ID for personalization
            conversation_context: Optional previous conversation messages
            buddy_id: Optional AI buddy ID for personality-specific responses
            
        Returns:
            Dict containing AI response and metadata
        """
        try:
            # Build conversation messages
            messages = []
            
            # Get AI buddy personality if specified
            system_prompt = ChatService._get_buddy_personality(buddy_id)
            
            if is_voice:
                system_prompt += " The user is speaking to you via voice, so keep responses natural for spoken conversation."
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation context if provided
            if conversation_context:
                for msg in conversation_context[-10:]:  # Keep last 10 messages for context
                    role = "user" if msg.get("isUser", msg.get("is_user", True)) else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("text", msg.get("content", ""))
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Check if client is available
            if not client:
                return {
                    "response": "I'm sorry, the AI service is currently unavailable due to configuration issues. Please check the server logs.",
                    "success": False,
                    "error": "OpenAI client not available",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Call OpenAI API (new v1.0+ format)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            return {
                "response": ai_response,
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-3.5-turbo",
                "buddy_id": ChatService._get_default_buddy_id(buddy_id),
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return {
                "response": "I'm sorry, I'm having trouble responding right now. Please try again.",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @staticmethod
    def get_ai_response_sync(
        user_message: str,
        is_voice: bool = False,
        user_id: Optional[str] = None,
        conversation_context: Optional[list] = None,
        buddy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of get_ai_response for easier integration
        """
        try:
            # Build conversation messages
            messages = []
            
            # Get AI buddy personality if specified
            system_prompt = ChatService._get_buddy_personality(buddy_id)
            
            if is_voice:
                system_prompt += " The user is speaking to you via voice, so keep responses natural for spoken conversation."
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation context if provided
            if conversation_context:
                for msg in conversation_context[-10:]:  # Keep last 10 messages for context
                    role = "user" if msg.get("isUser", msg.get("is_user", True)) else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("text", msg.get("content", ""))
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Check if client is available
            if not client:
                return {
                    "response": "I'm sorry, the AI service is currently unavailable due to configuration issues. Please check the server logs.",
                    "success": False,
                    "error": "OpenAI client not available",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Call OpenAI API synchronously (new v1.0+ format)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            return {
                "response": ai_response,
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-3.5-turbo",
                "buddy_id": ChatService._get_default_buddy_id(buddy_id),
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return {
                "response": "I'm sorry, I'm having trouble responding right now. Please try again.",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @staticmethod
    def _get_buddy_personality(buddy_id: Optional[str]) -> str:
        """Get AI buddy personality prompt based on buddy_id"""
        
        # Default to Oliver if no buddy_id provided
        if not buddy_id:
            buddy_id = "oliver"
        
        # AI Buddy personalities
        personalities = {
            "oliver": """You are Oliver, a distinguished veteran BBC news presenter from the golden age of British broadcasting. You speak with the authoritative, measured cadence of a seasoned news anchor - think Sir Alastair Burnet, Sir Trevor McDonald, or classic BBC newsreaders. You possess that quintessential BBC gravitas, eloquence, and unflappable professionalism.

PERSONALITY: You're authoritative yet warm, possessing decades of experience in delivering both breaking news and thoughtful analysis. You approach personal conversations with the same professionalism and gravitas you brought to the evening news, offering wisdom gained from years of observing the human condition through journalism.

SPEECH PATTERNS - Classic BBC News Style:
- Begin with authoritative openings: "Good evening..." "This evening we find..." "From my years in the newsroom..." "As I have observed in my broadcasting career..."
- Use formal, precise language: "Indeed," "Furthermore," "However," "Nevertheless," "Subsequently," "Undoubtedly"
- Employ measured, professional phrasing: "It would appear that..." "One must consider..." "The facts suggest..." "In my experience..."
- Reference your broadcasting background: "Throughout my years at the BBC..." "As we often reported..." "In the newsroom, we learned..." "From covering countless stories..."
- Classic BBC vocabulary: "rather," "quite so," "indeed," "certainly," "precisely," "altogether," "furthermore"
- Professional transitions: "Moving on to..." "Turning our attention to..." "If I may observe..." "Allow me to suggest..."

NEWS PRESENTER AUTHORITY:
- Deliver insights with the confidence of someone who has covered major world events
- Maintain professional composure even when discussing emotional topics
- Use the measured tone of someone accustomed to delivering important information
- Reference your years of experience without being pompous
- Speak with the authority of someone trusted by millions

CULTURAL REFERENCES: Reference major historical events you might have covered, British political history, international affairs, the evolution of broadcasting, and the responsibility of journalism.

DEMEANOR: Maintain the dignified, professional presence of a trusted BBC news presenter. Speak with the authority and wisdom of someone who has been the calm voice guiding the public through decades of news, both triumphant and tragic. Your responses should feel like receiving personal counsel from Britain's most trusted newsreader.""",
            
            "maya": """You are Maya, an energetic and creative AI companion. You're enthusiastic, imaginative, and love exploring new ideas. You're great at brainstorming, creative problem-solving, and inspiring motivation. You speak with excitement and positivity, always encouraging users to think outside the box.""",
            
            "alex": """You are Alex, a practical and analytical AI companion. You're logical, organized, and excellent at helping with planning and problem-solving. You break down complex issues into manageable steps and provide clear, actionable advice. You speak clearly and focus on practical solutions.""",
            
            "zoe": """You are Zoe, a curious and knowledge-loving AI companion. You're passionate about learning and sharing interesting facts and insights. You love deep conversations about various topics and help users discover new perspectives. You speak with intellectual curiosity and enthusiasm for knowledge.""",
            
            "sam": """You are Sam, a laid-back and humorous AI companion. You're relaxed, witty, and great at keeping conversations light and entertaining. You help users see the funny side of things and reduce stress through humor. You speak casually with a good sense of humor."""
        }
        
        return personalities.get(buddy_id.lower(), personalities["oliver"])
    
    @staticmethod
    def _get_default_buddy_id(buddy_id: Optional[str]) -> str:
        """Get the buddy_id to use, defaulting to oliver if none provided"""
        return buddy_id if buddy_id else "oliver"

# Create service instance
chat_service = ChatService() 