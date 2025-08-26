"""RAG Pipeline orchestrator."""

from typing import Dict, Any, List
from uuid import UUID
import structlog

from app.core.settings import get_settings
from app.infrastructure.db.database import get_db
from app.infrastructure.db import RagDocumentRepository

from .models import Document, AnswerResult
from .chunking import DefaultTokenChunker
from .cleaning import clean_text
from .embedding.azure_openai import AzureOpenAIEmbedder
from .vectorstore.redis_store import RedisVectorStore
from .retrieval import Retriever
from .prompt_builder import PromptBuilder
from .generator import LLMGenerator
from .caching import create_embedding_cache, create_answer_cache
from .guardrails import sanitize_user_query, check_context_quality
from .metrics import (
    time_retrieval, 
    time_generation, 
    log_pipeline_metrics,
    record_pipeline_error
)
from .exceptions import RAGError, LowSimilarityError, EmptyContextError

logger = structlog.get_logger(__name__)


class RAGPipeline:
    """
    Main RAG pipeline orchestrator.
    
    Coordinates the entire ingestion and retrieval process:
    - Ingest: clean -> chunk -> embed -> vectorstore.add -> persist docs/chunks in DB
    - Answer: check answer cache -> retrieve -> prompt build -> generate -> store in cache
    """
    
    def __init__(
        self,
        embedder=None,
        vector_store=None,
        llm_generator=None,
        chunker=None,
        prompt_builder=None,
        embedding_cache=None,
        answer_cache=None
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            embedder: Text embedding implementation
            vector_store: Vector storage implementation
            llm_generator: LLM generation implementation
            chunker: Text chunking implementation
            prompt_builder: Prompt building implementation
            embedding_cache: Embedding cache implementation
            answer_cache: Answer cache implementation
        """
        self.settings = get_settings()
        
        # Initialize components with defaults if not provided
        self.embedding_cache = embedding_cache or create_embedding_cache()
        self.answer_cache = answer_cache or create_answer_cache()
        
        self.embedder = embedder or AzureOpenAIEmbedder(cache=self.embedding_cache)
        self.vector_store = vector_store or RedisVectorStore()
        self.chunker = chunker or DefaultTokenChunker(
            chunk_size=self.settings.rag_chunk_size,
            chunk_overlap=self.settings.rag_chunk_overlap
        )
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.llm_generator = llm_generator or LLMGenerator()
        
        # Initialize retriever
        self.retriever = Retriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            similarity_threshold=self.settings.rag_similarity_threshold,
            top_k=self.settings.rag_top_k,
            mmr_lambda=self.settings.rag_mmr_lambda
        )
    
    async def ingest(
        self, 
        source_id: str, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG system.
        
        Process: clean -> chunk -> embed -> vectorstore.add -> persist docs/chunks in DB
        
        Args:
            source_id: Unique identifier for the document source
            text: Raw text content to ingest
            metadata: Optional metadata to associate with the document
            
        Returns:
            Dictionary with ingestion results
        """
        if not source_id or not text.strip():
            raise ValueError("source_id and text are required")
        
        try:
            logger.info("Starting document ingestion", source_id=source_id, text_length=len(text))
            
            # 1. Clean text
            cleaned_text = clean_text(text)
            if not cleaned_text.strip():
                raise ValueError("Document has no content after cleaning")
            
            # 2. Create document record
            async with get_db() as session:
                repo = RagDocumentRepository(session)
                
                # Check if document already exists
                existing_doc = await repo.get_by_source_id(source_id)
                if existing_doc:
                    logger.warning("Document already exists", source_id=source_id)
                    return {
                        "document_id": str(existing_doc.id),
                        "chunks": 0,
                        "status": "already_exists"
                    }
                
                # Create new document
                document = await repo.create_document(source_id)
                document_id = document.id
            
            # 3. Chunk text
            chunks = self.chunker.chunk_text(cleaned_text, document_id=str(document_id))
            if not chunks:
                raise EmptyContextError("No chunks generated from document")
            
            logger.debug("Generated chunks", num_chunks=len(chunks), document_id=str(document_id))
            
            # 4. Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embedding_result = await self.embedder.embed_texts(chunk_texts)
            
            if len(embedding_result.embeddings) != len(chunks):
                raise RAGError("Mismatch between chunks and embeddings")
            
            # 5. Store in vector store
            await self.vector_store.add(
                chunks=chunks,
                embeddings=embedding_result.embeddings,
                metadata={"source_id": source_id, "document_id": str(document_id), **(metadata or {})}
            )
            
            # 6. Persist chunks in database
            async with get_db() as session:
                repo = RagDocumentRepository(session)
                
                chunks_data = [
                    {
                        "idx": chunk.idx,
                        "content": chunk.content,
                        "content_hash": chunk.content_hash,
                    }
                    for chunk in chunks
                ]
                
                await repo.bulk_insert_chunks(document_id, chunks_data)
            
            logger.info(
                "Document ingestion completed",
                source_id=source_id,
                document_id=str(document_id),
                num_chunks=len(chunks),
                tokens_used=embedding_result.token_usage
            )
            
            return {
                "document_id": str(document_id),
                "chunks": len(chunks),
                "status": "success"
            }
            
        except Exception as e:
            record_pipeline_error(type(e).__name__, "ingestion")
            logger.error("Document ingestion failed", source_id=source_id, error=str(e))
            raise RAGError(f"Ingestion failed: {e}") from e
    
    async def answer(self, query: str) -> AnswerResult:
        """
        Generate an answer for a query using the RAG pipeline.
        
        Process: check answer cache -> retrieve -> prompt build -> generate -> store in cache
        
        Args:
            query: User query string
            
        Returns:
            AnswerResult with answer and sources
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Sanitize query
            sanitized_query = sanitize_user_query(query)
            if not sanitized_query:
                raise ValueError("Query is empty after sanitization")
            
            logger.info("Processing query", query_length=len(sanitized_query))
            
            # Check answer cache first
            cached_answer = await self.answer_cache.get(
                sanitized_query, 
                self.prompt_builder.prompt_version
            )
            if cached_answer:
                logger.info("Answer cache hit", query_length=len(sanitized_query))
                return cached_answer
            
            # Retrieve relevant chunks
            async with time_retrieval():
                retrieved_chunks = await self.retriever.retrieve(sanitized_query)
            
            if not retrieved_chunks:
                logger.warning("No relevant chunks found", query=sanitized_query)
                return AnswerResult(
                    answer="I don't have enough relevant information to answer this question.",
                    sources=[],
                    metadata={"reason": "no_relevant_chunks"}
                )
            
            # Check context quality
            context_quality = check_context_quality(retrieved_chunks)
            logger.debug("Context quality assessment", **context_quality)
            
            # Build prompt
            prompt_parts = self.prompt_builder.build_prompt(
                sanitized_query, 
                retrieved_chunks
            )
            
            # Generate answer
            async with time_generation():
                generation_result = await self.llm_generator.generate(prompt_parts)
            
            # Prepare sources
            sources = [
                {
                    "source_id": chunk.source_id or "unknown",
                    "score": chunk.score,
                    "content_preview": chunk.chunk.content[:200] + "..." if len(chunk.chunk.content) > 200 else chunk.chunk.content
                }
                for chunk in retrieved_chunks
            ]
            
            # Create answer result
            answer_result = AnswerResult(
                answer=generation_result.text,
                sources=sources,
                metadata={
                    "prompt_version": prompt_parts.prompt_version,
                    "num_chunks": len(retrieved_chunks),
                    "context_quality": context_quality,
                    "tokens_in": generation_result.tokens_in,
                    "tokens_out": generation_result.tokens_out,
                    "model": generation_result.model
                }
            )
            
            # Cache the answer
            await self.answer_cache.set(
                sanitized_query,
                prompt_parts.prompt_version,
                answer_result,
                ttl=self.settings.rag_answer_cache_ttl_seconds
            )
            
            # Log metrics
            log_pipeline_metrics(
                query=sanitized_query,
                num_retrieved=len(retrieved_chunks),
                num_filtered=len(retrieved_chunks),  # Already filtered in retriever
                min_similarity=min(chunk.score for chunk in retrieved_chunks),
                context_tokens=self.prompt_builder.estimate_token_count(prompt_parts),
                cache_hits={"answer": False, "embedding": False}  # TODO: Track embedding cache hits
            )
            
            logger.info(
                "Query processing completed",
                query_length=len(sanitized_query),
                answer_length=len(answer_result.answer),
                num_sources=len(sources)
            )
            
            return answer_result
            
        except LowSimilarityError:
            # This is expected and should be handled gracefully
            logger.info("Low similarity - no relevant content found", query=query)
            raise
            
        except Exception as e:
            record_pipeline_error(type(e).__name__, "answer")
            logger.error("Query processing failed", query=query, error=str(e))
            raise RAGError(f"Answer generation failed: {e}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on pipeline components.
        
        Returns:
            Health status of all components
        """
        health = {
            "status": "healthy",
            "components": {}
        }
        
        try:
            # Test embedder
            test_result = await self.embedder.embed_texts(["test"])
            health["components"]["embedder"] = {
                "status": "healthy" if test_result.embeddings else "error",
                "model": self.embedder.model_name,
                "dimension": self.embedder.embedding_dimension
            }
        except Exception as e:
            health["components"]["embedder"] = {"status": "error", "error": str(e)}
            health["status"] = "degraded"
        
        # Add other component health checks as needed
        health["components"]["vector_store"] = {"status": "unknown"}  # TODO: Implement
        health["components"]["database"] = {"status": "unknown"}  # TODO: Implement
        
        return health