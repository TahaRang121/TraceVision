"""
Embeddings storage module for TraceVision.

Provides a Qdrant-backed vector store for person appearance embeddings,
supporting storage, retrieval, and similarity search operations.
"""

from .embedding_store import EmbeddingStore

__all__ = ["EmbeddingStore"]
