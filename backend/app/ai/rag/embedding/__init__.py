"""Embedding package initialization."""

from .base import Embedder
from .azure_openai import AzureOpenAIEmbedder

__all__ = ["Embedder", "AzureOpenAIEmbedder"]