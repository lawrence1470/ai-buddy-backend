from celery import Celery
import asyncio
import logging
from datetime import datetime, timezone

from config import Config
from services.supabase_service import supabase_service
from services.summary_service import summary_service
from services.personality_service import personality_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'personality_backend',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

@celery_app.task
def process_session_async(user_id: str, session_id: str, transcript: list):
    """Background task to process a session"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generate session summary
            session_summary = loop.run_until_complete(
                summary_service.generate_session_summary(transcript)
            )
            
            # Analyze sentiment
            sentiment_analysis = loop.run_until_complete(
                summary_service.analyze_sentiment(transcript)
            )
            
            # Update personality profile
            personality_update = loop.run_until_complete(
                personality_service.update_personality_from_session(
                    user_id, transcript, session_summary
                )
            )
            
            # Save to Supabase
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'transcript': transcript,
                'summary': session_summary,
                'sentiment': sentiment_analysis,
                'personality_update': personality_update,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
            loop.run_until_complete(
                supabase_service.save_processed_session(session_data)
            )
            
            logger.info(f"Successfully processed session {session_id} for user {user_id}")
            return {
                'success': True,
                'session_id': session_id,
                'personality_type': personality_update.get('mbti_type', 'Unknown')
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing session {session_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery_app.task
def batch_process_user_sessions(user_id: str, limit: int = 50):
    """Background task to batch process all sessions for a user"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Fetch transcripts from Supabase
            transcripts = loop.run_until_complete(
                supabase_service.get_user_transcripts(user_id, limit)
            )
            
            processed_count = 0
            
            for transcript_data in transcripts:
                session_transcript = transcript_data.get('messages', [])
                session_id = transcript_data.get('id')
                
                if session_transcript:
                    # Process this session
                    result = process_session_async.delay(user_id, session_id, session_transcript)
                    processed_count += 1
            
            logger.info(f"Queued {processed_count} sessions for processing for user {user_id}")
            return {'success': True, 'queued_sessions': processed_count}
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error batch processing sessions for user {user_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # Start Celery worker
    celery_app.start() 