# WeatherAI

An AI-powered weather application that blends authoritative weather data with natural-language intelligence.

## Architecture Overview

WeatherAI is a full-stack application built with:

- **Backend**: FastAPI (Python) with async SQLAlchemy + pyodbc for MSSQL
- **Frontend**: React (TypeScript) + Vite with Leaflet maps for fast development
- **Database**: Microsoft SQL Server for relational data with automated bootstrap
- **Cache**: Redis for distributed caching and sliding-window rate limiting
- **LLM**: OpenAI GPT-4 integration with defensive prompting and mock fallback
- **Analytics**: Comprehensive data pipeline with aggregations, trends, and accuracy metrics
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

## Development

### Backend Development Commands

The backend includes a Makefile with common development tasks:

```bash
cd backend

# Install dependencies and dev tools
make install

# Run all tests
make test

# Run specific test suites
make test-domain    # Domain layer tests
make test-app       # Application layer tests
make test-unit      # All unit tests

# Code quality
make lint          # Run ruff and mypy
make format        # Format code with black and ruff

# Start development server
make api          # Start FastAPI with hot reload

# Clean temporary files
make clean
```

### Architecture Guidelines

The backend follows a clean, layered architecture (Phase 3c):

- **Domain Layer** (`app/domain/`): Pure business logic, entities, value objects, domain events
- **Application Layer** (`app/application/`): Use cases orchestrating domain and infrastructure  
- **Infrastructure Layer** (`app/infrastructure/`): External concerns (database, AI, cache, HTTP clients)
- **API Layer** (`app/api/`): HTTP request/response handling only
- **Core Layer** (`app/core/`): Cross-cutting concerns (settings, logging, metrics)
- **Security Layer** (`app/security/`): Authentication, authorization, rate limiting

Key principles:
- Dependency direction: Outer layers depend on inner layers only
- Domain layer has no infrastructure dependencies
- Use domain events for decoupled communication
- Structured logging with consistent tags
- Type safety with mypy strict mode

## Using Local SQL Server

For development with a local SQL Server instance instead of the dockerized container:

### Setup Steps

1. **Configure environment variables** in `backend/.env`:
   ```bash
   # Point to your local SQL Server
   DB_SERVER=host.docker.internal  # or localhost if running backend locally
   DB_PORT=1433
   DB_NAME=WeatherAI
   DB_USER=sa  # or your SQL Server username
   DB_PASSWORD=YourPassword123
   
   # Optional: Skip database creation if managed externally
   SKIP_DB_BOOTSTRAP=false
   ```

2. **Ensure SQL Server accepts connections**:
   - Enable TCP/IP connections in SQL Server Configuration Manager
   - Configure SQL Server to allow remote connections
   - Ensure SQL Server Authentication mode allows your chosen credentials
   - Verify Windows Firewall allows connections on port 1433

3. **Update docker-compose.yml** to exclude SQL Server service:
   ```yaml
   # Comment out or remove the sqlserver service section
   # Or use profiles to conditionally start services
   ```

4. **Alternative: Use profiles** in docker-compose:
   ```bash
   # Start only backend, frontend, and redis (no sqlserver)
   docker compose --profile no-sqlserver up --build
   ```

### Network Connectivity

- **From Docker containers**: Use `host.docker.internal` as the DB_SERVER
- **From local Python**: Use `localhost` or `127.0.0.1` as the DB_SERVER
- **Authentication**: Ensure your SQL Server user has database creation permissions

### Database Bootstrap

The bootstrap system will automatically:
1. Connect to your local SQL Server instance
2. Create the WeatherAI database if it doesn't exist
3. Run Alembic migrations to set up the schema

If you prefer to manage the database manually, set `SKIP_DB_BOOTSTRAP=true`.

## Redis Integration

WeatherAI now includes Redis integration for improved performance and scalability:

### Features
- **Rate Limiting**: Redis-backed sliding window rate limiting with in-memory fallback
- **Caching**: Forecast and explanation result caching with TTL
- **Health Monitoring**: Real-time Redis connectivity checks
- **Graceful Degradation**: Automatic fallback to in-memory operations when Redis is unavailable

### Configuration
```bash
# Redis connection
REDIS_URL=redis://redis:6379  # or redis://localhost:6379 for local Redis

# Rate limiting backend
USE_REDIS_RATE_LIMIT=true  # false to use in-memory only

# Health endpoint will show actual Redis status
# Rate limiting will log backend type (redis/in-memory) in debug mode
```

