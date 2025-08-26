"""Retrieval orchestrator for RAG pipeline."""

from typing import List
import structlog

from app.core.settings import get_settings
from .embedding.base import Embedder
from .vectorstore.base import VectorStore
from .mmr import apply_mmr
from .models import RetrievedChunk
from .exceptions import LowSimilarityError

logger = structlog.get_logger(__name__)


class Retriever:
    """
    Orchestrates the retrieval process: embedding -> vector search -> optional MMR -> filtering.
    """
    
    def __init__(
        self, 
        embedder: Embedder, 
        vector_store: VectorStore,
        similarity_threshold: float | None = None,
        top_k: int | None = None,
        use_mmr: bool = True,
        mmr_lambda: float | None = None
    ):
        """
        Initialize retriever.
        
        Args:
            embedder: Text embedding implementation
            vector_store: Vector storage and search implementation
            similarity_threshold: Minimum similarity score to include results
            top_k: Maximum number of results to return
            use_mmr: Whether to apply MMR re-ranking for diversity
            mmr_lambda: MMR lambda parameter (relevance vs diversity trade-off)
        """
        self.embedder = embedder
        self.vector_store = vector_store
        
        # Use settings defaults if not provided
        settings = get_settings()
        self.similarity_threshold = similarity_threshold or settings.rag_similarity_threshold
        self.top_k = top_k or settings.rag_top_k
        self.use_mmr = use_mmr
        self.mmr_lambda = mmr_lambda or settings.rag_mmr_lambda
        
    async def retrieve(self, query: str) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query string
            
        Returns:
            List of retrieved chunks, filtered and optionally re-ranked
            
        Raises:
            LowSimilarityError: If all retrieved chunks have similarity below threshold
        """
        if not query.strip():
            return []
        
        # 1. Generate query embedding
        logger.debug("Generating query embedding", query_length=len(query))
        embedding_result = await self.embedder.embed_texts([query])
        
        if not embedding_result.embeddings:
            logger.warning("No embedding generated for query")
            return []
        
        query_embedding = embedding_result.embeddings[0]
        
        # 2. Vector search
        logger.debug("Performing vector search", top_k=self.top_k)
        candidates = await self.vector_store.query(
            query_embedding=query_embedding,
            top_k=self.top_k * 2 if self.use_mmr else self.top_k  # Get more for MMR
        )
        
        if not candidates:
            logger.info("No candidates found in vector search")
            return []
        
        # 3. Apply similarity threshold filter
        filtered_candidates = [
            chunk for chunk in candidates 
            if chunk.score >= self.similarity_threshold
        ]
        
        if not filtered_candidates:
            max_score = max(chunk.score for chunk in candidates) if candidates else 0
            logger.warning(
                "All candidates below similarity threshold",
                threshold=self.similarity_threshold,
                max_score=max_score,
                num_candidates=len(candidates)
            )
            raise LowSimilarityError(
                threshold=self.similarity_threshold,
                max_similarity=max_score
            )
        
        # 4. Apply MMR re-ranking for diversity (optional)
        if self.use_mmr and len(filtered_candidates) > 1:
            logger.debug(
                "Applying MMR re-ranking",
                num_candidates=len(filtered_candidates),
                lambda_mult=self.mmr_lambda
            )
            final_results = apply_mmr(
                candidates=filtered_candidates,
                query_vector=query_embedding,
                top_k=self.top_k,
                lambda_mult=self.mmr_lambda
            )
        else:
            # Just take top_k results by similarity score
            final_results = filtered_candidates[:self.top_k]
        
        # Phase 4: Calculate average similarity for guardrails and enhanced logging
        if final_results:
            avg_similarity = sum(chunk.score for chunk in final_results) / len(final_results)
            min_similarity = min(chunk.score for chunk in final_results)
            max_similarity = max(chunk.score for chunk in final_results)
            
            logger.info(
                "Retrieval completed with Phase 4 enhancements",
                query_length=len(query),
                num_candidates=len(candidates),
                num_filtered=len(filtered_candidates),
                num_final=len(final_results),
                avg_similarity=avg_similarity,
                min_similarity=min_similarity,
                max_similarity=max_similarity,
                threshold=self.similarity_threshold,
                used_mmr=self.use_mmr and len(filtered_candidates) > 1
            )
            
            # Phase 4: Additional guardrail check based on average similarity
            # This provides an additional quality gate beyond individual thresholds
            if avg_similarity < self.similarity_threshold:
                logger.warning(
                    "Average similarity below threshold - triggering guardrail",
                    avg_similarity=avg_similarity,
                    threshold=self.similarity_threshold
                )
                raise LowSimilarityError(
                    threshold=self.similarity_threshold,
                    max_similarity=max_similarity
                )
            
            return final_results
        
        logger.info(
            "Retrieval completed - no results",
            query_length=len(query),
            num_candidates=len(candidates),
            num_filtered=len(filtered_candidates)
        )
        
        return []