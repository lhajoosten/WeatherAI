"""Database models package."""

# Import domain bases
from .core import CoreBase
from .rag import RagBase, Document, DocumentChunk

# Legacy import for backward compatibility - import from the parent models.py
import importlib.util
from pathlib import Path

# Load the Base from the models.py file at the db level
models_file = Path(__file__).parent.parent / "models.py"
spec = importlib.util.spec_from_file_location("legacy_models", models_file)
legacy_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_models)

Base = legacy_models.Base

# Export new RAG models for external use
__all__ = [
    "Base",  # Legacy base for existing models
    "CoreBase",  # Core domain base
    "RagBase",  # RAG domain base
    "Document",  # RAG document model
    "DocumentChunk",  # RAG document chunk model
]