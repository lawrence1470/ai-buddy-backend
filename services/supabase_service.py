from supabase import create_client, Client
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timezone
import uuid

from config import Config

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError("Supabase URL and KEY must be configured")
        
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # User Management
    def get_or_create_user(self, user_id: str, device_id: str = None) -> Dict:
        """Get existing user or create new one"""
        try:
            # First try to get existing user
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            
            if response.data:
                user = response.data[0]
                # Update last_active
                self.client.table('users').update({
                    'last_active': datetime.now(timezone.utc).isoformat()
                }).eq('id', user_id).execute()
                return user
            else:
                # Create new user  
                new_user = {
                    'id': user_id,
                    'device_id': device_id,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'last_active': datetime.now(timezone.utc).isoformat()
                }
                response = self.client.table('users').insert(new_user).execute()
                return response.data[0]
                
        except Exception as e:
            logger.error(f"Error getting/creating user {user_id}: {str(e)}")
            return {}
    
    # Session Management
    def save_session_with_summary(self, session_data: Dict) -> bool:
        """Save session data including AI-generated summaries"""
        try:
            # Ensure user exists
            self.get_or_create_user(session_data['user_id'])
            
            # Prepare session data
            session_record = {
                'id': session_data['session_id'],
                'user_id': session_data['user_id'],
                'transcript': session_data.get('transcript', []),
                'topic_summary': session_data.get('session_summary'),
                'sentiment_summary': session_data.get('sentiment_analysis', {}),
                'message_count': len(session_data.get('transcript', [])),
                'duration_seconds': session_data.get('duration_seconds', 0),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'ended_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Upsert session (insert or update)
            response = self.client.table('sessions').upsert(session_record).execute()
            
            logger.info(f"Session {session_data['session_id']} saved for user {session_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_data.get('session_id')}: {str(e)}")
            return False
    
    def get_session_with_summary(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data including summaries"""
        try:
            response = self.client.table('sessions').select('*').eq('id', session_id).execute()
            
            if not response.data:
                return None
            
            session = response.data[0]
            return {
                'session_id': session['id'],
                'user_id': session['user_id'],
                'created_at': session['created_at'],
                'ended_at': session['ended_at'],
                'transcript': session['transcript'] or [],
                'topic_summary': session['topic_summary'],
                'sentiment_summary': session['sentiment_summary'] or {},
                'duration_seconds': session['duration_seconds'],
                'message_count': session['message_count']
            }
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None
    
    def get_user_sessions_with_summaries(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent sessions for a user with summaries"""
        try:
            response = self.client.table('sessions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            results = []
            for session in response.data:
                results.append({
                    'session_id': session['id'],
                    'created_at': session['created_at'],
                    'ended_at': session['ended_at'],
                    'topic_summary': session['topic_summary'],
                    'sentiment_summary': session['sentiment_summary'] or {},
                    'message_count': session['message_count'],
                    'duration_seconds': session['duration_seconds']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving sessions for user {user_id}: {str(e)}")
            return []
    
    # Personality Profile Management
    def get_or_create_personality_profile(self, user_id: str) -> Dict:
        """Get existing personality profile or create new one"""
        try:
            # Ensure user exists
            self.get_or_create_user(user_id)
            
            # Try to get existing profile
            response = self.client.table('personality_profiles').select('*').eq('user_id', user_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                # Create new profile
                new_profile = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'extroversion_score': 0.5,
                    'sensing_score': 0.5,
                    'thinking_score': 0.5,
                    'judging_score': 0.5,
                    'overall_confidence': 0.0,
                    'extroversion_confidence': 0.0,
                    'sensing_confidence': 0.0,
                    'thinking_confidence': 0.0,
                    'judging_confidence': 0.0,
                    'evidence_log': [],
                    'sessions_analyzed': 0,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                response = self.client.table('personality_profiles').insert(new_profile).execute()
                return response.data[0]
                
        except Exception as e:
            logger.error(f"Error getting/creating personality profile for user {user_id}: {str(e)}")
            return {}
    
    def update_personality_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update personality profile data"""
        try:
            profile_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            response = self.client.table('personality_profiles').update(profile_data).eq('user_id', user_id).execute()
            
            logger.info(f"Personality profile updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating personality profile for user {user_id}: {str(e)}")
            return False
    
    def get_personality_profile(self, user_id: str) -> Optional[Dict]:
        """Get personality profile for a user"""
        try:
            response = self.client.table('personality_profiles').select('*').eq('user_id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving personality profile for user {user_id}: {str(e)}")
            return None
    
    # Legacy methods for backward compatibility
    async def get_user_transcripts(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Fetch transcripts for a specific user from Supabase"""
        try:
            sessions = self.get_user_sessions_with_summaries(user_id, limit)
            return [{'transcript': session.get('transcript', [])} for session in sessions]
        except Exception as e:
            logger.error(f"Error fetching transcripts for user {user_id}: {str(e)}")
            return []
    
    async def get_recent_transcripts(self, user_id: str, hours: int = 24) -> List[Dict]:
        """Fetch recent transcripts for a user within specified hours"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            response = self.client.table('sessions').select('*').eq('user_id', user_id).gte('created_at', cutoff_time.isoformat()).order('created_at', desc=True).execute()
            
            return [{'transcript': session.get('transcript', [])} for session in response.data]
        except Exception as e:
            logger.error(f"Error fetching recent transcripts for user {user_id}: {str(e)}")
            return []
    
    async def get_transcript_by_session(self, session_id: str) -> Optional[Dict]:
        """Fetch a specific transcript by session ID"""
        try:
            session = self.get_session_with_summary(session_id)
            return {'transcript': session.get('transcript', [])} if session else None
        except Exception as e:
            logger.error(f"Error fetching transcript for session {session_id}: {str(e)}")
            return None
    
    async def save_processed_session(self, session_data: Dict) -> bool:
        """Save processed session data back to Supabase"""
        return self.save_session_with_summary(session_data)
    
    async def update_user_personality(self, user_id: str, personality_data: Dict) -> bool:
        """Update user personality data in Supabase"""
        return self.update_personality_profile(user_id, personality_data)

# Global instance
supabase_service = SupabaseService() 