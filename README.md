# AI Personality Backend

🧠 **Advanced AI Personality Analysis System** for voice-first conversational AI companions.

This backend system analyzes conversation transcripts to build detailed MBTI personality profiles using Bayesian inference, OpenAI GPT-4, and advanced sentiment analysis. It's designed to power voice-first AI companion apps that need to understand and remember user personalities across conversations.

## 🌟 Key Features

- **Real-time Personality Analysis**: MBTI personality profiling using Bayesian inference
- **Session Management**: Automatic session tracking and transcript processing
- **Sentiment Analysis**: Advanced emotion and sentiment detection
- **Conversational Memory**: Context-aware memory for empathetic AI responses
- **PostgreSQL Integration**: Seamless integration with PostgreSQL/Neon DB for transcript storage
- **Background Processing**: Async task processing with Celery and Redis
- **RESTful API**: Complete API for mobile app integration

## 🏗️ Architecture

This system follows the detailed roadmap from your specification, implementing:

- **Phase 1**: Session Infrastructure with automatic session creation
- **Phase 2**: Post-Session Analytics with OpenAI-powered summaries
- **Phase 3**: Personality Engine with Bayesian MBTI analysis
- **Phase 4**: Conversational Memory for empathetic AI responses
- **Backend APIs**: Complete REST API for mobile app consumption

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env_example.txt` to `.env` and configure:

```bash
# Neon DB Configuration (Required)
DATABASE_URL=your_neon_db_connection_string_here

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Redis for background processing
REDIS_URL=redis://localhost:6379/0
```

> **Note**: Database tables are automatically created on startup - no additional database setup required!

### 3. Start the Backend

```bash
python api_docs_app.py
```

### 4. Test the Memory System

```bash
python test_memory_service.py
```

## 📡 API Endpoints

### Chat Conversation

#### AI Chat Response

```http
POST /chat
```

```json
{
  "text": "Hello! How are you doing today?",
  "is_voice": false,
  "user_id": "user-123",
  "conversation_context": [
    {
      "text": "Previous message",
      "isUser": true,
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ]
}
```

Response:

```json
{
  "response": "Hello! I'm doing well, thank you for asking. How are you doing today?",
  "success": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "model": "gpt-3.5-turbo",
  "tokens_used": 25
}
```

### Session Management

#### Process Single Session

```http
POST /sessions/process
```

```json
{
  "user_id": "user-123",
  "session_id": "session-456",
  "transcript": [
    {
      "speaker": "User",
      "content": "I love planning ahead and organizing my day...",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### Batch Process Sessions

```http
POST /sessions/batch-process
```

```json
{
  "user_id": "user-123",
  "limit": 50
}
```

### Personality Insights

#### Get Complete Personality Profile

```http
GET /personality/{user_id}
```

Response includes:

- MBTI type and description
- Confidence scores for all dimensions
- Facet bars for UI display
- Recent evidence and session history

#### Get MBTI Type Only

```http
GET /personality/{user_id}/type
```

#### Get Personality Facets

```http
GET /personality/{user_id}/facets
```

### Conversational Memory

#### Get Recent Memory Context

```http
GET /memory/recent/{user_id}?limit=10
```

Returns recent session summaries and personality insights for contextual AI responses.

### Analytics

#### Generate Summary

```http
POST /analytics/summary
```

```json
{
  "transcript": [...]
}
```

### AI Buddy Management

#### Get Available AI Buddies

```http
GET /ai-buddies
```

#### Get Specific AI Buddy Details

```http
GET /ai-buddies/{buddy_id}
```

#### Select Preferred AI Buddy

```http
POST /users/{user_id}/select-buddy
```

```json
{
  "buddy_id": "oliver"
}
```

#### Get User's Selected Buddy

```http
GET /users/{user_id}/selected-buddy
```

### User Management

#### Reset Personality Data

```http
POST /users/{user_id}/reset
```

## 🧮 Personality Analysis

### MBTI Dimensions

The system analyzes four core MBTI dimensions:

1. **Extroversion vs Introversion (E/I)**

   - Energy source and social interaction patterns
   - Communication style preferences

2. **Sensing vs Intuition (S/N)**

   - Information processing preferences
   - Detail vs big-picture focus

3. **Thinking vs Feeling (T/F)**

   - Decision-making approaches
   - Logic vs values-based choices

4. **Judging vs Perceiving (J/P)**
   - Structure and planning preferences
   - Flexibility vs organization

### Bayesian Inference

The system uses Bayesian inference to continuously update personality scores:

- **Prior Knowledge**: Previous personality assessment
- **New Evidence**: Latest conversation analysis
- **Posterior Update**: Refined personality scores
- **Confidence Tracking**: Reliability measures for each dimension

### Evidence Collection

Each conversation is analyzed for personality indicators:

- Direct statements about preferences
- Communication patterns and style
- Decision-making approaches
- Emotional expressions and responses

## 🗃️ Database Schema

> **Managed by PostgreSQL/Neon DB** - These tables are automatically created and managed on startup.

### Users Table

- `id`: Unique user identifier
- `device_id`: Optional device linking
- `created_at`, `updated_at`: Timestamps
- `last_active`: Last activity timestamp

### Sessions Table

- `id`: Session identifier
- `user_id`: Foreign key to users
- `transcript`: JSON array of messages
- `topic_summary`: AI-generated summary
- `sentiment_summary`: Emotion analysis results
- `created_at`, `ended_at`: Session timing

### PersonalityProfiles Table

- `user_id`: One-to-one with users
- `extroversion_score`, `sensing_score`, `thinking_score`, `judging_score`: MBTI scores (0.0-1.0)
- `*_confidence`: Confidence levels for each dimension
- `evidence_log`: JSON array of evidence entries
- `sessions_analyzed`: Number of sessions processed

## 🔄 Background Processing

For high-volume applications, use Celery for background processing:

### Start Redis (if not already running)

```bash
redis-server
```

### Start Celery Worker

```bash
celery -A tasks worker --loglevel=info
```

### Queue Background Tasks

```python
from tasks import process_session_async
result = process_session_async.delay(user_id, session_id, transcript)
```

## 📱 Mobile App Integration

### Typical Integration Flow

1. **Session End**: Mobile app sends transcript to `/api/sessions/process`
2. **Personality Update**: Backend analyzes and updates user profile
3. **UI Refresh**: App fetches updated insights from `/api/personality/{user_id}`
4. **Conversational Context**: AI fetches memory from `/api/memory/{user_id}/recent`

### Example iOS/React Native Usage

```javascript
// Process completed session
const processSession = async (userId, transcript) => {
  const response = await fetch(`${API_BASE}/api/sessions/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: generateSessionId(),
      transcript: transcript,
    }),
  });
  return response.json();
};

