from flask import Flask, request, jsonify, render_template_string
from flask_restx import Api, Resource, fields
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

# Create API with OpenAPI documentation
api = Api(
    app,
    version='1.0.0',
    title='AI Personality Backend API',
    description='Advanced AI Personality Analysis System for voice-first conversational AI companions',
    doc='/docs/',  # Swagger UI will be at /docs/
    contact='AI Companion Team',
    license='MIT'
)

# Create namespaces for organization
health_ns = api.namespace('health', description='Health check operations')
sessions_ns = api.namespace('sessions', description='Session management operations')
personality_ns = api.namespace('personality', description='Personality analysis operations')
memory_ns = api.namespace('memory', description='Conversational memory operations')
analytics_ns = api.namespace('analytics', description='Analytics and summary operations')

# Define models for request/response documentation
transcript_message_model = api.model('TranscriptMessage', {
    'speaker': fields.String(required=True, description='Speaker identifier (User/AI)', example='User'),
    'content': fields.String(required=True, description='Message content', example='I love planning ahead and organizing my day'),
    'timestamp': fields.String(required=True, description='ISO timestamp', example='2024-01-01T10:00:00Z')
})

session_process_model = api.model('SessionProcess', {
    'user_id': fields.String(required=True, description='Unique user identifier', example='user-123'),
    'session_id': fields.String(required=True, description='Unique session identifier', example='session-456'),
    'transcript': fields.List(fields.Nested(transcript_message_model), required=True, description='Array of conversation messages')
})

personality_scores_model = api.model('PersonalityScores', {
    'extroversion': fields.Float(description='Extroversion score (0.0-1.0)', example=0.75),
    'sensing': fields.Float(description='Sensing score (0.0-1.0)', example=0.45),
    'thinking': fields.Float(description='Thinking score (0.0-1.0)', example=0.82),
    'judging': fields.Float(description='Judging score (0.0-1.0)', example=0.79)
})

confidence_model = api.model('Confidence', {
    'overall': fields.Float(description='Overall confidence (0.0-1.0)', example=0.73),
    'extroversion': fields.Float(description='Extroversion confidence', example=0.68),
    'sensing': fields.Float(description='Sensing confidence', example=0.52),
    'thinking': fields.Float(description='Thinking confidence', example=0.85),
    'judging': fields.Float(description='Judging confidence', example=0.74)
})

facet_bar_model = api.model('FacetBar', {
    'name': fields.String(description='Dimension name', example='Extroversion'),
    'score': fields.Float(description='Score (0.0-1.0)', example=0.75),
    'confidence': fields.Float(description='Confidence (0.0-1.0)', example=0.68),
    'label': fields.String(description='MBTI letter', example='E')
})

personality_update_model = api.model('PersonalityUpdate', {
    'mbti_type': fields.String(description='MBTI personality type', example='ENTJ'),
    'scores': fields.Nested(personality_scores_model),
    'confidence': fields.Nested(confidence_model),
    'sessions_analyzed': fields.Integer(description='Number of sessions analyzed', example=5)
})

# Health endpoints
@health_ns.route('')
class HealthCheck(Resource):
    @health_ns.doc('health_check')
    @health_ns.marshal_with(api.model('HealthResponse', {
        'status': fields.String(description='Service status', example='healthy'),
        'timestamp': fields.String(description='Current timestamp'),
        'version': fields.String(description='API version', example='1.0.0'),
        'mode': fields.String(description='Running mode', example='test'),
        'services': fields.Raw(description='Service status details')
    }))
    def get(self):
        """Get system health status"""
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
        }

