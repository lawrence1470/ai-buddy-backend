import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timezone
import uuid
import json

from config import Config

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        if not Config.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")
        
        self.connection_string = Config.DATABASE_URL
        self._ensure_tables()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Users table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id VARCHAR PRIMARY KEY,
                            device_id VARCHAR,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            selected_buddy_id VARCHAR DEFAULT 'oliver'
                        )
                    """)
                    
                    # Sessions table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            id VARCHAR PRIMARY KEY,
                            user_id VARCHAR REFERENCES users(id),
                            transcript JSONB,
                            topic_summary TEXT,
                            sentiment_summary JSONB,
                            message_count INTEGER DEFAULT 0,
                            duration_seconds INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            ended_at TIMESTAMP WITH TIME ZONE
                        )
                    """)
                    
                    # Personality profiles table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS personality_profiles (
                            id VARCHAR PRIMARY KEY,
                            user_id VARCHAR REFERENCES users(id) UNIQUE,
                            extroversion_score FLOAT DEFAULT 0.5,
                            sensing_score FLOAT DEFAULT 0.5,
                            thinking_score FLOAT DEFAULT 0.5,
                            judging_score FLOAT DEFAULT 0.5,
                            overall_confidence FLOAT DEFAULT 0.0,
                            extroversion_confidence FLOAT DEFAULT 0.0,
                            sensing_confidence FLOAT DEFAULT 0.0,
                            thinking_confidence FLOAT DEFAULT 0.0,
                            judging_confidence FLOAT DEFAULT 0.0,
                            evidence_log JSONB DEFAULT '[]',
                            sessions_analyzed INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    
                    conn.commit()
                    logger.info("Database tables ensured")
        except Exception as e:
            logger.error(f"Error ensuring database tables: {str(e)}")
    
    # User Management
    def get_or_create_user(self, user_id: str, device_id: str = None) -> Dict:
        """Get existing user or create new one"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # First try to get existing user
                    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user = cur.fetchone()
                    
                    if user:
                        # Update last_active
                        cur.execute(
                            "UPDATE users SET last_active = %s WHERE id = %s",
                            (datetime.now(timezone.utc), user_id)
                        )
                        conn.commit()
                        return dict(user)
                    else:
                        # Create new user
                        cur.execute("""
                            INSERT INTO users (id, device_id, created_at, updated_at, last_active)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING *
                        """, (
                            user_id,
                            device_id,
                            datetime.now(timezone.utc),
                            datetime.now(timezone.utc),
                            datetime.now(timezone.utc)
                        ))
                        user = cur.fetchone()
                        conn.commit()
                        return dict(user)
                        
        except Exception as e:
            logger.error(f"Error getting/creating user {user_id}: {str(e)}")
            return {}
    
    # Session Management
    def save_session_with_summary(self, session_data: Dict) -> bool:
        """Save session data including AI-generated summaries"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure user exists
                    self.get_or_create_user(session_data['user_id'])
                    
                    # Upsert session
                    cur.execute("""
                        INSERT INTO sessions (id, user_id, transcript, topic_summary, sentiment_summary, 
                                            message_count, duration_seconds, created_at, ended_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            transcript = EXCLUDED.transcript,
                            topic_summary = EXCLUDED.topic_summary,
                            sentiment_summary = EXCLUDED.sentiment_summary,
                            message_count = EXCLUDED.message_count,
                            duration_seconds = EXCLUDED.duration_seconds,
                            ended_at = EXCLUDED.ended_at
                    """, (
                        session_data['session_id'],
                        session_data['user_id'],
                        json.dumps(session_data.get('transcript', [])),
                        session_data.get('session_summary'),
                        json.dumps(session_data.get('sentiment_analysis', {})),
                        len(session_data.get('transcript', [])),
                        session_data.get('duration_seconds', 0),
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc)
                    ))
                    
                    conn.commit()
                    logger.info(f"Session {session_data['session_id']} saved for user {session_data['user_id']}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving session {session_data.get('session_id')}: {str(e)}")
            return False
    
    def get_session_with_summary(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data including summaries"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
                    session = cur.fetchone()
                    
                    if not session:
                        return None
                    
                    return {
                        'session_id': session['id'],
                        'user_id': session['user_id'],
                        'created_at': session['created_at'].isoformat(),
                        'ended_at': session['ended_at'].isoformat() if session['ended_at'] else None,
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
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM sessions 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (user_id, limit))
                    
                    sessions = cur.fetchall()
                    results = []
                    
                    for session in sessions:
                        results.append({
                            'session_id': session['id'],
                            'created_at': session['created_at'].isoformat(),
                            'ended_at': session['ended_at'].isoformat() if session['ended_at'] else None,
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
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Ensure user exists
                    self.get_or_create_user(user_id)
                    
                    # Try to get existing profile
                    cur.execute("SELECT * FROM personality_profiles WHERE user_id = %s", (user_id,))
                    profile = cur.fetchone()
                    
                    if profile:
                        return dict(profile)
                    else:
                        # Create new profile
                        profile_id = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO personality_profiles (id, user_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s)
                            RETURNING *
                        """, (
                            profile_id,
                            user_id,
                            datetime.now(timezone.utc),
                            datetime.now(timezone.utc)
                        ))
                        profile = cur.fetchone()
                        conn.commit()
                        return dict(profile)
                        
        except Exception as e:
            logger.error(f"Error getting/creating personality profile for user {user_id}: {str(e)}")
            return {}
    
    def update_personality_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update personality profile data"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Build update query dynamically
                    update_fields = []
                    update_values = []
                    
                    allowed_fields = [
                        'extroversion_score', 'sensing_score', 'thinking_score', 'judging_score',
                        'overall_confidence', 'extroversion_confidence', 'sensing_confidence', 
                        'thinking_confidence', 'judging_confidence', 'evidence_log', 'sessions_analyzed'
                    ]
                    
                    for field in allowed_fields:
                        if field in profile_data:
                            update_fields.append(f"{field} = %s")
                            if field == 'evidence_log':
                                update_values.append(json.dumps(profile_data[field]))
                            else:
                                update_values.append(profile_data[field])
                    
                    update_fields.append("updated_at = %s")
                    update_values.append(datetime.now(timezone.utc))
                    update_values.append(user_id)
                    
                    cur.execute(f"""
                        UPDATE personality_profiles 
                        SET {', '.join(update_fields)}
                        WHERE user_id = %s
                    """, update_values)
                    
                    conn.commit()
                    logger.info(f"Personality profile updated for user {user_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating personality profile for user {user_id}: {str(e)}")
            return False
    
    def get_personality_profile(self, user_id: str) -> Optional[Dict]:
        """Get personality profile for a user"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM personality_profiles WHERE user_id = %s", (user_id,))
                    profile = cur.fetchone()
                    
                    if profile:
                        return dict(profile)
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving personality profile for user {user_id}: {str(e)}")
            return None
    
    # Legacy methods for backward compatibility
    async def get_user_transcripts(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Fetch transcripts for a specific user"""
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
            
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM sessions 
                        WHERE user_id = %s AND created_at >= %s 
                        ORDER BY created_at DESC
                    """, (user_id, cutoff_time))
                    
                    sessions = cur.fetchall()
                    return [{'transcript': session.get('transcript', [])} for session in sessions]
                    
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
        """Save processed session data"""
        return self.save_session_with_summary(session_data)
    
    async def update_user_personality(self, user_id: str, personality_data: Dict) -> bool:
        """Update user personality data"""
        return self.update_personality_profile(user_id, personality_data)
    
    # Buddy Selection Methods
    def select_buddy(self, user_id: str, buddy_id: str) -> bool:
        """Select preferred AI buddy for a user"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure user exists
                    self.get_or_create_user(user_id)
                    
                    # Update user with selected buddy
                    cur.execute("""
                        UPDATE users 
                        SET selected_buddy_id = %s, updated_at = %s 
                        WHERE id = %s
                    """, (buddy_id, datetime.now(timezone.utc), user_id))
                    
                    conn.commit()
                    logger.info(f"Buddy {buddy_id} selected for user {user_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error selecting buddy for user {user_id}: {str(e)}")
            return False
    
    def get_selected_buddy(self, user_id: str) -> Optional[str]:
        """Get user's selected AI buddy"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT selected_buddy_id FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    
                    if result:
                        return result['selected_buddy_id']
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting selected buddy for user {user_id}: {str(e)}")
            return None
    
    def get_user_with_buddy(self, user_id: str) -> Optional[Dict]:
        """Get user data including selected buddy"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user = cur.fetchone()
                    
                    if user:
                        return dict(user)
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user with buddy data for user {user_id}: {str(e)}")
            return None

# Global instance
database_service = DatabaseService() 