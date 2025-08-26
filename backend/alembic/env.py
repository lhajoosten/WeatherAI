import sys, os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Add the app directory to the Python path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.infrastructure.db.models import Base
from app.infrastructure.db.database import engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ensure target_metadata uses Base.metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use database URL from app settings
    url = settings.database_url_sync
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the sqlalchemy.url with our app settings
    # We need to manually create the engine to avoid config parser URL issues
    engine = create_engine(settings.database_url_sync, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
