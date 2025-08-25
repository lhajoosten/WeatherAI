"""Core domain base model with shared naming conventions."""

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Shared naming convention for indexes and constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Core domain metadata with naming conventions
core_metadata = MetaData(naming_convention=naming_convention)

# Core domain declarative base (tables in core schema or public for backward compatibility)
CoreBase = declarative_base(metadata=core_metadata)
