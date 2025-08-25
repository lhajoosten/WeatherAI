# ADR-003: Phase 3c Backend Modularization & Layer Consolidation

**Status:** In Progress  
**Date:** 2025-01-21  
**Authors:** WeatherAI Development Team  
**Supersedes:** [ADR-001: Phase 1 Backend Directory Structure](./2025-08-25-phase1-structure.md), [ADR-002: Multi-Schema Model Refactor](./2025-08-26-model-refactor.md)

## Context

Following successful completion of Phase 1 (directory normalization) and Phase 3/3b (multi-schema models, repository/service patterns, and Unit of Work), the WeatherAI backend requires a comprehensive modularization to establish clean architectural boundaries and prepare for upcoming enhancements including RAG analytics, observability, and advanced AI features.

### Current State

The existing architecture has established:
- ✅ Multi-schema database organization (`core`, `rag` schemas)
- ✅ Repository pattern with Unit of Work implementation
- ✅ DTO separation and typed schemas
- ✅ Exception hierarchy and centralized handling
- ✅ Basic service layer organization

### Challenges

- **Implicit Coupling**: Services directly import infrastructure components
- **Mixed Concerns**: Business logic scattered across multiple layers
- **Inconsistent Dependencies**: No clear dependency direction enforcement
- **Limited Observability**: Ad-hoc logging and no structured metrics
- **Security Distribution**: Auth and rate limiting spread across modules
- **Event Handling**: No domain event system for decoupled communication

## Decision

Implement a **full modular architecture** with strict layer separation and dependency inversion to establish a clean foundation for advanced features.

### New Architecture Layers

```
app/
├── api/              # FastAPI routers, HTTP concerns only
├── application/      # Use cases orchestrating domain + infrastructure  
├── domain/           # Entities, value objects, events, domain exceptions
├── infrastructure/   # External concerns (DB, AI, cache, HTTP clients)
│   ├── db/          # Database repositories, models, session management
│   ├── ai/          # LLM clients, embeddings, RAG pipeline adapters
│   ├── external/    # Weather APIs, external service clients
│   └── cache/       # Redis abstractions, cache patterns
├── core/            # Settings, logging, metrics, time utilities
├── schemas/         # API request/response DTOs with mappers
└── security/        # Authentication, authorization, rate limiting
```

### Key Architectural Principles

1. **Dependency Direction**: Outer layers depend on inner layers only
   - `api` → `application` → `domain`
   - `infrastructure` → `domain` (implements domain interfaces)
   - `core` has no dependencies (except external libraries)

2. **Domain Layer Purity**: Contains only business logic, no infrastructure
   - Domain entities and value objects
   - Domain events and business rules
   - Domain exceptions with clear semantics

3. **Application Layer Orchestration**: Use cases coordinate domain + infrastructure
   - Dependency injection of repository and service interfaces
   - Domain event publishing
   - Transaction boundary management

4. **Infrastructure Isolation**: All external concerns isolated behind interfaces
   - Database access only through repositories
   - External APIs through client interfaces
   - Cache operations through abstractions

## Implementation Strategy

### Phase 3c.1: Foundation Layer Creation ✅

- [x] Create new directory structure (`domain/`, `application/`, `infrastructure/`, `security/`)
- [x] Implement domain exception hierarchy in `domain/exceptions.py`
- [x] Create domain events system with in-memory event bus
- [x] Add domain value objects to reduce primitive obsession
- [x] Centralize settings in `core/settings.py` with typed sections
- [x] Implement structured JSON logging in `core/logging.py`
- [x] Create metrics interface with in-memory sink in `core/metrics.py`

### Phase 3c.2: Infrastructure Reorganization

- [ ] Move existing components to infrastructure layer:
  - [ ] Database repositories → `infrastructure/db/`
  - [ ] AI/RAG pipeline → `infrastructure/ai/`
  - [ ] Cache components → `infrastructure/cache/`
  - [ ] External weather clients → `infrastructure/external/`
