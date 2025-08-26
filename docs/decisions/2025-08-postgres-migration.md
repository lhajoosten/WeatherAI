# PostgreSQL Migration Decision Record

**Date:** 2025-08-26  
**Status:** Accepted  
**Issue:** #45 - Database-laag migreren van MSSQL naar PostgreSQL

## Context

WeatherAI was initially built using Microsoft SQL Server as the primary database. As the project evolves, we identified several factors that favor migrating to PostgreSQL:

1. **Development Experience**: PostgreSQL provides better developer tooling and is more widely used in open-source projects
2. **Infrastructure Simplicity**: Eliminates dependency on Microsoft-specific ODBC drivers and licensing
3. **Container Ecosystem**: Better integration with Docker/Kubernetes deployments
4. **Future Extensibility**: PostgreSQL's rich extension ecosystem (including pgvector for future embedding storage)
5. **Cross-Platform Development**: Improved development experience across different operating systems

## Decision

We will migrate from Microsoft SQL Server to PostgreSQL as the primary database for WeatherAI.

### Migration Approach (Phase 1)

**Scope**: Complete foundational migration enabling full application functionality on PostgreSQL

**Key Changes**:
- Replace `pyodbc`/`aioodbc` with `psycopg[binary]` 
- Convert `UNIQUEIDENTIFIER` columns to PostgreSQL `UUID` with `as_uuid=True`
- Update all connection strings and configuration
- Replace Docker SQL Server service with PostgreSQL
- Create new baseline Alembic migration for PostgreSQL schema
- Remove MSSQL-specific bootstrap and connection code

**Migration Strategy**: Clean cutover (no dual-write period) with controlled deployment after merge

## Alternatives Considered

### 1. Keep MSSQL
**Pros**: No migration effort, existing expertise  
**Cons**: Continued licensing costs, Docker complexity, limited extension ecosystem

### 2. Dual Database Support
**Pros**: Gradual migration, rollback capability  
**Cons**: Significant code complexity, maintenance overhead, delayed benefits

### 3. Other Database Systems
**MongoDB**: Not suitable for relational weather data  
**MySQL**: Less robust JSON support and extensions compared to PostgreSQL

## Consequences

### Positive
- **Simplified Development**: No more ODBC driver installation requirements
- **Better Tooling**: Rich PostgreSQL ecosystem (pgAdmin, various ORMs)
- **Container-Native**: Simplified Docker deployments
- **Future-Ready**: Enables pgvector for embeddings, advanced indexing
- **Cost Reduction**: Eliminates SQL Server licensing in production

### Negative
- **Migration Risk**: Schema and data migration complexity
- **Learning Curve**: Team needs PostgreSQL-specific knowledge
- **Breaking Change**: Requires coordinated deployment

### Neutral
- **Performance**: Expected similar performance for current workloads
- **Maintenance**: Different but comparable operational overhead

## Implementation Notes

### Database Schema Compatibility
- Most SQLAlchemy models are database-agnostic
- Main changes: `UNIQUEIDENTIFIER` → `UUID(as_uuid=True)`
- `func.now()` remains compatible across databases
- Removed MSSQL-specific `version_table_schema` configuration

### Connection Management
- Async engine using `psycopg` (PostgreSQL's modern Python driver)
- Maintained connection pooling and session management patterns
- Updated environment variables for PostgreSQL configuration

### Testing Strategy
- New baseline migration: `590348c0b8b5_initial_postgresql_schema_baseline`
- PostgreSQL-specific bootstrap with connectivity testing
- UUID roundtrip tests for data integrity verification

## Follow-up Actions

**Immediate (This PR)**:
- ✅ Core migration implementation  
- ✅ Updated documentation and environment examples
- ✅ New baseline Alembic migration
- ✅ PostgreSQL bootstrap functionality

**Future PRs**:
- Data migration tooling (if production data exists)
- pgvector integration for embeddings
- PostgreSQL-specific performance optimizations
- Advanced indexing strategies (GIN, partial indexes)

## Validation

### Success Criteria (All Met)
- ✅ Application boots with `docker-compose up` using PostgreSQL
- ✅ `alembic upgrade head` succeeds on clean PostgreSQL instance  
- ✅ All models import successfully with UUID columns
- ✅ Database connectivity tests pass
- ✅ No MSSQL dependencies remain in project files

### Test Results
```bash
# Migration generation and execution
alembic revision --autogenerate -m "Initial PostgreSQL schema baseline"
# INFO: Generated 590348c0b8b5_initial_postgresql_schema_baseline_.py

alembic upgrade head  
# INFO: Running upgrade -> 590348c0b8b5, Initial PostgreSQL schema baseline

# Database connectivity test
python -c "import asyncio; from app.infrastructure.db.bootstrap import test_database_connection; print('SUCCESS' if asyncio.run(test_database_connection()) else 'FAILED')"
# Output: SUCCESS
```

## References

- Issue #45: https://github.com/lhajoosten/WeatherAI/issues/45
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic Migrations: https://alembic.sqlalchemy.org/en/latest/