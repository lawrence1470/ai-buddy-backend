from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import logging
from datetime import datetime, timezone
import traceback

from config import Config
from models.database import create_tables
from services.supabase_service import supabase_service
from services.summary_service import summary_service
from services.personality_service import personality_service
from services.chat_service import chat_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize database
create_tables()

@app.route('/')
def hello_world():
    """Health check endpoint"""
    return {'message': 'AI Personality Backend is running!', 'status': 'healthy'}

@app.route('/health')
def health_check():
    """Detailed health check"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'services': {
            'supabase': 'connected' if Config.SUPABASE_URL else 'not configured',
            'openai': 'configured' if Config.OPENAI_API_KEY else 'not configured'
        }
    }, 200

# ==================== SESSION MANAGEMENT ====================

@app.route('/api/sessions/process', methods=['POST'])
def process_session():
    """Process a completed session and update personality profile"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        transcript = data.get('transcript', [])
        
        if not user_id or not transcript:
            return {'error': 'user_id and transcript are required'}, 400
        
        # Run async operations
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
            
            return {
                'success': True,
                'session_summary': session_summary,
                'sentiment_analysis': sentiment_analysis,
                'personality_update': personality_update
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing session: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': 'Internal server error'}, 500

@app.route('/api/sessions/batch-process', methods=['POST'])
def batch_process_sessions():
    """Process multiple sessions from Supabase for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        limit = data.get('limit', 50)
        
        if not user_id:
            return {'error': 'user_id is required'}, 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Fetch transcripts from Supabase
            transcripts = loop.run_until_complete(
                supabase_service.get_user_transcripts(user_id, limit)
            )
            
            if not transcripts:
                return {'message': 'No transcripts found for user'}, 404
            
            processed_sessions = []
            
            for transcript_data in transcripts:
                session_transcript = transcript_data.get('messages', [])
                session_id = transcript_data.get('id')
                
                if session_transcript:
                    # Generate summary
                    session_summary = loop.run_until_complete(
                        summary_service.generate_session_summary(session_transcript)
                    )
                    
                    # Update personality
                    personality_update = loop.run_until_complete(
                        personality_service.update_personality_from_session(
                            user_id, session_transcript, session_summary
                        )
                    )
                    
                    processed_sessions.append({
                        'session_id': session_id,
                        'summary': session_summary,
                        'personality_update': personality_update
                    })
            
            return {
                'success': True,
                'processed_count': len(processed_sessions),
                'sessions': processed_sessions
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error batch processing sessions: {str(e)}")
        return {'error': 'Internal server error'}, 500

# ==================== PERSONALITY INSIGHTS ====================

@app.route('/api/personality/<user_id>', methods=['GET'])
def get_personality_insights(user_id):
    """Get comprehensive personality insights for a user"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            insights = loop.run_until_complete(
                personality_service.get_personality_insights(user_id)
            )
            
            if not insights:
                return {'error': 'No personality profile found for user'}, 404
            
            return insights
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting personality insights: {str(e)}")
        return {'error': 'Internal server error'}, 500

@app.route('/api/personality/<user_id>/type', methods=['GET'])
def get_personality_type(user_id):
    """Get just the MBTI type and confidence for a user"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            insights = loop.run_until_complete(
                personality_service.get_personality_insights(user_id)
            )
            
            if not insights:
                return {'error': 'No personality profile found for user'}, 404
            
            return {
                'mbti_type': insights['mbti_type'],
                'type_description': insights['type_description'],
                'overall_confidence': insights['confidence']['overall'],
                'sessions_analyzed': insights['sessions_analyzed']
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting personality type: {str(e)}")
        return {'error': 'Internal server error'}, 500

@app.route('/api/personality/<user_id>/facets', methods=['GET'])
def get_personality_facets(user_id):
    """Get personality facet bars for UI"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            insights = loop.run_until_complete(
                personality_service.get_personality_insights(user_id)
            )
            
            if not insights:
                return {'error': 'No personality profile found for user'}, 404
            
            return {
                'facet_bars': insights['facet_bars'],
                'mbti_type': insights['mbti_type']
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting personality facets: {str(e)}")
        return {'error': 'Internal server error'}, 500

# ==================== CONVERSATIONAL MEMORY ====================

@app.route('/api/memory/<user_id>/recent', methods=['GET'])
def get_recent_memory(user_id):
    """Get recent session summaries for conversational memory"""
    try:
        hours = request.args.get('hours', 72, type=int)  # Default 3 days
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get recent transcripts
            recent_transcripts = loop.run_until_complete(
                supabase_service.get_recent_transcripts(user_id, hours)
            )
            
            # Get personality insights for context
            personality = loop.run_until_complete(
                personality_service.get_personality_insights(user_id)
            )
            
            memory_context = {
                'recent_sessions': recent_transcripts[:3],  # Last 3 sessions
                'personality_type': personality['mbti_type'] if personality else 'Unknown',
                'recent_evidence': personality['recent_evidence'][:3] if personality else []
            }
            
            return memory_context
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting recent memory: {str(e)}")
        return {'error': 'Internal server error'}, 500

# ==================== ANALYTICS & SUMMARY ====================

@app.route('/api/analytics/summary', methods=['POST'])
def generate_summary():
    """Generate summary for a given transcript"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', [])
        
        if not transcript:
            return {'error': 'transcript is required'}, 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            summary = loop.run_until_complete(
                summary_service.generate_session_summary(transcript)
            )
            
            sentiment = loop.run_until_complete(
                summary_service.analyze_sentiment(transcript)
            )
            
            return {
                'summary': summary,
                'sentiment': sentiment
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {'error': 'Internal server error'}, 500

# ==================== CHAT ENDPOINT ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint that takes user text and returns AI response"""
    try:
        data = request.get_json()
        
        # Extract data from request
        user_message = data.get('text', data.get('message', ''))
        is_voice = data.get('is_voice', data.get('isVoice', False))
        user_id = data.get('user_id', data.get('userId'))
        conversation_context = data.get('conversation_context', data.get('context', []))
        
        # Validate required fields
        if not user_message or not user_message.strip():
            return {'error': 'text/message is required'}, 400
        
        # Get AI response using the chat service
        result = chat_service.get_ai_response_sync(
            user_message=user_message.strip(),
            is_voice=is_voice,
            user_id=user_id,
            conversation_context=conversation_context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'response': 'I apologize, but I encountered an error. Please try again.',
            'success': False,
            'error': 'Internal server error'
        }, 500

# ==================== USER MANAGEMENT ====================

@app.route('/api/users/<user_id>/reset', methods=['POST'])
def reset_user_personality(user_id):
    """Reset user's personality data"""
    try:
        from models.database import get_db, PersonalityProfile, User
        
        db = next(get_db())
        
        # Delete personality profile
        profile = db.query(PersonalityProfile).filter(PersonalityProfile.user_id == user_id).first()
        if profile:
            db.delete(profile)
            db.commit()
        
        db.close()
        
        return {'success': True, 'message': 'Personality data reset successfully'}
        
    except Exception as e:
        logger.error(f"Error resetting user personality: {str(e)}")
        return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    logger.info("Starting AI Personality Backend...")
    app.run(debug=True, host='0.0.0.0', port=8000) 