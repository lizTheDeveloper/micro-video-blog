# Micro Video Blog Platform

A micro-video blog platform for sharing 5-second video content with social features and personalized recommendations.

## Phase 1: Foundation & User Authentication ✅

### Features Implemented
- ✅ User registration with email validation
- ✅ User login with JWT token authentication
- ✅ User profile management
- ✅ Password reset endpoints (basic structure)
- ✅ React frontend with authentication UI
- ✅ PostgreSQL database with user schema
- ✅ Redis integration for session management
- ✅ Comprehensive test suite

### Tech Stack
- **Backend**: FastAPI, Python 3.11, SQLAlchemy, Alembic
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Database**: PostgreSQL 14+
- **Cache**: Redis
- **Authentication**: JWT tokens with bcrypt password hashing

### Getting Started

#### Backend Setup
```bash
cd backend
source ../env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Database Setup
```bash
# Create database (if not exists)
createdb microvideoblog

# Run migrations
cd backend
alembic upgrade head
```

### API Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user profile
- `POST /auth/request-password-reset` - Request password reset
- `POST /auth/reset-password` - Reset password

### Next Steps
Phase 2 will implement core video upload and processing functionality.

## Development Status

- [x] Phase 1: Foundation & User Authentication
- [ ] Phase 2: Core Video Upload & Processing
- [ ] Phase 3: Video Playback & Streaming
- [ ] Phase 4: Basic Content Discovery & Feed
- [ ] Phase 5: Social Features - Likes & Comments
- [ ] Phase 6: Follow System & Personalized Feeds
- [ ] Phase 7: Content Moderation & Safety
- [ ] Phase 8: Basic Recommendation System
- [ ] Phase 9: Advanced Search & Discovery
- [ ] Phase 10: Performance Optimization & Scaling
- [ ] Phase 11: Analytics & Creator Insights
- [ ] Phase 12: Internationalization & Accessibility
- [ ] Phase 13: Advanced ML Recommendations
- [ ] Phase 14: Global Scaling & Final Optimization
