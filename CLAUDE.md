# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Personality Backend system that analyzes conversation transcripts to build detailed MBTI personality profiles using Bayesian inference, OpenAI GPT-4, and advanced sentiment analysis. It's designed to power voice-first AI companion apps.

## Development Commands

### Start the Application
```bash
python api_docs_app.py
```
- Runs on http://localhost:8080
- API documentation at http://localhost:8080/scalar

### Testing
```bash
python test_memory_service.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
1. Copy `env_example.txt` to `.env`
2. Configure required environment variables:
   - `DATABASE_URL` (required) - Neon DB PostgreSQL connection string
   - `OPENAI_API_KEY` (required)
   - `REDIS_URL` (optional, defaults to localhost)

## Architecture Overview

### Core Services (services/ directory)
- **chat_service.py**: Handles AI chat responses with buddy personalities, OpenAI integration with custom HTTP client for proxy handling
- **personality_service.py**: MBTI personality analysis using Bayesian inference, processes conversation evidence
- **memory_service.py**: Conversational memory system with emotional insights and vector similarity search
- **summary_service.py**: AI-powered session summaries and sentiment analysis using OpenAI
- **database_service.py**: PostgreSQL/Neon DB integration layer for data persistence and session management

### API Structure
- **Main app**: `api_docs_app.py` - Flask app with comprehensive OpenAPI documentation
- **Configuration**: `config.py` - Centralized configuration with environment variables
- **Database**: PostgreSQL/Neon DB-based with automatic schema management

### Key Features
1. **Personality Analysis**: MBTI profiling with 4 dimensions (E/I, S/N, T/F, J/P) using Bayesian inference
2. **AI Buddies**: 6 distinct personalities (Oliver, Luna, Zara, Maya, Alex, Sam) with ElevenLabs voice integration
3. **Session Processing**: Automatic transcript analysis, sentiment scoring, and personality updates
4. **Memory System**: ChromaDB-based vector storage for conversational context and emotional insights

## Database Schema (PostgreSQL/Neon DB)

### Primary Tables
- **users**: User management with device linking and buddy selection
- **sessions**: Conversation transcripts with AI-generated summaries and sentiment analysis
- **personality_profiles**: MBTI scores, confidence levels, and evidence logs

### Database Setup
- Automatic table creation on startup via `database_service._ensure_tables()`
- Tables created with proper foreign key relationships and constraints
- JSONB support for complex data structures (transcripts, evidence logs, sentiment data)

## Important Implementation Details

### OpenAI Integration
- Custom HTTP client in chat_service.py handles proxy issues
- Graceful fallback mechanisms for API failures
- Supports multiple models (GPT-3.5-turbo, GPT-4)

### Personality Engine
- Bayesian inference for continuous learning from conversation patterns
- Evidence collection and confidence tracking per MBTI dimension
- Minimum session requirements before personality determination

### AI Buddy System
- Distinct personalities with ElevenLabs voice IDs
- Personality-specific response generation
- User preference persistence and buddy selection API

### Background Processing
- Optional Celery integration with Redis for async session processing
- Configurable via `tasks.py` (currently archived)

## Configuration Settings

### Personality Analysis
- `MBTI_CONFIDENCE_THRESHOLD = 0.7`: Minimum confidence for type determination
- `MIN_SESSIONS_FOR_ANALYSIS = 3`: Sessions needed before analysis
- `MAX_TRANSCRIPT_LENGTH = 50000`: Character limit per session

### Session Management
- `SESSION_TIMEOUT_MINUTES = 30`: Auto-end session timeout
- `MAX_SESSIONS_PER_USER = 1000`: Storage limit per user

## Development Guidelines

### Cursor Rules Integration
This project follows deep learning and AI development patterns with:
- PyTorch framework preference for ML tasks
- Transformers library for LLM integration
- Focus on technical accuracy and efficiency
- Object-oriented model architectures
- Proper error handling and logging

### API Development
- All endpoints documented with OpenAPI 3.0 specification
- Scalar dark mode documentation interface
- Comprehensive error handling with structured responses
- Bearer token authentication support

### Testing Approach
- Service-level testing with `test_memory_service.py`
- No specific test framework configured - check for pytest or unittest patterns when adding tests