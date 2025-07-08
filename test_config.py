"""Test configuration"""
import os

# Use Supabase for testing (requires test database setup)
SUPABASE_URL = os.getenv('TEST_SUPABASE_URL')
SUPABASE_KEY = os.getenv('TEST_SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('TEST_SUPABASE_SERVICE_KEY')

# OpenAI Configuration for testing
OPENAI_API_KEY = os.getenv('TEST_OPENAI_API_KEY')

# Redis Configuration for testing
REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')

# Security Keys for testing
SECRET_KEY = 'test-secret-key-do-not-use-in-production'
JWT_SECRET_KEY = 'test-jwt-secret-key-do-not-use-in-production'

# Personality Analysis Settings for testing
MBTI_CONFIDENCE_THRESHOLD = 0.5  # Lower threshold for testing
MIN_SESSIONS_FOR_ANALYSIS = 1    # Lower minimum for testing
MAX_TRANSCRIPT_LENGTH = 10000    # Smaller max for testing

# Session Settings for testing
SESSION_TIMEOUT_MINUTES = 5      # Shorter timeout for testing
MAX_SESSIONS_PER_USER = 100      # Lower limit for testing 