# Session endpoints
@sessions_ns.route('/process')
class ProcessSession(Resource):
    @sessions_ns.doc('process_session')
    @sessions_ns.expect(session_process_model)
    @sessions_ns.marshal_with(api.model('SessionProcessResponse', {
        'success': fields.Boolean(description='Processing success', example=True),
        'session_summary': fields.String(description='Generated session summary'),
        'sentiment_analysis': fields.Raw(description='Sentiment analysis results'),
        'personality_update': fields.Nested(personality_update_model)
    }))
    def post(self):
        """Process a completed conversation session"""
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        transcript = data.get('transcript', [])
        
        if not user_id or not transcript:
            api.abort(400, 'user_id and transcript are required')
        
        # Mock response for testing
        return {
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

@sessions_ns.route('/batch-process')
class BatchProcessSessions(Resource):
    @sessions_ns.doc('batch_process_sessions')
    @sessions_ns.expect(api.model('BatchProcessRequest', {
        'user_id': fields.String(required=True, description='User ID', example='user-123'),
        'limit': fields.Integer(description='Max sessions to process', example=50)
    }))
    def post(self):
        """Batch process multiple sessions from Supabase"""
        data = request.get_json()
        user_id = data.get('user_id')
        limit = data.get('limit', 50)
        
        if not user_id:
            api.abort(400, 'user_id is required')
        
        return {
            'success': True,
            'processed_count': 3,
            'message': f'Mock: Processed 3 sessions for user {user_id}'
        }

# Personality endpoints
@personality_ns.route('/<user_id>')
class PersonalityInsights(Resource):
    @personality_ns.doc('get_personality_insights')
    @personality_ns.marshal_with(api.model('PersonalityInsightsResponse', {
        'mbti_type': fields.String(description='MBTI type', example='ENTJ'),
        'type_description': fields.String(description='Type description'),
        'scores': fields.Nested(personality_scores_model),
        'confidence': fields.Nested(confidence_model),
        'facet_bars': fields.List(fields.Nested(facet_bar_model)),
        'sessions_analyzed': fields.Integer(example=5),
        'recent_evidence': fields.List(fields.Raw()),
        'created_at': fields.String(),
        'updated_at': fields.String()
    }))
    def get(self, user_id):
        """Get comprehensive personality insights for a user"""
        return {
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

@personality_ns.route('/<user_id>/type')
class PersonalityType(Resource):
    @personality_ns.doc('get_personality_type')
    @personality_ns.marshal_with(api.model('PersonalityTypeResponse', {
        'mbti_type': fields.String(example='ENTJ'),
        'type_description': fields.String(),
        'overall_confidence': fields.Float(example=0.73),
        'sessions_analyzed': fields.Integer(example=5)
    }))
    def get(self, user_id):
        """Get MBTI type and confidence for a user"""
        return {
            'mbti_type': 'ENTJ',
            'type_description': 'The Commander - Natural-born leaders, strategic and decisive',
            'overall_confidence': 0.73,
            'sessions_analyzed': 5
        }

@personality_ns.route('/<user_id>/facets')
class PersonalityFacets(Resource):
    @personality_ns.doc('get_personality_facets')
    @personality_ns.marshal_with(api.model('PersonalityFacetsResponse', {
        'mbti_type': fields.String(example='ENTJ'),
        'facet_bars': fields.List(fields.Nested(facet_bar_model))
    }))
    def get(self, user_id):
        """Get personality facet bars for UI display"""
        return {
            'mbti_type': 'ENTJ',
            'facet_bars': [
                {'name': 'Extroversion', 'score': 0.75, 'confidence': 0.68, 'label': 'E'},
                {'name': 'Sensing', 'score': 0.45, 'confidence': 0.52, 'label': 'N'},
                {'name': 'Thinking', 'score': 0.82, 'confidence': 0.85, 'label': 'T'},
                {'name': 'Judging', 'score': 0.79, 'confidence': 0.74, 'label': 'J'}
            ]
        }

# Memory endpoints
@memory_ns.route('/<user_id>/recent')
class RecentMemory(Resource):
    @memory_ns.doc('get_recent_memory')
    @memory_ns.param('hours', 'Hours to look back', type='integer', default=72)
    def get(self, user_id):
        """Get recent session summaries for conversational memory"""
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

# Analytics endpoints
@analytics_ns.route('/summary')
class GenerateSummary(Resource):
    @analytics_ns.doc('generate_summary')
    @analytics_ns.expect(api.model('SummaryRequest', {
        'transcript': fields.List(fields.Nested(transcript_message_model), required=True)
    }))
    def post(self):
        """Generate summary and sentiment analysis for a transcript"""
        data = request.get_json()
        transcript = data.get('transcript', [])
        
        if not transcript:
            api.abort(400, 'transcript is required')
        
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

# Scalar documentation route
SCALAR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Personality Backend API</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        body { margin: 0; }
    </style>
</head>
<body>
    <script
        id="api-reference"
        data-url="/swagger.json"
        data-configuration='{
            "theme": "purple",
            "showSidebar": true,
            "hideDownloadButton": false,
            "searchHotKey": "k"
        }'
    ></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>
"""

@app.route('/scalar')
def scalar_docs():
    """Scalar API Documentation"""
    return render_template_string(SCALAR_HTML)

@app.route('/')
def index():
    """Root endpoint with links to documentation"""
    return {
        'message': 'AI Personality Backend API',
        'version': '1.0.0',
        'documentation': {
            'swagger_ui': '/docs/',
            'scalar_ui': '/scalar',
            'openapi_spec': '/swagger.json'
        },
        'endpoints': {
            'health': '/health',
            'process_session': '/sessions/process',
            'personality_insights': '/personality/{user_id}',
            'personality_type': '/personality/{user_id}/type',
            'personality_facets': '/personality/{user_id}/facets',
            'recent_memory': '/memory/{user_id}/recent',
            'generate_summary': '/analytics/summary'
        }
    }

if __name__ == '__main__':
    logger.info("Starting AI Personality Backend with OpenAPI Documentation...")
    logger.info("📚 Swagger UI: http://localhost:8000/docs/")
    logger.info("✨ Scalar UI: http://localhost:8000/scalar")
    logger.info("📋 OpenAPI Spec: http://localhost:8000/swagger.json")
    app.run(debug=True, host='0.0.0.0', port=8000) 