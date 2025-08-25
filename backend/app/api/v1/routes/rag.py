"""RAG API endpoints for document ingestion and querying."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
import structlog

from app.ai.rag.pipeline import RAGPipeline
from app.ai.rag.exceptions import RAGError, LowSimilarityError, EmptyContextError
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

# Global pipeline instance - in production, consider dependency injection
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


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
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
) -> IngestResponse:
    """Ingest a document into the RAG system."""
    try:
        logger.info(
            "Document ingestion request",
            source_id=request.source_id,
            text_length=len(request.text)
        )
        
        result = await pipeline.ingest(
            source_id=request.source_id,
            text=request.text,
            metadata=request.metadata
        )
        
        return IngestResponse(
            document_id=result["document_id"],
            chunks=result["chunks"],
            status=result["status"]
        )
        
    except ValueError as e:
        logger.warning("Invalid ingestion request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RAGError as e:
        logger.error("RAG ingestion error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected ingestion error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during ingestion"
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
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Query the RAG system for an answer."""
    try:
        logger.info("RAG query request", query_length=len(request.query))
        
        result = await pipeline.answer(request.query)
        
        # Convert sources to DTO format
        sources = [
            SourceDTO(
                source_id=source["source_id"],
                score=source["score"],
                content_preview=source.get("content_preview")
            )
            for source in result.sources
        ]
        
        response = QueryResponse(
            answer=result.answer,
            sources=sources,
            metadata=result.metadata
        )
        
        logger.info(
            "RAG query completed",
            query_length=len(request.query),
            answer_length=len(result.answer),
            num_sources=len(sources)
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid query request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LowSimilarityError as e:
        logger.info("Low similarity - returning 204", error=str(e))
        # Return 204 No Content as specified in requirements
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RAGError as e:
        logger.error("RAG query error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected query error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during query"
        )


@router.get(
    "/health",
    summary="RAG system health check",
    description="Check the health status of RAG pipeline components"
)
async def rag_health_check(
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Check RAG system health."""
    try:
        health = await pipeline.health_check()
        
        # Return appropriate status code based on health
        if health["status"] == "healthy":
            return health
        else:
            # Return 503 Service Unavailable for degraded service
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health
            )
            
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": str(e)}
        )