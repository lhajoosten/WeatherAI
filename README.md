# WeatherAI

An AI-powered weather application that blends authoritative weather data with natural-language intelligence.

## Architecture Overview

WeatherAI is a full-stack application built with:

- **Backend**: FastAPI (Python) with async SQLAlchemy + pyodbc for MSSQL
- **Frontend**: React (TypeScript) + Vite for fast development
- **Database**: Microsoft SQL Server for relational data
- **Cache**: Redis for caching and rate limiting
- **LLM**: OpenAI GPT-4 integration with mock fallback
- **Containerization**: Docker Compose for development environment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Running the Application

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lhajoosten/WeatherAI.git
   cd WeatherAI
   ```

2. **Set up environment variables**:
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   
   # Frontend  
   cp frontend/.env.example frontend/.env
   ```

3. **Configure secrets** (Important!):
   Edit `backend/.env` and change:
   - `JWT_SECRET` to a secure random string
   - `DB_PASSWORD` if desired (must match docker-compose.yml)
   - `OPENAI_API_KEY` to your OpenAI key (optional - will use mock responses if not provided)

4. **Start all services**:
   ```bash
   docker compose up --build
   ```

5. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Use

1. Register a new account via the web interface
2. Add a location with latitude/longitude coordinates
3. Click "Explain Weather" to see AI-generated weather insights
4. View token usage and model information in the response

## Project Structure

```
WeatherAI/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/routes/   # API endpoints
│   │   ├── core/            # Configuration
│   │   ├── db/              # Database models & repositories
│   │   ├── schemas/         # Pydantic DTOs
│   │   ├── services/        # Business logic & LLM client
│   │   └── tests/           # Unit tests
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts (auth)
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
├── docs/                    # Documentation
│   ├── PROJECT_CASE.md      # Full project specification
│   ├── COPILOT_GUIDELINES.md # Development guidelines
│   └── PROMPTS.md           # LLM prompt templates
├── docker-compose.yml       # Development environment
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user

### Locations
- `GET /api/v1/locations` - List user's locations  
- `POST /api/v1/locations` - Add new location
- `POST /api/v1/locations/{id}/explain` - Generate AI weather explanation

### Health
- `GET /api/health` - Health check endpoint

## Features

### Current (MVP)
- ✅ User registration and JWT authentication
- ✅ Location management (add, list)
- ✅ AI weather explanations with structured output
- ✅ LLM audit logging (tokens, cost tracking)
- ✅ Rate limiting (in-memory)
- ✅ Mock weather data and LLM responses
- ✅ MSSQL database with async SQLAlchemy
- ✅ Docker containerized development environment
- ✅ TypeScript frontend with React

### Security Features
- JWT token authentication
- Password hashing with bcrypt
- Rate limiting on API endpoints
- CORS configuration
- Input validation and sanitization
- No PII stored in LLM audit logs (prompt truncation)

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Lint and format
ruff check .
black .
mypy .

# Run development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Lint and format
npm run lint
```

### Database

The application uses automatic table creation via SQLAlchemy on startup. This includes:

- Users (authentication and profile)
- Locations (user's saved locations) 
- ForecastCache (cached weather data)
- LLMAudit (LLM usage tracking)

**TODO**: Replace with Alembic migrations for production.

## Configuration

### Environment Variables

See `.env.example` files for all available configuration options.

**Critical settings to change for production:**
- `JWT_SECRET`: Use a cryptographically secure random string
- `DB_PASSWORD`: Strong database password
- `OPENAI_API_KEY`: Your OpenAI API key
- `CORS_ORIGINS`: Restrict to your domain(s)

### LLM Configuration

The application supports both real OpenAI integration and mock responses:

- **With OpenAI key**: Uses real GPT-4 API calls
- **Without OpenAI key**: Uses deterministic mock responses for demo

All LLM calls are logged to the LLMAudit table with:
- Token usage (input/output)
- Model name and version
- Truncated prompt summary (no PII)
- Cost tracking (placeholder for future implementation)

## Next Suggested Issues

Priority order for continued development:

### Week 2 - Core Weather Integration
- [ ] Add Alembic migrations & remove create_all
- [ ] Implement real weather provider (Open-Meteo or NOAA) 
- [ ] Background scheduler (APScheduler) to refresh ForecastCache
- [ ] Weather data caching strategy with expiration

### Week 3 - Enhanced Infrastructure  
- [ ] Enhanced rate limiting using Redis (sliding window + per-endpoint)
- [ ] Cost calculation (model pricing map) in LLMAudit
- [ ] JWT refresh tokens + revoke handling
- [ ] Structured logging (JSON) + request correlation IDs

### Week 4 - API & Testing Improvements
- [ ] Add OpenAPI tags & examples + error model (RFC7807 style)
- [ ] Add integration & repository tests (TestContainers for MSSQL)
- [ ] Frontend: improve UI state management (React Query) & error boundaries
- [ ] Add user preferences & personalized action items

### Week 5 - Chat & Advanced Features
- [ ] Implement /query (chat) endpoint + session history
- [ ] Add security headers & stricter CORS
- [ ] CI: GitHub Actions workflow (lint, mypy, pytest, frontend build)
- [ ] Performance optimizations and caching

## Security Notes

⚠️ **Important Security Considerations:**

1. **Change default secrets**: The provided JWT secret and DB password are for development only
2. **OpenAI API key**: Store securely, never commit to version control
3. **Rate limiting**: Current implementation is in-memory only; use Redis for production
4. **CORS**: Currently open for development; restrict for production
5. **HTTPS**: Always use HTTPS in production
6. **Data privacy**: Prompts are truncated before storage; implement encryption for sensitive data

## Contributing

1. Follow the coding standards in `docs/COPILOT_GUIDELINES.md`
2. Add tests for new functionality
3. Update documentation for API changes
4. Use the provided PR template
5. Keep changes focused and atomic

## Troubleshooting

### Common Issues

**SQL Server connection fails:**
- Ensure Docker has enough memory allocated (4GB+ recommended)
- Check that port 1433 is not in use by another service
- Verify the SA password meets SQL Server complexity requirements

**Frontend can't reach backend:**
- Check `VITE_API_URL` in frontend/.env
- Ensure backend is running on port 8000
- Verify CORS settings in backend configuration

**OpenAI API errors:**
- Ensure `OPENAI_API_KEY` is correctly set
- Check API quota and billing status
- Application will fall back to mock responses if API fails

### Logs

View application logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

## License

MIT License - see LICENSE file for details.
