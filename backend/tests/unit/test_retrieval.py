"""Tests for enhanced retrieval with MMR and guardrails - Phase 4."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List

from app.infrastructure.ai.rag.retrieval import Retriever
from app.infrastructure.ai.rag.mmr import apply_mmr
from app.infrastructure.ai.rag.models import RetrievedChunk, DocumentChunk, EmbeddingResult
from app.domain.exceptions import LowSimilarityError


class TestMMRRetrieval:
    """Test MMR re-ranking functionality."""
    
    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder."""
        embedder = AsyncMock()
        embedder.embed_texts.return_value = EmbeddingResult(
            embeddings=[[0.1, 0.2, 0.3]],  # Mock query embedding
            token_usage=10,
            model="test-model"
        )
        return embedder
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = AsyncMock()
        return store
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample retrieved chunks."""
        chunks = []
        for i in range(5):
            chunk = RetrievedChunk(
                chunk=DocumentChunk(
                    content=f"Sample content {i}",
                    document_id=f"doc_{i}",
                    chunk_index=i,
                    metadata={}
                ),
                score=0.9 - (i * 0.1),  # Decreasing similarity
                source_id=f"source_{i}"
            )
            chunks.append(chunk)
        return chunks
    
    def test_mmr_basic_functionality(self, sample_chunks):
        """Test basic MMR re-ranking."""
        query_vector = [0.1, 0.2, 0.3]
        
        # Apply MMR with balanced relevance/diversity
        result = apply_mmr(
            candidates=sample_chunks,
            query_vector=query_vector,
            top_k=3,
            lambda_mult=0.5
        )
        
        assert len(result) == 3
        assert all(isinstance(chunk, RetrievedChunk) for chunk in result)
        
        # First result should be highest scoring
        assert result[0].score == 0.9
    
    def test_mmr_high_relevance(self, sample_chunks):
        """Test MMR with high relevance weight."""
        query_vector = [0.1, 0.2, 0.3]
        
        # High lambda favors relevance
        result = apply_mmr(
            candidates=sample_chunks,
            query_vector=query_vector,
            top_k=3,
            lambda_mult=0.9
        )
        
        # Should prefer highest scoring chunks
        scores = [chunk.score for chunk in result]
        assert scores == sorted(scores, reverse=True)
    
    def test_mmr_high_diversity(self, sample_chunks):
        """Test MMR with high diversity weight."""
        query_vector = [0.1, 0.2, 0.3]
        
        # Low lambda favors diversity
        result = apply_mmr(
            candidates=sample_chunks,
            query_vector=query_vector,
            top_k=3,
            lambda_mult=0.1
        )
        
        assert len(result) == 3
        # With high diversity, results should not be strictly ordered by score
    
    def test_mmr_insufficient_candidates(self, sample_chunks):
        """Test MMR when requesting more results than available."""
        query_vector = [0.1, 0.2, 0.3]
        
        # Request more than available
        result = apply_mmr(
            candidates=sample_chunks[:2],  # Only 2 chunks
            query_vector=query_vector,
            top_k=5,  # Request 5
            lambda_mult=0.5
        )
        
        assert len(result) == 2  # Should return all available
    
    def test_mmr_empty_candidates(self):
        """Test MMR with empty candidate list."""
        query_vector = [0.1, 0.2, 0.3]
        
        result = apply_mmr(
            candidates=[],
            query_vector=query_vector,
            top_k=3,
            lambda_mult=0.5
        )
        
        assert result == []


class TestRetrievalGuardrails:
    """Test retrieval guardrails and average similarity."""
    
    @pytest.fixture
    def retriever_with_threshold(self, mock_embedder, mock_vector_store):
        """Create retriever with specific threshold."""
        return Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store,
            similarity_threshold=0.55,  # Phase 4 threshold
            top_k=3,
            use_mmr=True,
            mmr_lambda=0.5
        )
    
    @pytest.mark.asyncio
    async def test_average_similarity_guardrail_pass(self, retriever_with_threshold, sample_chunks):
        """Test guardrail when average similarity is above threshold."""
        
        # Mock high similarity chunks (all above 0.55)
        high_sim_chunks = [
            RetrievedChunk(
                chunk=sample_chunks[0].chunk,
                score=0.8,
                source_id="source_1"
            ),
            RetrievedChunk(
                chunk=sample_chunks[1].chunk,
                score=0.7,
                source_id="source_2"
            ),
            RetrievedChunk(
                chunk=sample_chunks[2].chunk,
                score=0.6,
                source_id="source_3"
            )
        ]
        
        # Average = (0.8 + 0.7 + 0.6) / 3 = 0.7 > 0.55 ✓
        
        retriever_with_threshold.vector_store.query.return_value = high_sim_chunks
        
        result = await retriever_with_threshold.retrieve("test query")
        
        assert len(result) == 3
        avg_similarity = sum(chunk.score for chunk in result) / len(result)
        assert avg_similarity >= 0.55
    
    @pytest.mark.asyncio
    async def test_average_similarity_guardrail_fail(self, retriever_with_threshold, sample_chunks):
        """Test guardrail when average similarity is below threshold."""
        
        # Mock low similarity chunks (average below 0.55)
        low_sim_chunks = [
            RetrievedChunk(
                chunk=sample_chunks[0].chunk,
                score=0.6,  # Above individual threshold
                source_id="source_1"
            ),
            RetrievedChunk(
                chunk=sample_chunks[1].chunk,
                score=0.5,  # Below individual threshold but close
                source_id="source_2"
            ),
            RetrievedChunk(
                chunk=sample_chunks[2].chunk,
                score=0.4,  # Below threshold
                source_id="source_3"
            )
        ]
        
        # Average = (0.6 + 0.5 + 0.4) / 3 = 0.5 < 0.55 ✗
        
        retriever_with_threshold.vector_store.query.return_value = low_sim_chunks
        
        with pytest.raises(LowSimilarityError) as exc_info:
            await retriever_with_threshold.retrieve("test query")
        
        assert exc_info.value.threshold == 0.55
    
    @pytest.mark.asyncio
    async def test_individual_threshold_filtering(self, retriever_with_threshold, sample_chunks):
        """Test that individual chunks below threshold are filtered."""
        
        # Mix of chunks - some above, some below threshold
        mixed_chunks = [
            RetrievedChunk(
                chunk=sample_chunks[0].chunk,
                score=0.8,  # Above threshold
                source_id="source_1"
            ),
            RetrievedChunk(
                chunk=sample_chunks[1].chunk,
                score=0.7,  # Above threshold
                source_id="source_2"
            ),
            RetrievedChunk(
                chunk=sample_chunks[2].chunk,
                score=0.3,  # Below threshold - should be filtered
                source_id="source_3"
            ),
            RetrievedChunk(
                chunk=sample_chunks[3].chunk,
                score=0.6,  # Above threshold
                source_id="source_4"
            )
        ]
        
        retriever_with_threshold.vector_store.query.return_value = mixed_chunks
        
        result = await retriever_with_threshold.retrieve("test query")
        
        # Should only return chunks above threshold
        assert len(result) == 3
        assert all(chunk.score >= 0.55 for chunk in result)
    
    @pytest.mark.asyncio
    async def test_no_results_after_filtering(self, retriever_with_threshold, sample_chunks):
        """Test when all chunks are filtered out by threshold."""
        
        # All chunks below threshold
        low_chunks = [
            RetrievedChunk(
                chunk=sample_chunks[0].chunk,
                score=0.3,
                source_id="source_1"
            ),
            RetrievedChunk(
                chunk=sample_chunks[1].chunk,
                score=0.2,
                source_id="source_2"
            )
        ]
        
        retriever_with_threshold.vector_store.query.return_value = low_chunks
        
        with pytest.raises(LowSimilarityError) as exc_info:
            await retriever_with_threshold.retrieve("test query")
        
        assert exc_info.value.threshold == 0.55
        assert exc_info.value.max_similarity == 0.3


class TestRetrievalWithMMRIntegration:
    """Test complete retrieval pipeline with MMR integration."""
    
    @pytest.fixture
    def retriever_mmr_enabled(self, mock_embedder, mock_vector_store):
        """Create retriever with MMR enabled."""
        return Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store,
            similarity_threshold=0.55,
            top_k=3,
            use_mmr=True,
            mmr_lambda=0.5
        )
    
    @pytest.fixture
    def retriever_mmr_disabled(self, mock_embedder, mock_vector_store):
        """Create retriever with MMR disabled."""
        return Retriever(
            embedder=mock_embedder,
            vector_store=mock_vector_store,
            similarity_threshold=0.55,
            top_k=3,
            use_mmr=False,
            mmr_lambda=0.5
        )
    
    @pytest.mark.asyncio
    async def test_retrieval_with_mmr(self, retriever_mmr_enabled, sample_chunks):
        """Test retrieval pipeline with MMR enabled."""
        
        # Return enough chunks for MMR to be meaningful
        retriever_mmr_enabled.vector_store.query.return_value = sample_chunks
        
        result = await retriever_mmr_enabled.retrieve("test query")
        
        # Should apply MMR and return top_k results
        assert len(result) <= 3
        assert all(chunk.score >= 0.55 for chunk in result)
    
    @pytest.mark.asyncio
    async def test_retrieval_without_mmr(self, retriever_mmr_disabled, sample_chunks):
        """Test retrieval pipeline with MMR disabled."""
        
        retriever_mmr_disabled.vector_store.query.return_value = sample_chunks
        
        result = await retriever_mmr_disabled.retrieve("test query")
        
        # Should return results in original order (highest similarity first)
        assert len(result) <= 3
        scores = [chunk.score for chunk in result]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, retriever_mmr_enabled):
        """Test handling of empty queries."""
        
        result = await retriever_mmr_enabled.retrieve("")
        assert result == []
        
        result = await retriever_mmr_enabled.retrieve("   ")
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__])