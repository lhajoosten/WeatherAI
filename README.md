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
│   │   ├── analytics/        # Analytics platform (Phase 1)
│   │   │   ├── repositories/ # Data access layer
│   │   │   └── services/     # Business logic
│   │   ├── api/v1/routes/   # API endpoints
│   │   ├── core/            # Configuration
│   │   ├── db/              # Database models & repositories
│   │   ├── schemas/         # Pydantic DTOs
│   │   ├── services/        # Business logic & LLM client
│   │   ├── workers/         # Background job scheduler
│   │   └── tests/           # Unit tests
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   └── charts/      # Chart components (Recharts)
│   │   ├── contexts/        # React contexts (auth)
│   │   ├── context/         # Location context
│   │   ├── hooks/           # React Query hooks
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
├── docs/                    # Documentation
│   ├── ANALYTICS_DATA_MODEL.md # Analytics schema documentation
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

### Analytics (Phase 1)
- `GET /api/v1/analytics/observations` - Hourly weather observations
- `GET /api/v1/analytics/aggregations/daily` - Daily weather summaries
- `GET /api/v1/analytics/trends` - Trend analysis (7d, 30d periods)
- `GET /api/v1/analytics/accuracy` - Forecast accuracy metrics
- `POST /api/v1/analytics/summary` - AI-powered analytics summary

### Data Ingestion (New)
- `GET /api/v1/air-quality` - Air quality and pollen data  
- `GET /api/v1/astronomy/daily` - Daily astronomy data (sunrise, sunset, moon phase)
- `GET /api/v1/ingest/runs` - Ingestion run status and monitoring

### Health
- `GET /api/health` - Health check endpoint

## Analytics Platform

WeatherAI includes a comprehensive analytics platform for weather data analysis, trends, and forecast accuracy assessment.

### Architecture

The analytics system follows a layered architecture with normalized data models:

- **Data Models**: Separate tables for observations, forecasts, daily aggregates, accuracy metrics, and trend cache
- **Services**: Modular services for ingestion, aggregation, accuracy computation, and trend analysis
- **Background Jobs**: Automated data processing with lightweight async scheduler
- **API Layer**: RESTful endpoints with validation, rate limiting, and audit logging
- **Frontend**: Interactive dashboard with charts, trend cards, and AI-powered summaries

### Key Features

#### ✅ Phase 1 (Current Implementation)
- **Multi-Provider Data Ingestion**: Real weather data from OpenMeteo API, optional METAR observations, air quality and pollen data
- **Astronomical Computations**: Local sunrise/sunset, moon phase, and twilight calculations using astral library
- **Provider Orchestration**: Coordinated ingestion with status tracking, error handling, and configurable scheduling
- **Daily Aggregations**: Computed min/max/avg temperatures, precipitation totals, degree days
- **Trend Analysis**: Rolling comparisons with delta and percentage change calculations
- **Forecast Accuracy**: Error metrics comparing predictions vs observations
- **Interactive Dashboard**: React-based UI with charts (Recharts) and responsive design
- **AI Analytics Summary**: LLM-powered insights with structured prompts and guardrails
- **Background Processing**: Automated data computation with configurable schedules
- **Query Auditing**: Performance tracking and usage analytics

#### 🔄 Future Phases (Roadmap)
- **Enhanced Data Sources**: Radar tiles, lightning data, marine conditions
- **Advanced Analytics**: Anomaly detection, predictive modeling, bias correction
- **Ensemble Forecasting**: Multi-provider forecast combination and uncertainty quantification
- **Personalization**: User preferences, custom risk indices, location-specific insights
- **Enhanced UI**: Export capabilities, custom query builder, multi-location comparisons
- **Performance**: Redis caching, materialized views, columnstore indexes, partitioning
- **Real-time**: Streaming data ingestion, live updates, push notifications

## Data Ingestion Layer

WeatherAI now includes a comprehensive multi-provider data ingestion system:

### Supported Data Sources
- **OpenMeteo API**: Free weather forecasts, observations, and air quality data
- **NOAA METAR**: Aviation weather observations (optional, config-enabled)
- **Astral Library**: Local astronomical computations (sunrise, sunset, moon phase)

### Data Types Collected
- **Forecast Data**: 3-day hourly temperature, precipitation probability, wind speed
- **Observation Data**: Historical temperature, wind, humidity, precipitation
- **Air Quality**: PM2.5, PM10, ozone, nitrogen dioxide, sulfur dioxide, pollen counts
- **Astronomy**: Daily sunrise/sunset times, moon phase, civil twilight, daylight duration

### Architecture Features
- **Provider Abstractions**: Extensible interfaces for adding new data sources
- **Orchestrated Ingestion**: Sequential task coordination with status tracking
- **Bulk Upsert Operations**: Efficient data deduplication and conflict resolution
- **Error Resilience**: Retry mechanisms, timeout handling, and structured error logging
- **Configurable Scheduling**: Adjustable ingestion intervals and location limits

