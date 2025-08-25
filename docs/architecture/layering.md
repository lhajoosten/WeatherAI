# Backend Layering Architecture

This document describes the layered architecture implemented in Phase 3b of the WeatherAI backend refactor.

## Overview

The backend follows a clean, layered architecture that separates concerns and establishes clear dependency directions. This approach improves maintainability, testability, and supports future scaling requirements.

## Architecture Layers

### 1. Presentation Layer (`app/api/`)
- **Responsibility**: HTTP request/response handling, input validation, authentication
- **Components**: 
  - FastAPI routers (`app/api/v1/routes/`)
  - Dependency injection (`app/api/dependencies.py`)
  - Exception mapping to HTTP responses
- **Dependencies**: Services layer only
- **Key Principle**: Controllers should be thin adapters between HTTP and business logic

### 2. Services Layer (`app/services/`)
- **Responsibility**: Business logic orchestration, transaction management
- **Components**:
  - Domain services (e.g., `RAGService`, `AuthService`)
  - Workflow orchestration
  - Cross-repository operations
- **Dependencies**: Repositories, external services (pipelines, LLM clients)
- **Key Principle**: Services encapsulate business rules and coordinate between repositories

### 3. Repositories Layer (`app/repositories/`)
- **Responsibility**: Data access abstraction, persistence operations
- **Components**:
  - Domain-specific repositories (`RagDocumentRepository`)
  - Unit of Work pattern (`UnitOfWork`)
  - Database session management
- **Dependencies**: Database models, ORM
- **Key Principle**: Repositories abstract data storage implementation details

### 4. Domain Models Layer (`app/db/models/`)
- **Responsibility**: Data structure definitions, domain entities
- **Components**:
  - ORM models organized by domain (`core/`, `rag/`)
  - Separate declarative bases per schema
  - Database table definitions
- **Dependencies**: SQLAlchemy, database drivers
- **Key Principle**: Models represent domain concepts without business logic

### 5. External Integration Layer (`app/ai/`, `app/core/`)
- **Responsibility**: External service integration, infrastructure concerns
- **Components**:
  - RAG pipeline (`app/ai/rag/`)
  - Configuration (`app/core/config.py`)
  - Redis client, database connections
- **Dependencies**: External APIs, third-party libraries
- **Key Principle**: Isolate external dependencies behind stable interfaces

## Schema Organization

### Request/Response DTOs (`app/schemas/`)
DTOs are organized by domain with clear naming conventions:

```
app/schemas/
├── common/          # Shared schemas (errors, health)
├── user/           # User authentication and profile
├── location/       # Location and location groups  
├── rag/           # RAG system requests/responses
└── __init__.py    # Backward compatibility exports
```

**Naming Conventions**:
- `*Request` - Input schemas for API endpoints
- `*Response` - Output schemas for API endpoints  
- `*DTO` - Data transfer objects for internal use
- `*CreateRequest`, `*UpdateRequest` - Specific operation requests

## Dependency Direction

The architecture enforces strict dependency direction to prevent circular dependencies:

```
API Layer → Services Layer → Repositories Layer → Models Layer
     ↓           ↓               ↓                    ↓
   Schemas   Business Logic   Data Access        Domain Entities
```

**Key Rules**:
1. **No upward dependencies**: Lower layers cannot depend on higher layers
2. **Services orchestrate**: Business logic belongs in services, not controllers or repositories
3. **Repositories isolate**: Data access details are hidden behind repository interfaces
4. **Models are pure**: Domain models contain no business logic or external dependencies

## Exception Handling

### Exception Hierarchy
```python
AppError (base)
├── ValidationError (422)
├── NotFoundError (404)  
├── ConflictError (409)
├── RateLimitError (429)
└── ServiceUnavailableError (503)
```

### Central Exception Mapping
- **Location**: `app/core/exception_handlers.py`
- **Registration**: `app/main.py` via `register_exception_handlers()`
- **Strategy**: Domain exceptions map to appropriate HTTP status codes
- **Benefits**: Consistent error responses, reduced boilerplate in controllers

## Unit of Work Pattern

### Implementation
```python
# Usage in services
async with get_uow() as uow:
    repo = uow.get_repository(RagDocumentRepository)
    # ... perform operations
    # Automatic commit on success, rollback on exception
```

### Benefits
- **Transaction Management**: Automatic commit/rollback
- **Repository Coordination**: Multiple repositories share same session
- **Testing**: Easy to mock for unit tests
- **Consistency**: Ensures data consistency across operations

## Testing Strategy

### Test Organization
```
tests/
├── unit/           # Isolated unit tests with mocks
│   ├── test_unit_of_work.py
│   ├── test_rag_service.py
│   └── test_exception_handlers.py
└── integration/    # End-to-end tests with real dependencies
    ├── test_rag_integration.py
    └── test_rag_models.py
```

### Unit Tests
- **Scope**: Single component in isolation
- **Mocking**: All external dependencies mocked
- **Focus**: Business logic, error handling, edge cases

### Integration Tests
- **Scope**: Multiple components working together
- **Dependencies**: Real database, test containers
- **Focus**: Data flow, transaction behavior, API contracts

## Type Safety

### mypy Configuration
- **Strict mode enabled**: All new code must pass strict type checking
- **Gradual adoption**: Existing AI pipeline code has relaxed rules during transition
- **Interface enforcement**: Protocols used for external service abstractions

### Benefits
- **Early error detection**: Type mismatches caught at development time
- **Better IDE support**: Improved autocomplete and refactoring
- **Documentation**: Types serve as executable documentation

## Development Guidelines

### Adding New Features
1. **Start with schemas**: Define request/response DTOs
2. **Create domain models**: Add database tables if needed
3. **Build repositories**: Implement data access operations
4. **Implement services**: Add business logic and orchestration
5. **Add controllers**: Create thin API endpoints
6. **Write tests**: Unit tests for services, integration tests for flows

### Code Review Checklist
- [ ] Controllers only call services (no direct repository/pipeline usage)
- [ ] Services handle business logic and transaction management
- [ ] Repositories encapsulate all database operations
- [ ] Exception handling uses domain exceptions
- [ ] Type annotations are complete and accurate
- [ ] Tests cover new functionality

### Import Guidelines
```python
# Good: Domain-specific imports
from app.schemas.rag import IngestRequest, IngestResponse
from app.services.rag_service import RAGService
from app.repositories.rag import RagDocumentRepository

# Avoid: Cross-layer imports
from app.api.v1.routes.rag import router  # Controller importing from same layer
from app.db.models import RagDocument     # Service importing model directly
```

## Migration Notes

### Backward Compatibility
- **Schema exports**: Common schemas re-exported from `app.schemas` for compatibility
- **Repository shims**: Existing repositories available via `app.repositories` imports
- **Gradual migration**: Legacy patterns supported during transition period

### Future Improvements
- **Async throughout**: Full async/await adoption in all layers
- **Event sourcing**: Consider for audit trails and state management
- **CQRS patterns**: Separate read/write models for complex domains
- **Microservice preparation**: Clear service boundaries support future decomposition

## Related Documentation
- [ADR-001: Phase 1 Backend Directory Structure](../decisions/2025-08-25-phase1-structure.md)
- [ADR-002: Multi-Schema Model Refactor](../decisions/2025-08-26-model-refactor.md)
- [Database Migrations Guide](../migrations.md)