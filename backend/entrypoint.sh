#!/bin/sh
set -e

# Function to bootstrap database (create if it doesn't exist)
bootstrap_database() {
    echo "Starting database bootstrap process..."
    python - <<'PY'
import sys
import os

# Add environment variables with defaults
skip_bootstrap = os.getenv('SKIP_DB_BOOTSTRAP', 'false').lower() == 'true'
max_attempts = int(os.getenv('DB_BOOTSTRAP_MAX_ATTEMPTS', '30'))
sleep_seconds = int(os.getenv('DB_BOOTSTRAP_SLEEP_SECONDS', '2'))

if skip_bootstrap:
    print("Database bootstrap skipped by SKIP_DB_BOOTSTRAP=true")
    sys.exit(0)

try:
    from app.db.bootstrap import ensure_database
    
    success = ensure_database(
        max_attempts=max_attempts,
        sleep_seconds=sleep_seconds,
        skip_bootstrap=skip_bootstrap
    )
    
    if not success:
        print("Database bootstrap failed")
        sys.exit(1)
    else:
        print("Database bootstrap completed successfully")
        
except Exception as e:
    print(f"Database bootstrap error: {e}")
    sys.exit(1)
PY
}

# Function to check database connectivity
wait_for_db() {
    echo "Testing database connection..."
    python - <<'PY'
import asyncio, sys
from sqlalchemy import text

# Try common async SQLAlchemy exports: engine (recommended) or SessionLocal (fallback)
try:
    from app.db.database import engine
    async def check_db():
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("Database connection successful")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
except Exception as e_engine:
    try:
        from app.db.database import SessionLocal
        async def check_db():
            try:
                async with SessionLocal() as session:
                    await session.execute(text("SELECT 1"))
                print("Database connection successful")
                return True
            except Exception as e:
                print(f"Database connection failed: {e}")
                return False
    except Exception as e_session:
        print("Unable to import engine or SessionLocal from app.db.database:", e_engine, e_session)
        sys.exit(1)

if not asyncio.run(check_db()):
    sys.exit(1)
PY
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    
    # Get current migration version before upgrade
    CURRENT_VERSION=$(alembic current 2>/dev/null | grep -o '[a-f0-9]\{12\}' || echo "none")
    echo "Current migration version: $CURRENT_VERSION"
    
    # Run migrations
    if alembic upgrade head; then
        # Get version after upgrade
        NEW_VERSION=$(alembic current 2>/dev/null | grep -o '[a-f0-9]\{12\}' || echo "none")
        echo "Migration completed successfully. New version: $NEW_VERSION"
        
        # Log migration action
        python -c "
import structlog
logger = structlog.get_logger(__name__)
logger.info(
    'Database migration completed',
    action='migration.upgrade',
    status='success',
    from_version='$CURRENT_VERSION',
    to_version='$NEW_VERSION'
)
"
    else
        echo "Migration failed with exit code $?"
        
        # Check if DEV_FALLBACK is enabled
        if [ "$DEV_FALLBACK" = "true" ]; then
            echo "DEV_FALLBACK enabled, attempting create_all fallback..."
            python -c "
import asyncio
from app.db.database import engine
from app.db.models import Base
import structlog

logger = structlog.get_logger(__name__)

async def create_all():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.warning(
            'Used create_all fallback due to migration failure',
            action='migration.upgrade',
            status='fallback',
            reason='migration_failed'
        )
        print('create_all fallback completed')
    except Exception as e:
        logger.error(
            'create_all fallback failed',
            action='migration.upgrade', 
            status='error',
            error=str(e)
        )
        raise

asyncio.run(create_all())
"
        else
            echo "Migration failed and DEV_FALLBACK not enabled. Exiting."
            python -c "
import structlog
logger = structlog.get_logger(__name__)
logger.error(
    'Database migration failed',
    action='migration.upgrade',
    status='error',
    reason='migration_failed'
)
"
            exit 1
        fi
    fi
}

# Main execution
echo "Starting WeatherAI Backend..."
echo "Bootstrap configuration: MAX_ATTEMPTS=$DB_BOOTSTRAP_MAX_ATTEMPTS, SLEEP_SECONDS=$DB_BOOTSTRAP_SLEEP_SECONDS, SKIP=$SKIP_DB_BOOTSTRAP"

# Ensure database exists before attempting connections
ensure_database

# Bootstrap database first
bootstrap_database

# Test database connection
wait_for_db

# Run migrations
run_migrations

# Start the application
echo "Starting application server..."
exec "$@"