"""
AI Buddy Memory Service

This module provides emotional memory and conversational recall functionality
using OpenAI embeddings stored in both Supabase and ChromaDB for efficient
similarity search and journaling insights.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import asyncio

import openai
import chromadb
from chromadb.config import Settings
from supabase import create_client, Client

from config import Config

logger = logging.getLogger(__name__)

class MemoryService:
    """
    AI Buddy Memory Service for emotional memory and conversational recall.
    
    Combines structured storage in Supabase with vector similarity search in ChromaDB
    to enable personalized AI responses and journaling insights.
    """
    
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = Config.OPENAI_API_KEY
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Initialize Supabase client
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError("Supabase URL and KEY must be configured")
        
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.Client(Settings(
            # Use persistent storage for ChromaDB
            persist_directory="./chroma_db",
            anonymized_telemetry=False
        ))
        
        # Get or create the chat memory collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="chat_memory",
            metadata={"description": "AI buddy emotional memory and conversation history"}
        )
        
        logger.info("Memory Service initialized successfully")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI's text-embedding-3-small model.
        
        Args:
            text: The text to embed
            
        Returns:
            1536-dimensional embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Verify embedding dimension
            if len(embedding) != 1536:
                raise ValueError(f"Expected 1536-dimensional embedding, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def _save_to_supabase(self, user_id: str, message: str, message_id: str) -> bool:
        """
        Save message to Supabase chat_logs table.
        
        Args:
            user_id: User identifier
            message: Message content
            message_id: Unique message identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chat_log = {
                'id': message_id,
                'user_id': user_id,
                'message': message,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table('chat_logs').insert(chat_log).execute()
            
            if response.data:
                logger.info(f"Message saved to Supabase for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save message to Supabase: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving to Supabase: {str(e)}")
            return False
    
    def _save_to_chroma(self, user_id: str, message: str, message_id: str, embedding: List[float]) -> bool:
        """
        Save message embedding to ChromaDB collection.
        
        Args:
            user_id: User identifier  
            message: Message content
            message_id: Unique message identifier
            embedding: Message embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.add(
                documents=[message],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": user_id,
                    "message_id": message_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }],
                ids=[message_id]
            )
            
            logger.info(f"Embedding saved to ChromaDB for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to ChromaDB: {str(e)}")
            return False
    
    def store_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Store a user message with embedding for future recall.
        
        This function:
        1. Generates an embedding for the message
        2. Saves message + metadata to Supabase
        3. Saves embedding + metadata to ChromaDB
        
        Args:
            user_id: User identifier
            message: Message content to store
            
        Returns:
            Dictionary with storage results and message ID
        """
        try:
            # Generate unique message ID
            message_id = str(uuid.uuid4())
            
            # Generate embedding
            logger.info(f"Generating embedding for user {user_id}")
            embedding = self._generate_embedding(message)
            
            # Save to both storage systems
            supabase_success = self._save_to_supabase(user_id, message, message_id)
            chroma_success = self._save_to_chroma(user_id, message, message_id, embedding)
            
            success = supabase_success and chroma_success
            
            result = {
                "success": success,
                "message_id": message_id,
                "user_id": user_id,
                "supabase_saved": supabase_success,
                "chroma_saved": chroma_success,
                "embedding_dimension": len(embedding),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if success:
                logger.info(f"Message stored successfully for user {user_id}")
            else:
                logger.warning(f"Partial storage failure for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing message for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def find_similar_messages(self, user_id: str, message: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Find semantically similar messages for a user.
        
        This function:
        1. Embeds the input message
        2. Searches ChromaDB for similar embeddings (filtered by user_id)
        3. Returns top-k most similar messages
        
        Args:
            user_id: User identifier to filter results
            message: Query message to find similarities for
            top_k: Number of similar messages to return (default: 5)
            
        Returns:
            Dictionary with similar messages and metadata
        """
        try:
            # Generate embedding for query message
            logger.info(f"Finding similar messages for user {user_id}")
            query_embedding = self._generate_embedding(message)
            
            # Search ChromaDB with user_id filter
            results = self.collection.query(
                query_embeddings=[query_embedding],
                where={"user_id": user_id},
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_messages = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    
                    similar_messages.append({
                        "message": doc,
                        "message_id": metadata.get("message_id"),
                        "created_at": metadata.get("created_at"),
                        "similarity_score": 1.0 - distance,  # Convert distance to similarity
                        "distance": distance
                    })
            
            result = {
                "success": True,
                "user_id": user_id,
                "query_message": message,
                "similar_messages": similar_messages,
                "total_found": len(similar_messages),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Found {len(similar_messages)} similar messages for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error finding similar messages for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "query_message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_recent_messages(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get recent messages for a user from Supabase.
        
        Args:
            user_id: User identifier
            limit: Number of recent messages to retrieve
            
        Returns:
            Dictionary with recent messages
        """
        try:
            response = self.supabase.table('chat_logs').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            messages = response.data if response.data else []
            
            result = {
                "success": True,
                "user_id": user_id,
                "messages": messages,
                "total_count": len(messages),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Retrieved {len(messages)} recent messages for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving recent messages for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            # Get count from Supabase
            supabase_response = self.supabase.table('chat_logs').select('id', count='exact').eq('user_id', user_id).execute()
            supabase_count = supabase_response.count if hasattr(supabase_response, 'count') else 0
            
            # Get count from ChromaDB
            chroma_results = self.collection.query(
                query_embeddings=[[0.0] * 1536],  # Dummy embedding
                where={"user_id": user_id},
                n_results=1,
                include=["metadatas"]
            )
            
            # For more accurate count, we could implement a custom count method
            # For now, we'll estimate based on query results
            chroma_count = len(chroma_results.get('metadatas', [[]])[0]) if chroma_results.get('metadatas') else 0
            
            result = {
                "success": True,
                "user_id": user_id,
                "supabase_message_count": supabase_count,
                "chroma_embedding_count": chroma_count,
                "storage_sync": supabase_count == chroma_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Memory stats retrieved for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving memory stats for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_emotional_insights(self, user_id: str, emotion_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Get emotional insights by finding messages related to specific emotions.
        
        Args:
            user_id: User identifier
            emotion_keywords: List of emotion-related keywords to search for
            
        Returns:
            Dictionary with emotional insights
        """
        if emotion_keywords is None:
            emotion_keywords = [
                "happy", "sad", "angry", "excited", "worried", "anxious", 
                "grateful", "frustrated", "peaceful", "stressed", "joyful", "lonely"
            ]
        
        try:
            emotional_messages = []
            
            for emotion in emotion_keywords:
                # Find messages similar to emotion keywords
                emotion_results = self.find_similar_messages(
                    user_id=user_id,
                    message=f"I feel {emotion}",
                    top_k=3
                )
                
                if emotion_results.get("success") and emotion_results.get("similar_messages"):
                    for msg in emotion_results["similar_messages"]:
                        msg["detected_emotion"] = emotion
                        emotional_messages.append(msg)
            
            # Sort by similarity score
            emotional_messages.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            # Remove duplicates (keep highest scoring)
            seen_ids = set()
            unique_messages = []
            for msg in emotional_messages:
                msg_id = msg.get("message_id")
                if msg_id and msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    unique_messages.append(msg)
            
            result = {
                "success": True,
                "user_id": user_id,
                "emotional_messages": unique_messages[:10],  # Top 10 emotional messages
                "emotions_searched": emotion_keywords,
                "total_found": len(unique_messages),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Found {len(unique_messages)} emotional insights for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving emotional insights for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

# Global instance
memory_service = MemoryService() 