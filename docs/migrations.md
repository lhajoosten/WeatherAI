# Database Migrations Guide

This guide covers the WeatherAI database migration strategy, particularly the multi-schema approach introduced in Phase 3.

## Overview

WeatherAI uses Alembic for database migrations and follows a multi-schema approach to organize tables by domain:

- **core schema**: Core application tables (users, locations, analytics, etc.)
- **rag schema**: RAG (Retrieval Augmented Generation) specific tables
- **public schema**: Legacy tables (for backward compatibility during transition)

## Multi-Schema Strategy

### Benefits

1. **Domain Separation**: Clear separation between different functional areas
2. **Maintainability**: Easier to manage and understand related tables
3. **Security**: Schema-level permissions can be applied per domain
4. **Migration Safety**: Domain-specific changes are isolated

### Schema Organization

```
Database: WeatherAI
├── core/               # Core application domain
│   ├── users
│   ├── locations
│   ├── analytics tables
│   └── alembic_version (migration tracking)
├── rag/                # RAG domain  
│   ├── documents
│   └── document_chunks
└── public/             # Legacy tables (transitional)
```

## Generating Migrations

### Prerequisites

1. Ensure all model files are imported in `alembic/env.py`
2. Verify database connection is configured
3. Check that target metadata includes all domain bases

### Generate New Migration

```bash
# From backend directory
alembic revision --autogenerate -m "Description of changes"
```

The autogenerate will detect changes across all schemas due to the multi-metadata configuration.

### Manual Migration Creation

For complex schema operations (like moving tables between schemas):

```bash
alembic revision -m "Manual migration description"
```

Then edit the generated file to add custom SQL operations.

## Moving Tables Between Schemas

### Example: Moving Tables to New Schema

```python
def upgrade():
    # Create new schema
    op.execute("CREATE SCHEMA IF NOT EXISTS new_schema")
    
    # Move table
    op.execute("ALTER TABLE public.table_name SET SCHEMA new_schema")
    
    # Rename if needed
    op.execute("ALTER TABLE new_schema.old_name RENAME TO new_name")
    
    # Update foreign key references
    op.execute("ALTER TABLE new_schema.child_table DROP CONSTRAINT old_fk")
    op.execute("ALTER TABLE new_schema.child_table ADD CONSTRAINT new_fk FOREIGN KEY (parent_id) REFERENCES new_schema.parent_table(id)")

def downgrade():
    # Reverse operations
    op.execute("ALTER TABLE new_schema.child_table DROP CONSTRAINT new_fk")
    op.execute("ALTER TABLE new_schema.new_name RENAME TO old_name") 
    op.execute("ALTER TABLE new_schema.old_name SET SCHEMA public")
```

### Index and Constraint Handling

When moving tables, indexes and constraints typically move with the table, but names may need updating:

```python
# Rename index to follow new naming convention
op.execute("EXEC sp_rename 'rag.documents.old_index_name', 'new_index_name', 'INDEX'")
```

## Rollback Strategy

### General Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback to base (DANGEROUS)
alembic downgrade base
```

### Schema Move Rollbacks

When rolling back schema moves:

1. **Data Preservation**: Ensure data is not lost during schema moves
2. **Constraint Recreation**: Foreign keys and constraints must be properly recreated
3. **Application Compatibility**: Ensure application can handle the schema state during rollback

### Rollback Testing

Always test rollbacks in development:

```bash
# Apply migration
alembic upgrade head

# Test rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

## Best Practices

### 1. Migration Safety

- Always backup production data before major migrations
- Test migrations in staging environment first
- Use transactions for atomic operations
- Validate data integrity after migrations

### 2. Schema Design

- Group related tables in the same schema
- Use consistent naming conventions within schemas
- Plan schema organization before creating tables
- Document schema purpose and ownership

### 3. Multi-Schema Considerations

- Update application code to use schema-qualified table names when needed
- Ensure ORM models specify correct schema
- Update any raw SQL queries to use correct schema references
- Consider cross-schema foreign key implications

### 4. Naming Conventions

Follow consistent naming patterns:

```python
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
```

## Troubleshooting

### Common Issues

1. **Schema Permission Errors**
   ```sql
   -- Grant schema usage
   GRANT USAGE ON SCHEMA schema_name TO user_name;
   GRANT CREATE ON SCHEMA schema_name TO user_name;
   ```

2. **Cross-Schema Foreign Key Issues**
   - Ensure both schemas are accessible by the application user
   - Use fully qualified names in foreign key definitions

3. **Alembic Version Table Location**
   - The version table is in the core schema: `core.alembic_version`
   - Ensure the application user has access to this schema

4. **Migration Detection Issues**
   - Verify all model files are properly imported
   - Check that metadata objects are included in `target_metadata`
   - Ensure model `__tablename__` and schema settings are correct

### Debugging Migration Issues

```bash
# Check current migration state
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show <revision>

# Dry run (show SQL without executing)
alembic upgrade --sql head
```

## Phase 3 Specific Notes

The Phase 3 migration (`20250826_0004_move_rag_to_schema`) specifically:

- Moves `public.rag_documents` → `rag.documents`
- Moves `public.rag_document_chunks` → `rag.document_chunks`
- Updates foreign key constraints
- Renames indexes to follow new conventions
- Handles SQL Server specific syntax for index renaming

This migration preserves all existing data while establishing the new schema organization.