# 🚀 SQLite to Supabase Migration Guide

This document outlines the complete migration from SQLite/SQLAlchemy to Supabase for the AI Personality Backend.

## 🏗️ What Was Changed

### 1. **Database Layer Migration**

- **Removed**: SQLAlchemy ORM and SQLite database
- **Added**: Direct Supabase client integration
- **Updated**: All database operations to use Supabase REST API

### 2. **Files Modified**

#### Services Layer

- **`services/supabase_service.py`**: Complete rewrite with full database functionality
- **`services/database_service.py`**: Simplified to use Supabase service
- **`services/personality_service.py`**: Updated to work with Supabase data structures

#### Configuration

- **`config.py`**: Removed `DATABASE_URL` SQLite configuration
- **`env_example.txt`**: Updated to reflect Supabase-only setup
- **`test_config.py`**: Switched to Supabase test configuration

#### Models

- **`models/database.py`**: Replaced SQLAlchemy models with schema documentation and utilities

#### Dependencies

- **`requirements.txt`**: Removed `sqlalchemy` and `psycopg2-binary`

#### Application

- **`api_docs_app.py`**: Updated personality endpoint to use async service calls

### 3. **Files Added**

- **`supabase_migration.sql`**: Database schema creation script for Supabase

### 4. **Files Removed**

- **`personality.db`**: SQLite database file

## 🛠️ Setup Instructions

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned
3. Navigate to Settings → API to get your credentials

### Step 2: Set Up Database Schema

1. Go to the SQL Editor in your Supabase dashboard
2. Copy and paste the contents of `supabase_migration.sql`
3. Run the script to create all required tables and indexes

### Step 3: Configure Environment Variables

Create a `.env` file with your Supabase credentials:

```env
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/0

# Security Keys (Change in production!)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test the Migration

```bash
python api_docs_app.py
```

The application should start without any SQLite/SQLAlchemy errors.

## 🏗️ Database Schema

### Tables Created

1. **`users`**: User records with device tracking
2. **`sessions`**: Chat sessions with AI analysis results
3. **`personality_profiles`**: MBTI personality profiles with confidence scores

### Key Features

- **Row Level Security (RLS)**: Enabled for data protection
- **Automatic Timestamps**: `created_at` and `updated_at` fields
- **JSONB Support**: For complex data like transcripts and evidence logs
- **Optimized Indexes**: For common query patterns
- **Foreign Key Constraints**: Maintaining data integrity

## 🔄 API Compatibility

All existing API endpoints remain unchanged:

- `GET /personality/{user_id}` - Now uses async Supabase queries
- `POST /sessions/process` - Saves to Supabase instead of SQLite
- `GET /sessions/{session_id}` - Retrieves from Supabase
- `GET /sessions/user/{user_id}` - Fetches user sessions from Supabase

## 🧠 Data Migration (If Needed)

If you have existing SQLite data to migrate:

1. **Export from SQLite**:

```sql
-- Export users
SELECT * FROM users;

-- Export sessions
SELECT * FROM sessions;

-- Export personality profiles
SELECT * FROM personality_profiles;
```

2. **Import to Supabase**:
   Use the Supabase dashboard or API to insert the exported data into the new tables.

## 🚀 Benefits of Supabase Migration

### Scalability

- **Cloud-native**: Automatically scales with usage
- **PostgreSQL**: More robust than SQLite for concurrent access
- **Connection pooling**: Better performance under load

### Features

- **Real-time subscriptions**: Can listen to database changes
- **Built-in authentication**: If needed for user management
- **Auto-generated APIs**: REST and GraphQL endpoints
- **Dashboard**: Visual database management

### Reliability

- **Backups**: Automatic database backups
- **Monitoring**: Built-in performance monitoring
- **High availability**: Cloud infrastructure reliability

## 🛡️ Security Considerations

### Row Level Security (RLS)

- Policies created to ensure users can only access their own data
- Adjust policies in `supabase_migration.sql` based on your auth setup

### API Keys

- Use environment variables for all sensitive credentials
- Never commit API keys to version control
- Use service key only for server-side operations

### Data Validation

- Client-side validation through Supabase client
- Server-side validation in Python services
- Database constraints for data integrity

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**:

   - Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
   - Check if your IP is whitelisted (if RLS policies are restrictive)

2. **Permission Errors**:

   - Review RLS policies in the Supabase dashboard
   - Ensure service key is used for admin operations

3. **Data Type Mismatches**:
   - JSONB fields expect valid JSON
   - Float fields should be numeric
   - Text fields handle strings properly

### Testing Connection

```python
from services.supabase_service import supabase_service

# Test basic connection
try:
    result = supabase_service.client.table('users').select('count').execute()
    print("✅ Supabase connection successful")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 🎯 Next Steps

1. **Monitor Performance**: Use Supabase dashboard to monitor query performance
2. **Optimize Queries**: Add indexes for any new query patterns
3. **Backup Strategy**: Configure automated backups if needed
4. **Authentication**: Consider integrating Supabase Auth if user authentication is required
5. **Real-time Features**: Explore real-time subscriptions for live updates

---

**Migration completed successfully! 🎉**

The application now uses Supabase as its primary database, providing better scalability, reliability, and features compared to the previous SQLite setup.
