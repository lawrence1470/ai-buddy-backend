from openai import OpenAI
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

from config import Config

# Configure OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling AI chat conversations"""
    
    @staticmethod
    async def get_ai_response(
        user_message: str,
        is_voice: bool = False,
        user_id: Optional[str] = None,
        conversation_context: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Get AI response for user message
        
        Args:
            user_message: The user's input message
            is_voice: Whether the message came from voice input
            user_id: Optional user ID for personalization
            conversation_context: Optional previous conversation messages
            
        Returns:
            Dict containing AI response and metadata
        """
        try:
            # Build conversation messages
            messages = []
            
            # System prompt - customize based on your needs
            system_prompt = """You are a helpful, friendly AI assistant. You engage in natural conversation and provide thoughtful, concise responses. Keep responses conversational and warm."""
            
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
        conversation_context: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of get_ai_response for easier integration
        """
        try:
            # Build conversation messages
            messages = []
            
            # System prompt
            system_prompt = """You are a helpful, friendly AI assistant. You engage in natural conversation and provide thoughtful, concise responses. Keep responses conversational and warm."""
            
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

# Create service instance
chat_service = ChatService() 