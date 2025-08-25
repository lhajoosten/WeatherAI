# ADR-001: Phase 1 Backend Directory Structure Normalization

**Date:** 2025-08-25  
**Status:** Accepted  
**Authors:** WeatherAI Team  

## Context

The WeatherAI backend has grown organically and needs structural standardization to support future development phases. The current structure has:

- Mixed concerns between analytics and core functionality
- Inconsistent import patterns across modules  
- Missing organizational structure for planned AI/LLM pipeline
- No dedicated utilities package for shared functions
- Database session management without clear documentation

We need to establish a clean foundation for future phases that will introduce:
- Domain exception layers
- Service/repository boundary refinement  
- Advanced LLM/RAG pipeline implementation
- Enhanced rate limiting and analytics modularization

## Decision

Implement a **Phase 1 structural normalization** with the following changes:

### Directory Structure
1. **Move `backend/ai/` to `backend/app/ai/`** - Consolidate all app code under single namespace
2. **Add `backend/app/utils/`** - Shared utilities (starting with datetime helpers)
3. **Add `backend/app/scripts/`** - Placeholder for future management commands
4. **Enhance `backend/app/db/`** - Add clear documentation about session management role

### Import Standardization  
1. **Update all imports** referencing moved `ai/` module to use `app.ai.*`
2. **Add absolute import consistency** across all modules
3. **Add TODO markers** for future repository-level abstractions

### Documentation & Quality
1. **Update README** to reflect new structure and clarify responsibilities
2. **Add module docstrings** explaining purpose and future plans
3. **Maintain code quality** with ruff/mypy compliance

## Alternatives Considered

### 1. Leave structure as-is
- **Pros:** No immediate change risk
- **Cons:** Technical debt accumulation, harder future refactoring

### 2. Big-bang restructuring  
- **Pros:** Complete modernization immediately
- **Cons:** High risk, large diff, potential for regression

### 3. Gradual service-by-service refactoring
- **Pros:** Lower risk per change
- **Cons:** Slower progress, inconsistent intermediate states

## Consequences

### Positive
- ✅ **Foundation for future phases**: Clean structure for domain/service separation
- ✅ **Improved maintainability**: Clear package responsibilities and imports
- ✅ **Enhanced developer experience**: Consistent structure following guidelines
- ✅ **Documentation clarity**: Explicit role definitions and future plans

### Negative  
- ⚠️ **Import updates required**: Need to update existing import statements
- ⚠️ **Temporary scaffolding**: Some placeholder modules until future phases

### Neutral
- 📝 **No behavioral changes**: API contracts and runtime behavior unchanged
- 📝 **No performance impact**: Structural changes only

## Implementation Plan

1. ✅ Move `ai/` directory to `app/ai/`
2. ✅ Create `app/utils/` with `datetime.py` utility
3. ✅ Create `app/scripts/` placeholder with documentation
4. ✅ Update imports in affected modules (`digest_service.py`, test files)
5. ✅ Add database session management documentation
6. ✅ Add TODO comments for future abstraction points
7. ✅ Update README project structure section
8. ✅ Validate with linting and type checking

## Future Phases (Out of Scope)

- **Phase 2:** Domain exception layer introduction
- **Phase 3:** Service/repository boundary refinement  
- **Phase 4:** Advanced RAG pipeline implementation
- **Phase 5:** Analytics platform modularization

## Validation Criteria

- [x] Application imports successfully: `python -c "import app.main"`
- [x] No new linting errors introduced  
- [x] Directory structure matches guidelines
- [x] Documentation updated and accurate
- [x] All affected imports updated correctly