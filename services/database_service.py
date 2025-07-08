from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone

from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        # Use the global Supabase service instance
        self.supabase = supabase_service
    
    def save_session_with_summary(self, session_data: Dict) -> bool:
        """Save session data including AI-generated summaries to database"""
        return self.supabase.save_session_with_summary(session_data)
    
    def get_session_with_summary(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data including summaries"""
        return self.supabase.get_session_with_summary(session_id)
    
    def get_user_sessions_with_summaries(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent sessions for a user with summaries"""
        return self.supabase.get_user_sessions_with_summaries(user_id, limit)

# Global instance
database_service = DatabaseService() 