See [docs/INGESTION_ARCHITECTURE.md](docs/INGESTION_ARCHITECTURE.md) for detailed architecture documentation.

### Data Model

The analytics platform uses a star-schema inspired design optimized for time-series analysis:

- **ObservationHourly**: Raw weather observations with source tracking
- **ForecastHourly**: Normalized forecast data with model attribution  
- **AggregationDaily**: Pre-computed daily summaries for performance
- **ForecastAccuracy**: Error metrics for model performance assessment
- **TrendCache**: Cached trend calculations for common periods/metrics
- **AnalyticsQueryAudit**: API usage and performance tracking

See `docs/ANALYTICS_DATA_MODEL.md` for detailed schema documentation.

### Dashboard Features

- **Location Selection**: Choose from saved locations with persistent selection
- **Date Range Controls**: 7-day and 30-day analysis periods
- **Interactive Charts**: Time-series visualization with Recharts library
- **Trend Cards**: Color-coded delta indicators with percentage changes
- **AI Insights**: On-demand analytics summaries with structured outputs
- **Dark/Light Mode**: Theme toggle with persistent preferences
- **Responsive Design**: Works on desktop and mobile devices

### LLM Integration

Analytics summaries use structured prompts to ensure factual, deterministic outputs:

- **Template**: `analytics_summary_v1` with strict JSON input format
- **Guardrails**: No user text in prompts, only computed metrics and trends
- **Sections**: Overview, Notable Changes, Accuracy Assessment, Actionable Recommendations
- **Fallback**: Mock narratives when OpenAI API key not available
- **Audit**: Token usage, cost tracking, and performance monitoring

### Getting Started with Analytics

1. **Add Locations**: Use the Locations page to add weather monitoring points
2. **View Dashboard**: Navigate to Analytics to see interactive charts and trends
3. **Generate Insights**: Click "Generate" in the AI Analytics Summary panel
4. **Explore Data**: Use period selectors and chart interactions to analyze patterns

### Development Notes

- **Mock Data**: Phase 1 generates realistic synthetic data for testing
- **Migrations**: Uses Alembic for database schema management
- **Testing**: Unit tests for services, integration tests for endpoints
- **Background Jobs**: Simple async scheduler (production should use Celery/APScheduler)
- **Rate Limiting**: Higher limits for analytics endpoints due to dashboard usage

## Features

## Features

### Current (MVP + Analytics Phase 1)
- ✅ User registration and JWT authentication
- ✅ Location management (add, list)
- ✅ AI weather explanations with structured output
- ✅ **Analytics Platform**: Interactive dashboard with charts and trends
- ✅ **Data Models**: Normalized analytics tables with proper indexing
- ✅ **Background Processing**: Automated data ingestion and aggregation
- ✅ **Trend Analysis**: Rolling comparisons with delta calculations
- ✅ **Forecast Accuracy**: Error metrics and performance tracking
- ✅ **AI Analytics Summary**: LLM-powered insights with guardrails
- ✅ **Modern Frontend**: React + Chakra UI + React Query + Recharts
- ✅ **Database Migrations**: Alembic-based schema management
- ✅ LLM audit logging (tokens, cost tracking)
- ✅ Rate limiting with analytics-specific limits
- ✅ Mock weather data and LLM responses
- ✅ MSSQL database with async SQLAlchemy
- ✅ Docker containerized development environment

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

**New Stabilization & Reliability Settings:**
- `SQLALCHEMY_ECHO`: Enable/disable SQL statement logging (default: false)
- `LOG_LEVEL`: Logging level - DEBUG/INFO/WARNING/ERROR (default: INFO)
- `DISABLE_INGEST_IN_DEV`: Skip ingestion cycles in development (default: true)
- `OPENMETEO_AIR_QUALITY_STRICT`: Treat air quality 404s as failures (default: false)

**Ingestion Configuration:**
- `INGEST_INTERVAL_MINUTES`: Minutes between ingestion cycles (default: 120)
- `MAX_LOCATIONS_PER_INGEST`: Maximum locations processed per cycle (default: 25)

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

**Docker build issues with SSL certificates:**
- This can occur in some CI/container environments
- For production deployment, ensure proper SSL certificate configuration
- The application code is complete and will work once dependencies are resolved

### Logs

View application logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Development Notes

The complete project scaffold includes:
- ✅ All backend code (FastAPI, SQLAlchemy, LLM integration)
- ✅ All frontend code (React, TypeScript, authentication)
- ✅ Database models and repositories
- ✅ API endpoints with proper validation
- ✅ Authentication and rate limiting
- ✅ Docker configuration files
- ✅ Comprehensive documentation

**Note:** The MSSQL ODBC driver installation in Docker may require adjustments based on the deployment environment. For immediate testing, you can:
1. Run the backend locally with `pip install -e .[dev]` and connect to a local SQL Server
2. Use the mock weather data and LLM responses that are built into the application
3. Modify the Dockerfile for your specific environment's SSL certificate requirements

## License

MIT License - see LICENSE file for details.