### Rate Limiting Details
- **Sliding Window**: Uses Redis ZSETs for precise time-based rate limiting
- **Endpoint-Specific Limits**: 
  - Regular endpoints: 60 requests/minute
  - LLM endpoints (explain, chat): 10 requests/minute  
  - Analytics endpoints: 180 requests/minute (dashboard usage)
- **Fallback Behavior**: Seamlessly switches to in-memory limiting if Redis fails

## Key Features

### User Management & Personalization
- **Modern Authentication**: Responsive login/register forms with password strength validation
- **User Profiles**: Customizable display names, bios, avatars, and timezone settings
- **Theme Support**: Light/dark mode with system preference detection and persistence
- **Weather Preferences**: Configurable units (metric/imperial), display options for wind/precipitation/humidity
- **Profile Management**: Comprehensive user settings with security overview

### Weather Intelligence
- **AI-Powered Explanations**: Natural language weather insights using OpenAI GPT-4 with v2 structured prompts
- **Multiple Locations**: Save and manage multiple weather locations
- **Location Groups**: Organize locations into custom groups for easy access
- **Interactive Maps**: Real Leaflet-based maps with OpenStreetMap tiles, location markers, and selection

### Analytics & Insights
- **Historical Data**: Hourly observations and daily aggregations with automated computation
- **Trend Analysis**: 7-day and 30-day weather trend comparisons with percentage changes
- **Forecast Accuracy**: Track prediction accuracy over time for temperature, precipitation, wind, humidity
- **AI Summaries v2**: Enhanced structured insights with defensive truncation and anti-hallucination measures
- **Analytics Pipeline**: Complete data pipeline with daily aggregations, accuracy metrics, and trend caching

### Technical Features
- **Redis Integration**: Distributed caching and sliding-window rate limiting with memory fallback
- **Database Bootstrap**: Automated database creation with intelligent server/database status detection
- **Enhanced Health Checks**: Comprehensive status monitoring (database, Redis, migrations, git version)
- **Real-time Updates**: Live weather data integration with multi-layer caching
- **Responsive Design**: Mobile-first UI that works on all devices
- **Advanced Rate Limiting**: Redis ZSET sliding window with configurable limits and fallback
- **Audit Logging**: Complete LLM usage tracking with token counting and cost monitoring
- **Management Commands**: Typer CLI for analytics computation, data seeding, and system maintenance


## Project Structure

```
WeatherAI/
├── backend/                 # FastAPI Python backend (Phase 3c: Modular Architecture)
│   ├── app/
│   │   ├── api/              # HTTP layer - FastAPI routers and error handlers
│   │   ├── application/      # Use cases orchestrating domain + infrastructure
│   │   │   ├── event_bus.py  # Domain event system with in-memory bus
│   │   │   └── rag_use_cases.py # RAG query and document ingestion use cases
│   │   ├── domain/           # Pure business logic - entities, value objects, events
│   │   │   ├── events.py     # Domain events (DataIngestedEvent, RAGQueryAnsweredEvent)
│   │   │   ├── exceptions.py # Domain exception hierarchy (DomainError, ValidationError)
│   │   │   └── value_objects.py # Value objects (LocationId, Coordinates, Temperature)
│   │   ├── infrastructure/   # External concerns with dependency inversion
│   │   │   ├── db/          # Database repositories, models, Unit of Work pattern
│   │   │   ├── ai/          # LLM clients, embeddings, RAG pipeline adapters
│   │   │   ├── external/    # Weather APIs, external service clients
│   │   │   └── cache/       # Redis abstractions, cache patterns
│   │   ├── core/            # Cross-cutting concerns
│   │   │   ├── settings.py  # Centralized typed configuration sections
│   │   │   ├── logging.py   # Structured JSON logging with tags
│   │   │   └── metrics.py   # Observability metrics with timing decorators
│   │   ├── schemas/         # API request/response DTOs with domain mappers
│   │   ├── security/        # Authentication, authorization, rate limiting
│   │   ├── analytics/       # Analytics platform (existing)
│   │   ├── workers/         # Background job scheduler
│   │   └── tests/           # Layer-specific unit and integration tests
│   ├── alembic/             # Database migrations
│   ├── Makefile             # Development commands (test, lint, format, api)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   └── charts/      # Chart components (Recharts)
│   │   ├── contexts/        # React contexts (auth, theme)
│   │   ├── context/         # Location context
│   │   ├── features/        # Feature modules
│   │   │   └── user/        # User management module
│   │   │       ├── components/ # Profile, preferences, security
│   │   │       ├── hooks/   # React Query hooks
│   │   │       ├── pages/   # User management pages
│   │   │       ├── services/ # User API client
│   │   │       └── types/   # User-related types
│   │   ├── hooks/           # Shared React Query hooks
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

### User Management
- `GET /api/v1/user/me` - Get current user with profile and preferences
- `PATCH /api/v1/user/profile` - Update user profile information
- `PATCH /api/v1/user/preferences` - Update weather display preferences
- `POST /api/v1/user/avatar` - Upload user avatar

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
- `GET /api/health` - Enhanced health check with real service connectivity tests
  - Returns: `healthy` (all services connected) or `degraded` (some services unavailable)
  - Checks: Database connectivity, Redis connectivity, OpenAI configuration status

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

# Run migrations  
alembic upgrade head

# Seed synthetic data for development (optional)
python -m app.manage seed-data --days 7 --locations all

# Run tests
pytest

# Lint and format
ruff check .
black .
mypy .

# Run development server
uvicorn app.main:app --reload
```

