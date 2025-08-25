"""Redis-based vector storage implementation."""

import json
import numpy as np
from typing import List, Dict, Any
import structlog

from app.core.redis_client import redis_client
from app.core.config import get_settings
from ..models import Chunk, RetrievedChunk
from .base import VectorStore

logger = structlog.get_logger(__name__)


class RedisVectorStore(VectorStore):
    """
    Redis-based vector store implementation.
    
    Uses RediSearch with HNSW if available, falls back to brute force cosine similarity.
    
    Note: This is a basic implementation. For production use, consider:
    - Redis Stack with RediSearch module
    - Proper index management
    - Bulk operations optimization
    - Memory usage monitoring
    """
    
    def __init__(self, index_name: str = "rag_chunks"):
        """
        Initialize Redis vector store.
        
        Args:
            index_name: Name of the Redis index to use
        """
        self.index_name = index_name
        self.settings = get_settings()
        
        # Key prefixes for different data types
        self.chunk_prefix = f"{index_name}:chunk:"
        self.vector_prefix = f"{index_name}:vector:"
        self.metadata_prefix = f"{index_name}:meta:"
        
    async def add(
        self, 
        chunks: List[Chunk], 
        embeddings: List[List[float]], 
        metadata: Dict[str, Any] | None = None
    ) -> None:
        """
        Add chunks with embeddings to Redis.
        
        Stores chunk content, embeddings, and metadata separately for efficiency.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        if not chunks:
            return
        
        try:
            # Use Redis pipeline for bulk operations
            pipe = redis_client.pipeline()
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = chunk.content_hash
                
                # Store chunk content and metadata
                chunk_data = {
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "document_id": str(chunk.document_id) if chunk.document_id else None,
                    "idx": chunk.idx,
                    "metadata": json.dumps(chunk.metadata or {}),
                }
                
                # Store embedding as JSON (TODO: consider binary format for efficiency)
                embedding_data = {
                    "vector": json.dumps(embedding),
                    "dimension": len(embedding),
                }
                
                # Store global metadata
                meta_data = metadata or {}
                
                pipe.hset(f"{self.chunk_prefix}{chunk_id}", mapping=chunk_data)
                pipe.hset(f"{self.vector_prefix}{chunk_id}", mapping=embedding_data)
                pipe.hset(f"{self.metadata_prefix}{chunk_id}", mapping=meta_data)
                
                # Set expiration if configured (optional)
                # pipe.expire(f"{self.chunk_prefix}{chunk_id}", 86400)  # 24 hours
            
            await pipe.execute()
            
            logger.info(
                "Added chunks to vector store",
                index_name=self.index_name,
                num_chunks=len(chunks)
            )
            
        except Exception as e:
            logger.error(
                "Failed to add chunks to vector store",
                index_name=self.index_name,
                error=str(e)
            )
            raise
    
    async def query(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        filter_metadata: Dict[str, Any] | None = None
    ) -> List[RetrievedChunk]:
        """
        Query for similar chunks using brute force cosine similarity.
        
        TODO: Implement RediSearch/HNSW when available.
        """
        try:
            # Get all chunk IDs
            chunk_keys = await redis_client.keys(f"{self.chunk_prefix}*")
            
            if not chunk_keys:
                return []
            
            # Calculate similarities
            similarities = []
            
            for chunk_key in chunk_keys:
                chunk_id = chunk_key.decode().replace(self.chunk_prefix, "")
                
                # Get embedding
                vector_data = await redis_client.hgetall(f"{self.vector_prefix}{chunk_id}")
                if not vector_data:
                    continue
                
                stored_embedding = json.loads(vector_data[b"vector"].decode())
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                similarities.append((chunk_id, similarity))
            
            # Sort by similarity and take top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:top_k]
            
            # Retrieve chunk data for top results
            results = []
            for chunk_id, score in top_similarities:
                chunk_data = await redis_client.hgetall(f"{self.chunk_prefix}{chunk_id}")
                if not chunk_data:
                    continue
                
                # Reconstruct chunk
                metadata = json.loads(chunk_data[b"metadata"].decode())
                
                chunk = Chunk(
                    content=chunk_data[b"content"].decode(),
                    content_hash=chunk_data[b"content_hash"].decode(),
                    document_id=chunk_data[b"document_id"].decode() if chunk_data[b"document_id"] else None,
                    idx=int(chunk_data[b"idx"]) if chunk_data[b"idx"] else None,
                    metadata=metadata,
                )
                
                retrieved_chunk = RetrievedChunk(
                    chunk=chunk,
                    score=score,
                    source_id=metadata.get("source_id"),
                )
                
                results.append(retrieved_chunk)
            
            logger.debug(
                "Vector query completed",
                index_name=self.index_name,
                num_results=len(results),
                top_score=results[0].score if results else 0
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to query vector store",
                index_name=self.index_name,
                error=str(e)
            )
            raise
    
    async def delete(self, chunk_ids: List[str]) -> None:
        """Delete chunks by their IDs."""
        if not chunk_ids:
            return
        
        try:
            pipe = redis_client.pipeline()
            
            for chunk_id in chunk_ids:
                pipe.delete(f"{self.chunk_prefix}{chunk_id}")
                pipe.delete(f"{self.vector_prefix}{chunk_id}")
                pipe.delete(f"{self.metadata_prefix}{chunk_id}")
            
            await pipe.execute()
            
            logger.info(
                "Deleted chunks from vector store",
                index_name=self.index_name,
                num_chunks=len(chunk_ids)
            )
            
        except Exception as e:
            logger.error(
                "Failed to delete chunks from vector store",
                index_name=self.index_name,
                error=str(e)
            )
            raise
    
    async def clear(self) -> None:
        """Clear all chunks from this index."""
        try:
            # Get all keys for this index
            all_keys = []
            for prefix in [self.chunk_prefix, self.vector_prefix, self.metadata_prefix]:
                keys = await redis_client.keys(f"{prefix}*")
                all_keys.extend(keys)
            
            if all_keys:
                await redis_client.delete(*all_keys)
            
            logger.info(
                "Cleared vector store",
                index_name=self.index_name,
                num_keys=len(all_keys)
            )
            
        except Exception as e:
            logger.error(
                "Failed to clear vector store",
                index_name=self.index_name,
                error=str(e)
            )
            raise
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)