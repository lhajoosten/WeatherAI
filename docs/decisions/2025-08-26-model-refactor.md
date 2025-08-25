# ADR-002: Multi-Schema Model Refactor (Phase 3)

**Date:** 2025-08-26  
**Status:** Accepted  
**Authors:** WeatherAI Team  

## Context

Following the Phase 1 backend directory structure normalization, the WeatherAI application needs a more robust database organization strategy to support growing domain complexity. The current single-schema approach with prefixed table names (e.g., `rag_documents`) presents several challenges:

- **Domain Mixing**: Core application and RAG functionality tables mixed in public schema
- **Naming Conflicts**: Risk of table name collisions as domains grow
- **Maintenance Complexity**: Difficult to apply domain-specific migrations and permissions
- **Unclear Ownership**: No clear boundary between different functional areas
- **Migration Challenges**: Complex to manage domain-specific database changes

The application currently has:
- Core functionality (users, locations, analytics) in public schema
- RAG tables (`rag_documents`, `rag_document_chunks`) in public schema with prefixes
- Single Alembic metadata tracking all tables together
- Monolithic model file growing in complexity

Future planned domains include:
- Enhanced RAG pipeline with embedding tables
- Analytics aggregation tables
- Potential multi-tenant support
- External integration audit tables

## Decision

Implement a **multi-schema database organization** with domain-specific declarative bases and organized migration management.

### Database Schema Organization

1. **Core Schema (`core`)**
   - Core application tables: users, locations, preferences, basic analytics
   - Houses the Alembic version tracking table
   - Uses `CoreBase` declarative base with shared naming conventions

2. **RAG Schema (`rag`)**  
   - RAG-specific tables: documents, document_chunks (no prefixes)
   - Future: embeddings, vector indexes, prompt_versions
   - Uses `RagBase` declarative base with `schema="rag"`

3. **Public Schema (Transitional)**
   - Legacy tables during migration period
   - Gradually migrated to appropriate domain schemas

### ORM Model Structure

1. **Separate Declarative Bases**
   ```python
   # app/db/models/core/base.py
   CoreBase = declarative_base(metadata=core_metadata)
   
   # app/db/models/rag/base.py  
   RagBase = declarative_base(metadata=rag_metadata)
   ```

2. **Domain-Specific Model Files**
   ```
   app/db/models/
   ├── core/
   │   ├── base.py
   │   └── __init__.py
   ├── rag/
   │   ├── base.py
   │   ├── document.py
   │   ├── document_chunk.py
   │   └── __init__.py
   └── __init__.py (exports for backward compatibility)
   ```

3. **Shared Naming Conventions**
   - Consistent index/constraint naming across all schemas
   - Simplified table names without domain prefixes within schemas

### Migration Strategy

1. **Multi-Metadata Alembic Setup**
   - Target multiple metadata objects: `[Base.metadata, CoreBase.metadata, RagBase.metadata]`
   - Schema-aware migration generation with `include_schemas=True`
   - Version table in core schema: `version_table_schema="core"`

2. **Phased Table Migration**
   - Create schemas (`core`, `rag`)
   - Move existing RAG tables: `public.rag_documents` → `rag.documents`
   - Rename to remove prefixes: `rag_document_chunks` → `document_chunks`
   - Update foreign key constraints and index names

### Environment Configuration

Add schema configuration variables to `.env.example`:
```bash
# Schema Configuration (Phase 3)
DB_SCHEMA_CORE=core
DB_SCHEMA_RAG=rag
```

## Alternatives Considered

### 1. Maintain Single Schema with Prefixes
- **Pros:** No migration complexity, simple Alembic setup
- **Cons:** Continued naming conflicts, poor domain separation, scaling issues
- **Rejected:** Does not address long-term organizational needs

### 2. Separate Databases per Domain  
- **Pros:** Complete isolation, independent scaling
- **Cons:** Cross-domain queries complexity, connection pooling overhead, operational complexity
- **Rejected:** Overengineering for current scale

### 3. Table Naming Conventions Only
- **Pros:** Simple to implement, no schema changes needed
- **Cons:** Still single namespace, no permission boundaries, limited organizational benefits
- **Rejected:** Insufficient for growing complexity

### 4. Microservices with Separate Databases
- **Pros:** Complete service isolation
- **Cons:** Major architectural change, data consistency challenges, development overhead
- **Rejected:** Too large a change for Phase 3 scope

## Consequences

### Positive
- ✅ **Clear Domain Boundaries**: Logical separation of concerns at database level
- ✅ **Simplified Table Names**: Remove prefixes within schemas (e.g., `rag.documents` vs `public.rag_documents`)
- ✅ **Schema-Level Security**: Fine-grained permissions per domain
- ✅ **Migration Isolation**: Domain-specific changes easier to manage
- ✅ **Future Scalability**: Foundation for additional domains and features
- ✅ **Backward Compatibility**: Existing code continues to work during transition

### Negative
- ⚠️ **Migration Complexity**: One-time complex migration to move tables
- ⚠️ **Alembic Configuration**: More complex metadata management
- ⚠️ **Cross-Schema Queries**: Need to handle schema-qualified names in some contexts

### Neutral
- 📝 **Model Import Changes**: Update imports to use new domain-specific models
- 📝 **Documentation Updates**: New migration and schema documentation needed
- 📝 **Development Patterns**: Establish patterns for multi-schema development

## Implementation Plan

### Phase 3 (Current)
1. ✅ Create domain-specific base classes (`CoreBase`, `RagBase`)
2. ✅ Implement new RAG models in `app/db/models/rag/`
3. ✅ Update Alembic configuration for multi-metadata
4. ✅ Create migration to move RAG tables to `rag` schema
5. ✅ Add environment consistency checking tool
6. ✅ Update documentation (migrations guide + this ADR)

### Future Phases
- **Phase 4**: Migrate core tables to `core` schema
- **Phase 5**: Add ingest_job and prompt_versions tables to appropriate schemas  
- **Phase 6**: Implement schema-level permission strategy
- **Phase 7**: Add embedding and vector index tables to `rag` schema

## Validation Criteria

- [x] CoreBase and RagBase defined with consistent naming conventions
- [x] Alembic env.py targets multiple metadata objects
- [x] Migration script creates schemas and moves tables safely
- [x] After migration: tables exist as `rag.documents` and `rag.document_chunks`
- [x] No tables with `rag_` prefix remain in any schema
- [x] Environment consistency script passes validation
- [x] Documentation accurately reflects new strategy
- [ ] Tests pass with new model imports (to be validated)
- [x] Unique constraint on `(document_id, idx)` enforced in new model

## Rollback Plan

If issues arise:
1. **Immediate**: Use Alembic downgrade to reverse table moves
2. **Partial**: Keep schemas but move tables back to public temporarily  
3. **Full**: Revert to single-schema approach with prefixed names

The migration includes complete downgrade logic to restore original state.

## References

- Phase 1 ADR: `docs/decisions/2025-08-25-phase1-structure.md`
- Migration Guide: `docs/migrations.md`
- SQLAlchemy Multi-Schema Documentation
- Alembic Schema Management Best Practices