#### Dev Seed Command

The seed command generates synthetic weather data for development and testing:

```bash
# Seed 7 days of data for all locations
python -m app.manage seed-data --days 7 --locations all

# Seed 14 days for specific locations  
python -m app.manage seed-data --days 14 --locations "1,2,3"

# Seed 3 days for all locations (minimal dataset)
python -m app.manage seed-data --days 3 --locations all
```

**Features:**
- Generates realistic synthetic observations and forecasts
- Idempotent - skips existing data for date ranges
- Creates hourly data with seasonal and daily temperature variations
- Includes precipitation, wind, humidity, and weather conditions
- Useful for populating analytics dashboards with realistic data

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

## Using Local SQL Server

When connecting to a local SQL Server instance instead of the Docker container:

### Configuration
```bash
# In backend/.env
DB_SERVER=host.docker.internal  # On Windows/Mac Docker Desktop
# OR
DB_SERVER=localhost             # If running backend outside Docker

# Skip automatic database creation if DB exists
SKIP_DB_BOOTSTRAP=true

# Adjust connection attempts for faster startup
DB_BOOTSTRAP_MAX_ATTEMPTS=5
DB_BOOTSTRAP_SLEEP_SECONDS=1
```

### Troubleshooting
- **Error 4060 (Database does not exist)**: Set `SKIP_DB_BOOTSTRAP=false` to auto-create
- **Error 226 (CREATE DATABASE inside transaction)**: Fixed by using autocommit in bootstrap
- **Connection timeouts**: Increase `DB_BOOTSTRAP_MAX_ATTEMPTS` and check firewall

## Redis Rate Limiting & Caching

WeatherAI uses Redis for distributed rate limiting and caching with intelligent fallback.

### Key Patterns
- **Rate Limiting**: `ratelimit:{user_id}:{endpoint}` (Redis ZSET with sliding window)
- **Analytics Cache**: `analytics:{hash}` (JSON-serialized results with TTL)
- **Forecast Cache**: `forecast:{hash}` (Weather data with 5-minute TTL)

### Configuration
```bash
# Enable/disable Redis features
USE_REDIS_RATE_LIMIT=true          # Use Redis for rate limiting
REDIS_CACHE_ANALYTICS_TTL=60       # Analytics cache TTL (seconds)
REDIS_CACHE_FORECAST_TTL=300       # Forecast cache TTL (seconds)
```

### Fallback Behavior
- **Rate Limiting**: Falls back to in-memory tracking if Redis unavailable
- **Caching**: Falls back to in-memory cache with shorter TTL
- **Health Status**: Reports Redis status but doesn't fail startup

## Analytics Pipeline

Comprehensive data pipeline for weather analytics with automated computation.

