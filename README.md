# ARWA - Academic Recovery AI

## Overview

ARWA is an AI-powered academic recovery system that helps students identify risks and get personalized recommendations for improving their academic performance.

## Features

- **AI Analysis Pipeline**: Advanced reasoning engine for academic risk prediction
- **Backend API**: FastAPI server with 7 endpoints for analysis
- **Frontend UI**: Next.js application with React components
- **Real-time Communication**: WebSocket and HTTP APIs
- **Comprehensive Reports**: Executive summaries with actionable insights

## Architecture

The application follows a layered architecture:

```
Frontend (Next.js)
  ↓
API Layer (FastAPI)
  ↓
Business Logic
  ↓
AI Service (13-stage pipeline)
  ↓
Data Layer
```

## Components

### Backend

- **main.py**: FastAPI application entry point with CORS middleware
- **api/routes.py**: API endpoints including /analyze, /health, /
- **api/controller.py**: RecoveryController orchestrates analysis
- **agent/recovery_orchestrator.py**: Master AI pipeline with 13 stages
- **models/api_models.py**: Pydantic request/response schemas

### Frontend

- **app/analyze/page.tsx**: Main analysis form component
- **hooks/useAnalysis.ts**: useAnalysis hook for API state management
- **lib/api.ts**: ApiClient class for HTTP requests
- **lib/types.ts**: TypeScript interfaces for all data types

## Installation and Running

### Backend

```bash
cd backend
../.venv/bin/python3 -m pip install fastapi uvicorn
../.venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### GET / (Home)
Returns basic API information.

### GET /health
Returns health status and agent information.

### POST /analyze
Analyzes student academic data.

**Request Body**:
```json
{
    "current_grade": 85.0,
    "stress_level": 5,
    "available_time": 4.0,
    "assignments": [
        {
            "title": "Math Homework",
            "course": "Math",
            "difficulty": 0.7,
            "estimated_hours": 3,
            "days_remaining": 2,
            "completed": false
        }
    ]
}
```

**Response**:
```json
{
    "report": {...},
    "features": {...},
    "academic_prediction": {...},
    "burnout_prediction": {...},
    "state": {...},
    "decisions": [...],
    "plan": {...},
    "simulations": [...],
    "strategies": [...],
    "best_strategy": null,
    "recovery_score": {...},
    "forecast": {...},
    "reasoning": [...],
    "explanations": [...],
    "reflection": [...]
}
```

### GET /analyses
Returns a lightweight summary of the authenticated user's analyses, newest first. Requires a `Bearer` JWT.

**Response**:
```json
[
    {
        "analysis_id": "uuid",
        "created_at": "2026-08-14T12:00:00Z",
        "academic_risk": 39,
        "academic_risk_level": "MODERATE",
        "burnout_risk": 47,
        "burnout_risk_level": "HIGH",
        "recovery_score": 33
    }
]
```

### GET /analyses/{analysis_id}
Returns the complete persisted analysis for the authenticated user. Requires a `Bearer` JWT. Requests for another user's analysis return 404 (RLS-enforced).

**Response**:
```json
{
    "analysis": {...},
    "analysis_assignments": [...],
    "risk_factors": [...],
    "priorities": [...],
    "recommendations": [...],
    "recovery_plan_days": [...],
    "recovery_plan_tasks": [...],
    "explanations": [...]
}
```

### GET /assignments, POST /assignments, PUT /assignments/{id}, DELETE /assignments/{id}
Persistent assignment CRUD, scoped to the authenticated user via RLS.

## AI Pipeline

The AI analysis pipeline consists of 13 stages:

1. **Feature Extraction**: Extract relevant features from student data
2. **Academic Risk Prediction**: Predict academic risk using ML models
3. **Burnout Risk Prediction**: Predict burnout risk using ML models
4. **State Building**: Build internal state representation
5. **Decision Engine**: Generate optimal decisions
6. **Planner**: Create recovery plan
7. **Simulation Engine**: Simulate different strategies
8. **Strategy Comparison**: Compare and rank strategies
9. **Recovery Score Calculation**: Calculate current and projected scores
10. **Recovery Forecast**: Forecast future recovery trajectory
11. **AI Report Generation**: Generate comprehensive report
12. **Explainability**: Generate human-understandable explanations
13. **Reflection**: Reflect on outcomes and learn

## Testing

The application includes comprehensive tests for all components. To run tests:

```bash
cd backend
python3 -m pytest tests/ -v
```

## Docker

To run with Docker:

```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License

## Contact

For questions or support, please contact the development team.
