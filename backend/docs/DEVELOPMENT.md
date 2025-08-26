# WeatherAI Backend Development Guide

## Clean Architecture Implementation

This backend follows **Clean Architecture** principles with strict layer separation completed in Phase 3c.

### Layer Responsibilities

#### Domain Layer (`app/domain/`)
- **Purpose**: Pure business logic and domain rules
- **Contains**: Entities, value objects, domain events, domain exceptions
- **Dependencies**: None (no external dependencies allowed)
- **Guidelines**:
  - Domain entities should contain business logic only
  - Use value objects for complex data types (email, coordinates, etc.)
  - Define domain events for important business events
  - Create specific domain exceptions (not generic exceptions)

#### Application Layer (`app/application/`)
- **Purpose**: Orchestrate domain and infrastructure
- **Contains**: Use cases, interfaces, application services
- **Dependencies**: Domain layer only (infrastructure via interfaces)
- **Guidelines**:
  - Each use case should represent a single business operation
  - Use cases coordinate between domain and infrastructure
  - Publish domain events from use cases
  - Handle transaction boundaries (Unit of Work pattern)

#### Infrastructure Layer (`app/infrastructure/`)
- **Purpose**: External concerns and implementation details
- **Contains**: Repositories, database models, external APIs, AI clients
- **Dependencies**: Application interfaces, third-party libraries
- **Guidelines**:
  - Implement repository interfaces defined in application layer
  - Keep database models separate from domain entities
  - Wrap external services behind stable interfaces
  - Handle infrastructure-specific error handling

#### API Layer (`app/api/`)
- **Purpose**: HTTP request/response handling
- **Contains**: FastAPI routers, dependencies, DTOs
- **Dependencies**: Application use cases (not services directly)
- **Guidelines**:
  - Controllers should be thin adapters
  - Use dependency injection for use cases
  - Map HTTP errors from domain exceptions
  - Validate input using Pydantic schemas

#### Core Layer (`app/core/`)
- **Purpose**: Cross-cutting concerns
- **Contains**: Configuration, logging, metrics, utilities
- **Dependencies**: Minimal external dependencies
- **Guidelines**:
  - Centralize configuration management
  - Provide structured logging utilities
  - Implement observability patterns

#### Security Layer (`app/security/`)
- **Purpose**: Authentication, authorization, security concerns
- **Contains**: Auth services, rate limiting, security utilities
- **Dependencies**: Core layer, external auth providers
- **Guidelines**:
  - Centralize security policies
  - Implement defense in depth
  - Use secure defaults

### Development Workflow

#### Adding New Features

1. **Start with Domain**: Define entities, value objects, domain events
   ```python
   # app/domain/entities/forecast.py
   class WeatherForecast:
       def __init__(self, location: Location, temperature: Temperature):
           self.location = location
           self.temperature = temperature
           
       def is_extreme(self) -> bool:
           return self.temperature.is_extreme()
   ```

2. **Create Use Cases**: Implement business operations
   ```python
   # app/application/weather_use_cases.py
   class GetWeatherForecast:
       def __init__(self, weather_repo, location_repo, uow_factory):
           self.weather_repo = weather_repo
           self.location_repo = location_repo
           self.uow_factory = uow_factory
           
       async def execute(self, location_id: str) -> dict:
           async with self.uow_factory() as uow:
               location = await self.location_repo.get_by_id(location_id)
               forecast = await self.weather_repo.get_forecast(location)
               return {"forecast": forecast.to_dict()}
   ```

3. **Implement Infrastructure**: Create repositories, external adapters
   ```python
   # app/infrastructure/weather/openweather_client.py
   class OpenWeatherClient:
       async def get_forecast(self, location: Location) -> WeatherData:
           # External API implementation
           pass
   ```

4. **Add API Endpoints**: Create thin HTTP adapters
   ```python
   # app/api/v1/routes/weather.py
   @router.get("/forecast/{location_id}")
   async def get_forecast(
       location_id: str,
       use_case: GetWeatherForecast = Depends(get_weather_forecast_use_case)
   ):
       result = await use_case.execute(location_id)
       return ForecastResponse(**result)
   ```

5. **Add Dependency Injection**:
   ```python
   # app/api/dependencies.py
   async def get_weather_forecast_use_case(
       weather_repo: WeatherRepository = Depends(get_weather_repository)
   ) -> GetWeatherForecast:
       return GetWeatherForecast(weather_repo, location_repo, get_uow)
   ```

#### Testing Strategy

- **Unit Tests**: Test domain logic and use cases in isolation
- **Integration Tests**: Test full flows with real dependencies
- **API Tests**: Test HTTP endpoints with test client

#### Code Review Checklist

- [ ] Domain layer has no infrastructure dependencies
- [ ] API endpoints use use cases (not services directly)
- [ ] Use cases coordinate domain and infrastructure properly
- [ ] Repositories implement interfaces from application layer
- [ ] Error handling uses domain exceptions
- [ ] Dependency injection is properly configured
- [ ] Tests cover new functionality
- [ ] Documentation is updated

### Common Patterns

#### Repository Pattern
```python
# app/application/interfaces/repositories.py
class WeatherRepository(ABC):
    @abstractmethod
    async def get_forecast(self, location: Location) -> WeatherForecast:
        pass

# app/infrastructure/weather/repositories.py
class SqlWeatherRepository(WeatherRepository):
    async def get_forecast(self, location: Location) -> WeatherForecast:
        # Implementation
        pass
```

#### Unit of Work Pattern
```python
async def execute(self, command):
    async with self.uow_factory() as uow:
        entity = await uow.repository.get(command.id)
        entity.perform_business_operation(command.data)
        await uow.repository.save(entity)
        # Automatic commit/rollback handled by UoW context manager
```

#### Domain Events
```python
# In use case
event = DocumentIngestedEvent(document_id=doc.id, user_id=user_id)
self.event_bus.publish(event)

# Event handler (separate use case or infrastructure)
async def handle_document_ingested(event: DocumentIngestedEvent):
    # Process the event
    pass
```

### Architecture Decision Records (ADR)

See `docs/decisions/` for detailed architectural decisions and rationale.

### Performance Considerations

- Use async/await for I/O operations
- Implement caching at infrastructure layer
- Use connection pooling for database
- Monitor performance with structured metrics

### Observability

- Use structured logging with consistent fields
- Emit metrics for business operations
- Trace requests across layers
- Monitor error rates and latencies