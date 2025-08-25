"""Use cases for RAG (Retrieval-Augmented Generation) operations.

This module contains application use cases that orchestrate domain
and infrastructure components for RAG functionality.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from uuid import UUID

from app.domain.events import RAGQueryAnsweredEvent, DataIngestedEvent
from app.domain.exceptions import NotFoundError, ValidationError
from app.application.event_bus import get_event_bus
from app.core.logging import get_rag_logger
from app.core.metrics import record_rag_query, measure_time


logger = get_rag_logger(__name__)


class AskRAGQuestion:
    """Use case for asking questions to the RAG system."""
    
    def __init__(
        self,
        rag_pipeline,  # Infrastructure dependency
        document_repository,  # Infrastructure dependency
        uow_factory  # Infrastructure dependency
    ):
        self.rag_pipeline = rag_pipeline
        self.document_repository = document_repository
        self.uow_factory = uow_factory
        self.event_bus = get_event_bus()
    
    async def execute(
        self,
        user_id: str,
        query: str,
        max_sources: int = 5,
        min_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """Execute RAG question answering.
        
        Args:
            user_id: ID of the user asking the question
            query: The question to answer
            max_sources: Maximum number of source documents to retrieve
            min_similarity: Minimum similarity threshold for documents
            
        Returns:
            Dictionary with answer, sources, and metadata
            
        Raises:
            ValidationError: If query is invalid
            NotFoundError: If no relevant documents found
        """
        if not query.strip():
            raise ValidationError("Query cannot be empty")
        
        logger.info("Executing RAG query", user_id=user_id, query_length=len(query))
        
        with measure_time("rag.query", {"user_id": user_id}):
            # Retrieve relevant documents
            retrieved_docs = await self.rag_pipeline.retrieve(
                query=query,
                max_results=max_sources,
                min_similarity=min_similarity
            )
            
            if not retrieved_docs:
                raise NotFoundError("No relevant documents found for query")
            
            # Generate answer using retrieved context
            answer_result = await self.rag_pipeline.generate(
                query=query,
                context_docs=retrieved_docs
            )
            
            # Prepare response
            response = {
                "answer": answer_result.answer,
                "sources": [
                    {
                        "document_id": doc.document_id,
                        "similarity": doc.similarity,
                        "excerpt": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                    }
                    for doc in retrieved_docs
                ],
                "metadata": {
                    "query_length": len(query),
                    "answer_length": len(answer_result.answer),
                    "sources_count": len(retrieved_docs),
                    "model": getattr(answer_result, 'model', 'unknown')
                }
            }
            
            # Record metrics
            record_rag_query(
                query_length=len(query),
                retrieved_docs=len(retrieved_docs),
                response_length=len(answer_result.answer),
                duration_seconds=0  # Will be set by measure_time decorator
            )
            
            # Publish domain event
            event = RAGQueryAnsweredEvent(
                user_id=user_id,
                query=query,
                answer_length=len(answer_result.answer),
                sources_count=len(retrieved_docs)
            )
            self.event_bus.publish(event)
            
            logger.info(
                "RAG query completed",
                user_id=user_id,
                answer_length=len(answer_result.answer),
                sources_count=len(retrieved_docs)
            )
            
            return response


class IngestDocument:
    """Use case for ingesting documents into the RAG system."""
    
    def __init__(
        self,
        rag_pipeline,  # Infrastructure dependency
        document_repository,  # Infrastructure dependency
        uow_factory  # Infrastructure dependency
    ):
        self.rag_pipeline = rag_pipeline
        self.document_repository = document_repository
        self.uow_factory = uow_factory
        self.event_bus = get_event_bus()
    
    async def execute(
        self,
        source_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute document ingestion.
        
        Args:
            source_id: Unique identifier for the document source
            text: Document text content
            metadata: Optional metadata for the document
            
        Returns:
            Dictionary with ingestion results
            
        Raises:
            ValidationError: If document data is invalid
        """
        if not source_id.strip():
            raise ValidationError("Source ID cannot be empty")
        
        if not text.strip():
            raise ValidationError("Document text cannot be empty")
        
        logger.info("Ingesting document", source_id=source_id, text_length=len(text))
        
        async with self.uow_factory() as uow:
            # Check if document already exists
            existing = await self.document_repository.get_by_source_id(source_id)
            if existing:
                raise ValidationError(f"Document with source_id '{source_id}' already exists")
            
            # Process document through RAG pipeline
            document_result = await self.rag_pipeline.ingest(
                source_id=source_id,
                text=text,
                metadata=metadata or {}
            )
            
            # Store in repository
            repo = uow.get_repository(type(self.document_repository))
            document_id = await repo.create_document(
                source_id=source_id,
                text=text,
                metadata=metadata or {},
                chunks_count=len(document_result.chunks)
            )
            
            await uow.commit()
            
            # Publish domain event
            event = DataIngestedEvent(
                location_id=source_id,  # Using source_id as aggregate_id
                provider="rag_ingestion",
                data_type="document",
                record_count=len(document_result.chunks)
            )
            self.event_bus.publish(event)
            
            logger.info(
                "Document ingested successfully",
                source_id=source_id,
                document_id=document_id,
                chunks_count=len(document_result.chunks)
            )
            
            return {
                "document_id": document_id,
                "source_id": source_id,
                "chunks_count": len(document_result.chunks),
                "status": "success"
            }


class RetrieveDocuments:
    """Use case for retrieving documents by various criteria."""
    
    def __init__(self, document_repository, uow_factory):
        self.document_repository = document_repository
        self.uow_factory = uow_factory
    
    async def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        source_id_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute document retrieval.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            source_id_filter: Optional filter by source_id
            
        Returns:
            Dictionary with documents and pagination info
        """
        async with self.uow_factory() as uow:
            repo = uow.get_repository(type(self.document_repository))
            
            documents = await repo.list_documents(
                limit=limit,
                offset=offset,
                source_id_filter=source_id_filter
            )
            
            total_count = await repo.count_documents(source_id_filter)
            
            return {
                "documents": [
                    {
                        "id": doc.id,
                        "source_id": doc.source_id,
                        "text_preview": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat()
                    }
                    for doc in documents
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(documents) < total_count
                }
            }