### Data Flow
1. **Observations/Forecasts** → Hourly data ingestion
2. **Daily Aggregations** → Min/max/avg temperatures, precipitation totals, degree days
3. **Accuracy Metrics** → Forecast vs observation comparisons
4. **Trend Analysis** → 7-day and 30-day rolling comparisons
5. **AI Summaries** → LLM-powered insights with structured prompts

### Management Commands
```bash
# Seed synthetic data for development
python -m app.manage seed-data --days 7 --locations all

# Compute daily aggregations (last 30 days)
python -m app.manage compute-aggregations --days 30

# Compute forecast accuracy (last 7 days)  
python -m app.manage compute-accuracy --days 7

# Compute trends (7d, 30d periods)
python -m app.manage compute-trends --periods "7d,30d"

# Run full analytics refresh (all computations)
python -m app.manage analytics-refresh

# Target specific location
python -m app.manage analytics-refresh --location-id 1
```

### Automation
- **Auto-refresh**: Seed data automatically triggers analytics refresh (unless `NO_REFRESH=true`)
- **Idempotent**: All commands can be run multiple times safely
- **Incremental**: Computations only process new/changed data

## Map Integration

Interactive maps powered by Leaflet with OpenStreetMap tiles.

### Features
- **Real Map Rendering**: Replaces coordinate grid with proper Leaflet implementation
- **Location Markers**: Clickable markers with popup information
- **Selection Handling**: Visual feedback for selected locations
- **Group Filtering**: Filter locations by custom groups
- **Mobile Responsive**: Touch-friendly interaction on mobile devices

### Adding Map Providers
To add additional map tile providers, modify `MapView.tsx`:

```typescript
// Example: Add satellite imagery
<TileLayer
  attribution='&copy; <a href="https://www.mapbox.com/">Mapbox</a>'
  url="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token={your_token}"
/>
```

### Troubleshooting
- **Blue stripes/missing tiles**: Ensure Leaflet CSS is imported in `main.tsx`
- **Marker icons missing**: Default icon fix is included in component
- **Map not rendering**: Check browser console for JavaScript errors

## Troubleshooting

### Common Errors

| Error | Description | Solution |
|-------|-------------|----------|
| Error 4060 | Database does not exist | Set `SKIP_DB_BOOTSTRAP=false` |
| Error 226 | CREATE DATABASE in transaction | Fixed by autocommit in bootstrap |
| Redis connection failed | Redis unavailable | Check Redis container, app continues with fallback |
| NO_DATA summary | Insufficient analytics data | Run `analytics-refresh` command |
| Map tiles missing | Leaflet CSS not loaded | Import CSS in `main.tsx` |

### Health Check Debugging
```bash
# Check application status
curl http://localhost:8000/api/health

# Response includes:
# - Database connection status
# - Redis connection status  
# - Migration version
# - Git commit hash
```

### Analytics Pipeline Debugging
```bash
# Check analytics cache stats
curl http://localhost:8000/api/v1/analytics/cache/stats

# View recent aggregations
curl http://localhost:8000/api/v1/analytics/aggregations/daily?days=7

# Test AI summary generation
curl -X POST http://localhost:8000/api/v1/analytics/summary \
  -H "Content-Type: application/json" \
  -d '{"location_id": 1}'
```

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

**Database bootstrap fails with SQL Server error 226:**
- This occurs when CREATE DATABASE is attempted within a transaction
- **Solution**: The new bootstrap system uses `pyodbc.connect(autocommit=True)` to avoid this issue
- Set `SKIP_DB_BOOTSTRAP=true` if using an externally managed database
- Check `DB_BOOTSTRAP_MAX_ATTEMPTS` and `DB_BOOTSTRAP_SLEEP_SECONDS` in configuration

**SQL Server connection fails:**
- Ensure Docker has enough memory allocated (4GB+ recommended)
- Check that port 1433 is not in use by another service
- Verify the SA password meets SQL Server complexity requirements

**Database connection errors (error 4060):**
- This happens when the WeatherAI database doesn't exist yet
- The bootstrap system now automatically creates the database before migrations
- For manual creation: Connect to master database and run `CREATE DATABASE [WeatherAI]`

**Redis connection issues:**
- Redis errors are handled gracefully with fallback to in-memory operations
- Rate limiting will use in-memory storage if Redis is unavailable
- Health endpoint will show `redis: disconnected` if Redis is down
- Set `USE_REDIS_RATE_LIMIT=false` to disable Redis rate limiting entirely

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
