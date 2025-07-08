#!/usr/bin/env python3

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    """Health check endpoint"""
    return {'message': 'AI Chat Server is running!', 'status': 'healthy'}

@app.route('/health')
def health_check():
    """Detailed health check"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'services': {
            'openai': 'configured' if os.getenv('OPENAI_API_KEY') else 'not configured'
        }
    }, 200

@app.route('/chat', methods=['POST'])
def chat():
    """AI Chat Conversation endpoint"""
    try:
        data = request.get_json()
        
        # Extract data from request
        user_message = data.get('text', data.get('message', ''))
        is_voice = data.get('is_voice', data.get('isVoice', False))
        user_id = data.get('user_id', data.get('userId'))
        conversation_context = data.get('conversation_context', data.get('context', []))
        
        # Validate required fields
        if not user_message or not user_message.strip():
            return jsonify({'error': 'text/message is required'}), 400
        
        # Check if OpenAI API key is configured
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({
                'response': 'OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file.',
                'success': False,
                'error': 'Missing API key'
            }), 500
        
        # Import and use the chat service
        try:
            from services.chat_service import chat_service
            
            # Get AI response using the chat service
            result = chat_service.get_ai_response_sync(
                user_message=user_message.strip(),
                is_voice=is_voice,
                user_id=user_id,
                conversation_context=conversation_context
            )
            
            return jsonify(result)
            
        except ImportError as e:
            logger.error(f"Could not import chat service: {e}")
            return jsonify({
                'response': 'Chat service is not available. Please check server configuration.',
                'success': False,
                'error': 'Service unavailable'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'response': 'I apologize, but I encountered an error. Please try again.',
            'success': False,
            'error': 'Internal server error'
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Simple AI Chat Server...")
    logger.info("=" * 50)
    logger.info("🏠 Server:        http://localhost:8080")
    logger.info("💬 Chat Endpoint: http://localhost:8080/chat")
    logger.info("🏥 Health Check:  http://localhost:8080/health")
    logger.info("=" * 50)
    
    # Check OpenAI API key
    if os.getenv('OPENAI_API_KEY'):
        logger.info("✅ OpenAI API key found")
    else:
        logger.warning("⚠️  OpenAI API key not found - chat will not work")
    
    logger.info("✨ Ready to chat!")
    app.run(debug=True, host='0.0.0.0', port=8080) 