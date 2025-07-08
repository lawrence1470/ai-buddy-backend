# Database Schema Documentation for Supabase Tables
# This file documents the database schema used with Supabase

from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

# Database Schema Documentation
SUPABASE_SCHEMA = {
    'users': {
        'columns': {
            'id': 'TEXT PRIMARY KEY',
            'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            'device_id': 'TEXT UNIQUE',
            'last_active': 'TIMESTAMP WITH TIME ZONE'
        },
        'description': 'User records with device tracking'
    },
    'sessions': {
        'columns': {
            'id': 'TEXT PRIMARY KEY',
            'user_id': 'TEXT REFERENCES users(id)',
            'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            'ended_at': 'TIMESTAMP WITH TIME ZONE',
            'transcript': 'JSONB',
            'duration_seconds': 'INTEGER DEFAULT 0',
            'message_count': 'INTEGER DEFAULT 0',
            'topic_summary': 'TEXT',
            'sentiment_summary': 'JSONB'
        },
        'description': 'Chat sessions with AI analysis results'
    },
    'personality_profiles': {
        'columns': {
            'id': 'TEXT PRIMARY KEY',
            'user_id': 'TEXT UNIQUE REFERENCES users(id)',
            'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            'extroversion_score': 'FLOAT DEFAULT 0.5',
            'sensing_score': 'FLOAT DEFAULT 0.5',
            'thinking_score': 'FLOAT DEFAULT 0.5',
            'judging_score': 'FLOAT DEFAULT 0.5',
            'overall_confidence': 'FLOAT DEFAULT 0.0',
            'extroversion_confidence': 'FLOAT DEFAULT 0.0',
            'sensing_confidence': 'FLOAT DEFAULT 0.0',
            'thinking_confidence': 'FLOAT DEFAULT 0.0',
            'judging_confidence': 'FLOAT DEFAULT 0.0',
            'evidence_log': 'JSONB DEFAULT \'[]\'',
            'sessions_analyzed': 'INTEGER DEFAULT 0'
        },
        'description': 'MBTI personality profiles with confidence scores'
    }
}

# Utility functions for data conversion and validation
def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def calculate_mbti_type(scores: Dict[str, float]) -> str:
    """Calculate MBTI type string from personality scores"""
    e_or_i = 'E' if scores.get('extroversion', 0.5) > 0.5 else 'I'
    s_or_n = 'S' if scores.get('sensing', 0.5) > 0.5 else 'N'
    t_or_f = 'T' if scores.get('thinking', 0.5) > 0.5 else 'F'
    j_or_p = 'J' if scores.get('judging', 0.5) > 0.5 else 'P'
    return f"{e_or_i}{s_or_n}{t_or_f}{j_or_p}"

def validate_personality_scores(scores: Dict[str, float]) -> bool:
    """Validate that personality scores are in valid range (0.0 to 1.0)"""
    required_dimensions = ['extroversion', 'sensing', 'thinking', 'judging']
    
    for dim in required_dimensions:
        if dim not in scores:
            return False
        score = scores[dim]
        if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
            return False
    
    return True

def create_user_record(user_id: str, device_id: str = None) -> Dict:
    """Create a new user record"""
    return {
        'id': user_id,
        'device_id': device_id,
        'created_at': get_current_timestamp(),
        'updated_at': get_current_timestamp(),
        'last_active': get_current_timestamp()
    }

def create_session_record(session_id: str, user_id: str, **kwargs) -> Dict:
    """Create a new session record"""
    return {
        'id': session_id,
        'user_id': user_id,
        'created_at': get_current_timestamp(),
        'ended_at': kwargs.get('ended_at', get_current_timestamp()),
        'transcript': kwargs.get('transcript', []),
        'duration_seconds': kwargs.get('duration_seconds', 0),
        'message_count': kwargs.get('message_count', 0),
        'topic_summary': kwargs.get('topic_summary'),
        'sentiment_summary': kwargs.get('sentiment_summary', {})
    }

def create_personality_profile_record(user_id: str) -> Dict:
    """Create a new personality profile record with default values"""
    return {
        'id': generate_uuid(),
        'user_id': user_id,
        'created_at': get_current_timestamp(),
        'updated_at': get_current_timestamp(),
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
        'sessions_analyzed': 0
    } 