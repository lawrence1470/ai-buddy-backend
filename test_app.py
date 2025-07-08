from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime, timezone
import json

from test_config import TestConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config.from_object(TestConfig)
CORS(app)

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
        'mode': 'test',
        'services': {
            'database': 'supabase (test mode)',
            'supabase': 'mocked',
            'openai': 'mocked'
        }
    }, 200

# Mock session processing endpoint for testing
@app.route('/api/sessions/process', methods=['POST'])
def process_session():
    """Mock session processing for testing"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        transcript = data.get('transcript', [])
        
        if not user_id or not transcript:
            return {'error': 'user_id and transcript are required'}, 400
        
        # Mock response for testing
        mock_response = {
            'success': True,
            'session_summary': f'Mock summary for session {session_id}: User discussed various topics showing personality traits.',
            'sentiment_analysis': {
                'overall_sentiment': 0.6,
                'emotions': ['confident', 'analytical'],
                'tone': 'positive'
            },
            'personality_update': {
                'mbti_type': 'ENTJ',
                'scores': {
                    'extroversion': 0.7,
                    'sensing': 0.4,
                    'thinking': 0.8,
                    'judging': 0.75
                },
                'confidence': {
                    'overall': 0.65,
                    'extroversion': 0.6,
                    'sensing': 0.5,
                    'thinking': 0.8,
                    'judging': 0.7
                },
                'sessions_analyzed': 1
            }
        }
        
        return mock_response
        
    except Exception as e:
        logger.error(f"Error processing session: {str(e)}")
        return {'error': 'Internal server error'}, 500

@app.route('/api/personality/<user_id>', methods=['GET'])
def get_personality_insights(user_id):
    """Mock personality insights for testing"""
    try:
        mock_insights = {
            'mbti_type': 'ENTJ',
            'type_description': 'The Commander - Natural-born leaders, strategic and decisive',
            'scores': {
                'extroversion': 0.75,
                'sensing': 0.45,
                'thinking': 0.82,
                'judging': 0.79
            },
            'confidence': {
                'overall': 0.73,
                'extroversion': 0.68,
                'sensing': 0.52,
                'thinking': 0.85,
                'judging': 0.74
            },
            'facet_bars': [
                {'name': 'Extroversion', 'score': 0.75, 'confidence': 0.68, 'label': 'E'},
                {'name': 'Sensing', 'score': 0.45, 'confidence': 0.52, 'label': 'N'},
                {'name': 'Thinking', 'score': 0.82, 'confidence': 0.85, 'label': 'T'},
                {'name': 'Judging', 'score': 0.79, 'confidence': 0.74, 'label': 'J'}
            ],
            'sessions_analyzed': 5,
            'recent_evidence': [
                {'timestamp': '2024-01-01T10:00:00Z', 'evidence': 'Prefers structured planning'},
                {'timestamp': '2024-01-01T11:00:00Z', 'evidence': 'Makes decisions based on logic'}
            ],
            'created_at': '2024-01-01T09:00:00Z',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        return mock_insights
        
    except Exception as e:
        logger.error(f"Error getting personality insights: {str(e)}")
        return {'error': 'Internal server error'}, 500

@app.route('/api/personality/<user_id>/type', methods=['GET'])
def get_personality_type(user_id):
    """Mock personality type for testing"""
    return {
        'mbti_type': 'ENTJ',
        'type_description': 'The Commander - Natural-born leaders, strategic and decisive',
        'overall_confidence': 0.73,
        'sessions_analyzed': 5
    }

@app.route('/api/personality/<user_id>/facets', methods=['GET'])
def get_personality_facets(user_id):
    """Mock personality facets for testing"""
    return {
        'mbti_type': 'ENTJ',
        'facet_bars': [
            {'name': 'Extroversion', 'score': 0.75, 'confidence': 0.68, 'label': 'E'},
            {'name': 'Sensing', 'score': 0.45, 'confidence': 0.52, 'label': 'N'},
            {'name': 'Thinking', 'score': 0.82, 'confidence': 0.85, 'label': 'T'},
            {'name': 'Judging', 'score': 0.79, 'confidence': 0.74, 'label': 'J'}
        ]
    }

@app.route('/api/memory/<user_id>/recent', methods=['GET'])
def get_recent_memory(user_id):
    """Mock recent memory for testing"""
    return {
        'recent_sessions': [
            {'id': 'session-1', 'summary': 'User discussed career planning'},
            {'id': 'session-2', 'summary': 'User talked about team leadership'}
        ],
        'personality_type': 'ENTJ',
        'recent_evidence': [
            {'evidence': 'Shows leadership qualities', 'confidence': 0.8},
            {'evidence': 'Prefers structured approach', 'confidence': 0.7}
        ]
    }

@app.route('/api/analytics/summary', methods=['POST'])
def generate_summary():
    """Mock summary generation for testing"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', [])
        
        if not transcript:
            return {'error': 'transcript is required'}, 400
        
        return {
            'summary': 'Mock summary: The conversation shows the user discussing planning and decision-making with a structured approach.',
            'sentiment': {
                'overall_sentiment': 0.6,
                'subjectivity': 0.4,
                'emotions': ['confident', 'analytical'],
                'intensity': 6,
                'tone': 'positive'
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    logger.info("Starting AI Personality Backend (Test Mode)...")
    app.run(debug=True, host='0.0.0.0', port=8000) 