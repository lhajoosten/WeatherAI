"""RAG API endpoints for document ingestion and querying."""

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
import structlog

from app.api.dependencies import get_rag_pipeline, get_ingest_document_use_case, get_ask_rag_question_use_case
from app.application.rag_use_cases import IngestDocument, AskRAGQuestion
from app.application.dto.rag import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceDTO
)
from app.application.dto.rag_stream import StreamQueryRequest
from app.infrastructure.ai.rag.pipeline import RAGPipeline
from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
from app.domain.exceptions import (
    RateLimitExceededError,
    QueryValidationError
)
from app.core.constants import DomainErrorCode

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
    ingest_use_case: IngestDocument = Depends(get_ingest_document_use_case)
) -> IngestResponse:
    """Ingest a document into the RAG system."""
    result = await ingest_use_case.execute(
        source_id=request.source_id,
        text=request.text,
        metadata=request.metadata or {}
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
    ask_rag_use_case: AskRAGQuestion = Depends(get_ask_rag_question_use_case)
):
    """Query the RAG system for an answer."""
    result = await ask_rag_use_case.execute(
        user_id="anonymous",  # TODO: Extract from authentication
        query=request.query,
        max_sources=getattr(request, 'max_sources', 5),
        min_similarity=getattr(request, 'min_similarity', 0.7)
    )
    
    # Convert sources to DTO format
    sources = [
        SourceDTO(
            source_id=source["document_id"],
            score=source["similarity"],
            content_preview=source.get("excerpt")
        )
        for source in result["sources"]
    ]
    
    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        metadata=result.get("metadata", {})
    )


@router.post(
    "/stream",
    summary="Stream RAG answer with real-time tokens",
    description="""
    Stream a RAG answer in real-time using Server-Sent Events (SSE).
    
    Returns text/event-stream with three event types:
    - token: Individual tokens of the answer
    - done: Final event with metadata (sources count, prompt version, etc.)
    - error: Error event with error code and details
    
    Rate limited to 20 requests per 5 minutes per user.
    Query length limited to 2000 characters.
    
    Implements guardrails with similarity threshold fallback.
    """,
    responses={
        200: {
            "description": "Streaming response",
            "content": {"text/event-stream": {}}
        },
        400: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def stream_rag_answer(
    request: StreamQueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Stream RAG answer with Server-Sent Events."""
    
    # Create streaming service
    streaming_service = RAGStreamingService(pipeline)
    
    # Define the streaming response generator
    async def event_stream():
        try:
            async for event_data in streaming_service.stream_answer(
                query=request.query,
                user_id=None,  # TODO: Extract from auth when available
                trace_id=None  # TODO: Generate trace ID
            ):
                yield event_data
        except RateLimitExceededError as e:
            # Rate limit error - return 429 status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": DomainErrorCode.RATE_LIMITED,
                    "message": str(e),
                    "limit": e.limit,
                    "window_seconds": e.window_seconds
                }
            )
        except QueryValidationError as e:
            # Validation error - return 400 status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": DomainErrorCode.VALIDATION_ERROR,
                    "message": str(e),
                    **e.extra_data
                }
            )
        except Exception as e:
            logger.error("Streaming endpoint error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": DomainErrorCode.INTERNAL_ERROR,
                    "message": "An internal error occurred"
                }
            )
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get(
    "/health",
    summary="RAG system health check",
    description="Check the health status of RAG pipeline components"
)
async def rag_health_check(
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Check RAG system health using pipeline directly."""
    try:
        pipeline_health = await pipeline.health_check()
        return {
            "status": "healthy",
            "pipeline": pipeline_health,
            "service": "operational"
        }
    except Exception as e:  # pragma: no cover
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "service": "degraded"
            }
        )