- [ ] Create interface abstractions for infrastructure dependencies
- [ ] Implement Redis-based rate limiter in `security/`

### Phase 3c.3: Application Layer Implementation

- [ ] Convert existing services to use case classes
- [ ] Implement dependency injection patterns
- [ ] Add domain event publishing to use cases
- [ ] Create schema mappers for domain ↔ DTO conversion

### Phase 3c.4: API Layer Cleanup

- [ ] Ensure routers only handle HTTP concerns
- [ ] Replace direct service calls with use case calls
- [ ] Update error handlers to use new domain exceptions
- [ ] Add consistent input validation

### Phase 3c.5: Testing & Documentation

- [ ] Update all imports to new module structure
- [ ] Add layer-specific unit tests
- [ ] Create integration test for domain event flow
- [ ] Update README with new architecture tree
- [ ] Add development guidelines for each layer

## Benefits

### Technical Benefits

- **Clear Boundaries**: Each layer has well-defined responsibilities
- **Dependency Inversion**: Business logic doesn't depend on infrastructure
- **Testing Simplification**: Easy to mock dependencies at layer boundaries
- **Extensibility**: New features follow established patterns
- **Observability**: Centralized logging and metrics across all operations

### Development Benefits

- **Reduced Coupling**: Changes in one layer don't ripple through others
- **Team Coordination**: Clear ownership of different architectural concerns
- **Onboarding**: New developers can understand system structure quickly
- **Code Reviews**: Easier to enforce architectural guidelines

### Future Enablement

- **RAG Analytics**: Clean foundation for advanced analytics features
- **Microservices**: Clear service boundaries support future decomposition
- **Event Sourcing**: Domain events provide foundation for event sourcing
- **Performance Optimization**: Metrics and logging enable data-driven optimization

## Risks & Mitigation

### Migration Complexity

- **Risk**: Large refactor could introduce regressions
- **Mitigation**: Incremental migration with comprehensive testing at each step

### Import Changes

- **Risk**: Extensive import updates across codebase
- **Mitigation**: Preserve backward compatibility where possible, systematic update

### Learning Curve

- **Risk**: Team needs to learn new architectural patterns
- **Mitigation**: Clear documentation, code examples, and review guidelines

## Acceptance Criteria

- [ ] All tests pass with new import structure
- [ ] No direct infrastructure dependencies in domain or application layers
- [ ] Domain events can be published and handled
- [ ] Centralized error mapping works correctly
- [ ] Structured logging provides consistent format
- [ ] Settings are centralized and typed
- [ ] mypy passes with strict checking
- [ ] README reflects new architecture

## Related Documentation

- [ADR-001: Phase 1 Backend Directory Structure](./2025-08-25-phase1-structure.md)
- [ADR-002: Multi-Schema Model Refactor](./2025-08-26-model-refactor.md)
- [Backend Layering Architecture](../architecture/layering.md)
- [Copilot Development Guidelines](../../COPILOT_GUIDELINES.md)

## Consequences

### Positive

- ✅ **Clean Architecture**: Proper separation of concerns with dependency inversion
- ✅ **Scalability Foundation**: Architecture supports future growth and complexity
- ✅ **Testing Strategy**: Clear layer boundaries enable effective unit and integration testing
- ✅ **Developer Experience**: Consistent patterns and clear module responsibilities
- ✅ **Observability**: Structured logging and metrics enable operational insights

### Negative

- ⚠️ **Migration Effort**: Significant refactoring required for existing codebase
- ⚠️ **Complexity Increase**: More layers and abstractions to understand
- ⚠️ **Import Updates**: Extensive import path changes required

### Neutral

- 📝 **Backward Compatibility**: Maintained where possible during transition
- 📝 **Performance**: No significant performance impact expected
- 📝 **Team Training**: Learning investment required for architectural patterns