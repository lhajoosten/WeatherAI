"""RAG streaming service for Phase 4."""

import asyncio
import json
from typing import AsyncGenerator, Optional
import structlog

from app.core.constants import PROMPT_VERSION, DomainErrorCode
from app.core.config import get_settings
from app.domain.exceptions import (
    QueryValidationError,
    NoContextAvailableError,
    RetrievalTimeoutError,
    InternalProcessingError
)
from app.infrastructure.ai.rag.pipeline import RAGPipeline
from app.infrastructure.ai.rag.streaming_rate_limit import check_streaming_rate_limit
from app.infrastructure.ai.rag.metrics import (
    record_guardrail_triggered,
    record_pipeline_error,
    log_pipeline_metrics
)
from app.schemas.rag_stream import (
    StreamTokenEvent,
    StreamDoneEvent,
    StreamErrorEvent
)

logger = structlog.get_logger(__name__)


class RAGStreamingService:
    """Service for streaming RAG responses with Phase 4 enhancements."""
    
    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline
        self.settings = get_settings()
    
    def _validate_query(self, query: str) -> None:
        """Validate query according to Phase 4 requirements."""
        if not query or not query.strip():
            raise QueryValidationError("Query cannot be empty")
        
        if len(query) > self.settings.rag_max_query_length:
            raise QueryValidationError(
                f"Query length exceeds maximum of {self.settings.rag_max_query_length} characters",
                query_length=len(query),
                max_length=self.settings.rag_max_query_length
            )
    
    async def _stream_llm_response(self, prompt_parts, context_metadata: dict) -> AsyncGenerator[str, None]:
        """Stream LLM response token by token (placeholder implementation)."""
        # TODO: Implement actual streaming LLM generation
        # For now, simulate streaming by yielding answer in chunks
        try:
            generation_result = await self.pipeline.llm_generator.generate(prompt_parts)
            answer = generation_result.text
            
            # Simulate streaming by yielding words
            words = answer.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error("LLM generation failed during streaming", error=str(e))
            raise InternalProcessingError("LLM generation failed", original_error=e)
    
    async def stream_answer(
        self,
        query: str,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream RAG answer with events: token, done, error.
        
        Args:
            query: User query
            user_id: Optional user identifier for rate limiting
            trace_id: Optional trace ID for observability
            
        Yields:
            SSE formatted events (data: {json})
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Phase 4: Input validation
            self._validate_query(query)
            
            # Phase 4: Rate limiting check
            await check_streaming_rate_limit(user_id)
            
            # Phase 4: Check answer cache first
            sanitized_query = query.strip()
            cached_answer = await self.pipeline.answer_cache.get(
                sanitized_query, 
                PROMPT_VERSION
            )
            
            if cached_answer:
                # Stream cached answer
                logger.info(
                    "Streaming cached answer",
                    event="rag_stream_cache_hit",
                    user_id=user_id,
                    trace_id=trace_id,
                    query_hash=hash(sanitized_query) % (10**8),
                    truncated_query=sanitized_query[:120],
                    prompt_version=PROMPT_VERSION
                )
                
                # Stream the cached answer as tokens
                words = cached_answer.answer.split()
                for i, word in enumerate(words):
                    token_event = StreamTokenEvent(data=word + (" " if i < len(words) - 1 else ""))
                    yield f"data: {token_event.model_dump_json()}\n\n"
                    await asyncio.sleep(0.01)
                
                # Send done event
                done_event = StreamDoneEvent.create(
                    sources_count=len(cached_answer.sources),
                    prompt_version=PROMPT_VERSION
                )
                done_event.data["cache_hit"] = True
                yield f"data: {done_event.model_dump_json()}\n\n"
                return
            
            # Phase 4: Retrieval with timeout
            try:
                retrieval_start = asyncio.get_event_loop().time()
                retrieved_chunks = await asyncio.wait_for(
                    self.pipeline.retriever.retrieve(sanitized_query),
                    timeout=30.0  # 30 second timeout
                )
                retrieval_latency_ms = (asyncio.get_event_loop().time() - retrieval_start) * 1000
                
            except asyncio.TimeoutError:
                raise RetrievalTimeoutError(30.0)
            
            # Phase 4: Guardrail - Check average similarity
            if retrieved_chunks:
                avg_similarity = sum(chunk.score for chunk in retrieved_chunks) / len(retrieved_chunks)
                min_similarity = min(chunk.score for chunk in retrieved_chunks)
                
                if avg_similarity < self.settings.rag_similarity_threshold:
                    # Trigger guardrail
                    record_guardrail_triggered("similarity_threshold")
                    
                    logger.info(
                        "Guardrail triggered - low similarity",
                        event="rag_guardrail_triggered",
                        user_id=user_id,
                        trace_id=trace_id,
                        avg_similarity=avg_similarity,
                        threshold=self.settings.rag_similarity_threshold,
                        query_hash=hash(sanitized_query) % (10**8),
                        truncated_query=sanitized_query[:120],
                        prompt_version=PROMPT_VERSION
                    )
                    
                    # Send fallback response
                    fallback_text = "I don't have enough relevant information to answer this question based on the available documents."
                    
                    # Stream fallback as tokens
                    words = fallback_text.split()
                    for i, word in enumerate(words):
                        token_event = StreamTokenEvent(data=word + (" " if i < len(words) - 1 else ""))
                        yield f"data: {token_event.model_dump_json()}\n\n"
                        await asyncio.sleep(0.01)
                    
                    # Send done event with guardrail info
                    done_event = StreamDoneEvent.create(
                        sources_count=0,
                        guardrail="no_context",
                        prompt_version=PROMPT_VERSION
                    )
                    yield f"data: {done_event.model_dump_json()}\n\n"
                    return
            else:
                # No chunks retrieved
                raise NoContextAvailableError(self.settings.rag_similarity_threshold)
            
            # Build prompt
            prompt_parts = self.pipeline.prompt_builder.build_prompt(
                sanitized_query,
                retrieved_chunks
            )
            
            # Context metadata for logging
            context_metadata = {
                "num_retrieved": len(retrieved_chunks),
                "min_similarity": min_similarity,
                "avg_similarity": avg_similarity,
                "context_tokens": self.pipeline.prompt_builder.estimate_token_count(prompt_parts)
            }
            
            # Stream LLM response
            tokens_generated = 0
            async for token in self._stream_llm_response(prompt_parts, context_metadata):
                token_event = StreamTokenEvent(data=token)
                yield f"data: {token_event.model_dump_json()}\n\n"
                tokens_generated += 1
            
            # Log metrics
            total_latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            log_pipeline_metrics(
                query=sanitized_query,
                num_retrieved=len(retrieved_chunks),
                num_filtered=len(retrieved_chunks),  # TODO: Add filtering step
                min_similarity=min_similarity,
                context_tokens=context_metadata["context_tokens"],
                cache_hits={"answer": False, "embedding": False},  # TODO: Track embedding cache
                retrieval_latency_ms=retrieval_latency_ms,
                tokens_out=tokens_generated
            )
            
            # Send done event
            done_event = StreamDoneEvent.create(
                total_tokens=tokens_generated,
                sources_count=len(retrieved_chunks),
                prompt_version=PROMPT_VERSION
            )
            yield f"data: {done_event.model_dump_json()}\n\n"
            
        except QueryValidationError as e:
            error_event = StreamErrorEvent.create(
                error_code=DomainErrorCode.VALIDATION_ERROR,
                message=str(e),
                details=e.extra_data
            )
            yield f"data: {error_event.model_dump_json()}\n\n"
            
        except NoContextAvailableError as e:
            error_event = StreamErrorEvent.create(
                error_code=DomainErrorCode.NO_CONTEXT,
                message=str(e),
                details=e.extra_data
            )
            yield f"data: {error_event.model_dump_json()}\n\n"
            
        except RetrievalTimeoutError as e:
            error_event = StreamErrorEvent.create(
                error_code=DomainErrorCode.RETRIEVAL_TIMEOUT,
                message=str(e),
                details=e.extra_data
            )
            yield f"data: {error_event.model_dump_json()}\n\n"
            
        except Exception as e:
            record_pipeline_error(type(e).__name__, "streaming", query)
            
            logger.error(
                "Streaming error",
                event="rag_stream_error",
                error=str(e),
                user_id=user_id,
                trace_id=trace_id,
                query_hash=hash(query) % (10**8) if query else None,
                truncated_query=query[:120] if query else None,
                prompt_version=PROMPT_VERSION
            )
            
            error_event = StreamErrorEvent.create(
                error_code=DomainErrorCode.INTERNAL_ERROR,
                message="An internal error occurred while processing your request",
                details={"error_type": type(e).__name__}
            )
            yield f"data: {error_event.model_dump_json()}\n\n"