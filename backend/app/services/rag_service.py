"""RAG service orchestrating pipeline and repository operations."""

from typing import Dict, Any
from uuid import UUID
import structlog

from app.ai.rag.pipeline import RAGPipeline
from app.ai.rag.models import AnswerResult
from app.ai.rag.exceptions import RAGError
from app.repositories.rag import RagDocumentRepository
from app.repositories.base import UnitOfWork
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError

logger = structlog.get_logger(__name__)


class RAGService:
    """Service orchestrating RAG pipeline operations and document persistence."""
    
    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline
    
    async def ingest_document(
        self, 
        source_id: str, 
        text: str, 
        metadata: Dict[str, Any] = None,
        uow: UnitOfWork = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG system.
        
        Args:
            source_id: Unique identifier for the document
            text: Document text content
            metadata: Optional metadata dictionary
            uow: Unit of Work for transaction management
            
        Returns:
            Dictionary with document_id, chunks count, and status
            
        Raises:
            ConflictError: If document with source_id already exists
            ServiceUnavailableError: If pipeline operations fail
        """
        logger.info("[RAG] [SERVICE] Starting document ingestion", source_id=source_id, text_length=len(text))
        
        try:
            # Use UoW if provided, otherwise create our own
            if uow:
                return await self._ingest_with_uow(source_id, text, metadata, uow)
            else:
                from app.repositories.base import get_uow
                async with get_uow() as uow:
                    return await self._ingest_with_uow(source_id, text, metadata, uow)
                    
        except RAGError as e:
            logger.error("[RAG] [SERVICE] Pipeline error during ingestion", 
                        source_id=source_id, error=str(e))
            raise ServiceUnavailableError("RAG Pipeline", details=str(e))
        except Exception as e:
            logger.error("[RAG] [SERVICE] Unexpected error during ingestion", 
                        source_id=source_id, error=str(e), exc_info=True)
            raise ServiceUnavailableError("RAG Service", details="Ingestion failed")
    
    async def _ingest_with_uow(
        self, 
        source_id: str, 
        text: str, 
        metadata: Dict[str, Any] = None,
        uow: UnitOfWork = None
    ) -> Dict[str, Any]:
        """Internal method to handle ingestion with UoW."""
        rag_repo = uow.get_repository(RagDocumentRepository)
        
        # Check if document already exists
        existing_doc = await rag_repo.get_by_source_id(source_id)
        if existing_doc:
            raise ConflictError(
                "Document already exists", 
                details=f"Document with source_id '{source_id}' already exists"
            )
        
        # Process through RAG pipeline
        pipeline_result = await self.pipeline.ingest(source_id, text, metadata)
        
        # Pipeline should have already created the document and chunks
        # Verify the document exists
        document = await rag_repo.get_by_source_id(source_id)
        if not document:
            raise ServiceUnavailableError(
                "RAG Pipeline", 
                details="Pipeline completed but document not found in database"
            )
        
        logger.info("[RAG] [SERVICE] Document ingestion completed", 
                   source_id=source_id, 
                   document_id=str(document.id),
                   chunks=pipeline_result.get("chunks", 0),
                   status="success")
        
        return {
            "document_id": str(document.id),
            "chunks": pipeline_result.get("chunks", 0),
            "status": "success"
        }
    
    async def query(self, query: str) -> AnswerResult:
        """
        Query the RAG system for an answer.
        
        Args:
            query: User query string
            
        Returns:
            AnswerResult with answer and sources
            
        Raises:
            ServiceUnavailableError: If pipeline operations fail
        """
        logger.info("[RAG] [SERVICE] Processing query", query_length=len(query))
        
        try:
            result = await self.pipeline.answer(query)
            
            logger.info("[RAG] [SERVICE] Query completed", 
                       query_length=len(query),
                       sources_count=len(result.sources) if result.sources else 0,
                       status="success")
            
            return result
            
        except RAGError as e:
            logger.error("[RAG] [SERVICE] Pipeline error during query", 
                        query_length=len(query), error=str(e))
            raise ServiceUnavailableError("RAG Pipeline", details=str(e))
        except Exception as e:
            logger.error("[RAG] [SERVICE] Unexpected error during query", 
                        query_length=len(query), error=str(e), exc_info=True)
            raise ServiceUnavailableError("RAG Service", details="Query failed")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the RAG service and pipeline.
        
        Returns:
            Health status dictionary
        """
        try:
            pipeline_health = await self.pipeline.health_check()
            
            return {
                "status": "healthy",
                "pipeline": pipeline_health,
                "service": "operational"
            }
        except Exception as e:
            logger.error("[RAG] [SERVICE] Health check failed", error=str(e))
            return {
                "status": "unhealthy", 
                "error": str(e),
                "service": "degraded"
            }