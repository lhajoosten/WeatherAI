"""RAG API endpoints for document ingestion and querying."""

from fastapi import APIRouter, Depends, status
import structlog

from app.services.rag_service import RAGService
from app.api.dependencies import get_rag_service
from app.schemas.rag import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    ErrorResponse,
    SourceDTO
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a document into the RAG system",
    description="""
    Ingest a text document into the RAG system for later retrieval.
    
    The document will be:
    1. Cleaned and normalized
    2. Split into chunks
    3. Embedded using Azure OpenAI
    4. Stored in the vector database
    5. Persisted in the main database
    
    Returns the document ID and number of chunks created.
    """
)
async def ingest_document(
    request: IngestRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> IngestResponse:
    """Ingest a document into the RAG system."""
    result = await rag_service.ingest_document(
        source_id=request.source_id,
        text=request.text,
        metadata=request.metadata
    )
    
    return IngestResponse(
        document_id=result["document_id"],
        chunks=result["chunks"],
        status=result["status"]
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        200: {"description": "Answer found with relevant sources"},
        204: {"description": "No relevant content found - low similarity"},
        400: {"description": "Invalid query"},
        500: {"description": "Internal server error"}
    },
    summary="Query the RAG system for an answer",
    description="""
    Query the RAG system to get an answer based on ingested documents.
    
    The system will:
    1. Sanitize and validate the query
    2. Generate embeddings for the query
    3. Retrieve relevant document chunks
    4. Apply similarity filtering and MMR re-ranking
    5. Generate an answer using the LLM
    6. Return the answer with source citations
    
    Returns 204 No Content if no relevant documents are found (all below similarity threshold).
    """
)
async def query_documents(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Query the RAG system for an answer."""
    result = await rag_service.query(request.query)
    
    # Convert sources to DTO format
    sources = [
        SourceDTO(
            source_id=source["source_id"],
            score=source["score"],
            content_preview=source.get("content_preview")
        )
        for source in result.sources
    ]
    
    return QueryResponse(
        answer=result.answer,
        sources=sources,
        metadata=result.metadata
    )


@router.get(
    "/health",
    summary="RAG system health check",
    description="Check the health status of RAG pipeline components"
)
async def rag_health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Check RAG system health."""
    health = await rag_service.health_check()
    
    # Return appropriate status code based on health
    if health["status"] == "healthy":
        return health
    else:
        # Return 503 Service Unavailable for degraded service
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health
        )