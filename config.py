import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Neon DB Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Redis Configuration (for Celery)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Personality Analysis Settings
    MBTI_CONFIDENCE_THRESHOLD = 0.7
    MIN_SESSIONS_FOR_ANALYSIS = 3
    MAX_TRANSCRIPT_LENGTH = 50000
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_SESSIONS_PER_USER = 1000 