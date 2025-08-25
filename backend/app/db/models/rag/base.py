"""RAG domain base model with rag schema."""

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

# RAG domain metadata with naming conventions and rag schema
rag_metadata = MetaData(naming_convention=naming_convention, schema="rag")

# RAG domain declarative base (tables in rag schema)
RagBase = declarative_base(metadata=rag_metadata)