// Get personality insights for UI
const getPersonalityInsights = async (userId) => {
  const response = await fetch(`${API_BASE}/api/personality/${userId}`);
  return response.json();
};
```

## 🔒 Security & Privacy

- **PostgreSQL Security**: Personality data secured by proper database constraints and foreign keys
- **API Keys**: Secure environment variable configuration
- **Data Reset**: Built-in user data reset functionality
- **Privacy-First**: No PII logging, secure cloud storage with Neon DB
- **Encrypted Transit**: All API communication over HTTPS

## 🔧 Configuration

### Personality Analysis Settings

```python
# config.py
MBTI_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for type determination
MIN_SESSIONS_FOR_ANALYSIS = 3    # Sessions needed before analysis
MAX_TRANSCRIPT_LENGTH = 50000    # Character limit per session
```

### Session Management

```python
SESSION_TIMEOUT_MINUTES = 30     # Auto-end session timeout
MAX_SESSIONS_PER_USER = 1000     # Storage limit per user
```

## 📊 Example Personality Analysis

Input conversation about planning and decision-making:

```json
{
  "mbti_type": "ENTJ",
  "type_description": "The Commander - Natural-born leaders, strategic and decisive",
  "scores": {
    "extroversion": 0.75,
    "sensing": 0.45,
    "thinking": 0.82,
    "judging": 0.79
  },
  "confidence": {
    "overall": 0.73,
    "extroversion": 0.68,
    "thinking": 0.85
  },
  "facet_bars": [
    {
      "name": "Extroversion",
      "score": 0.75,
      "confidence": 0.68,
      "label": "E"
    }
  ]
}
```

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check API key and billing status
2. **Database Connection**: Verify DATABASE_URL in your `.env` file
3. **Chat Endpoint**: Ensure OpenAI API key is configured for `/api/chat`
4. **Memory Issues**: Large transcripts may need chunking

### Debug Mode

```bash
export FLASK_DEBUG=1
python app.py
```

### Logging

Check logs for detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Roadmap

Following your original specification:

- ✅ **Phase 1-3**: Core personality engine implemented
- ✅ **Phase 4**: Conversational memory system
- 🔄 **Phase 5**: Mobile UI components (your app)
- 📋 **Phase 6**: Enhanced security features
- 📋 **Phase 7**: QA and testing framework
- 📋 **Phase 8**: Production deployment & metrics

## 🤝 Contributing

This backend is designed to work with your voice-first AI companion app. The API is stable and ready for integration with your React Native/iOS frontend.

## 📄 License

This project is part of your AI companion app development.

---

**Ready to build personality-aware AI that truly understands your users!** 🧠✨
