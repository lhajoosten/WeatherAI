"""Schema models for RAG streaming responses."""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel

from app.core.constants import RAGStreamEventType, PROMPT_VERSION


class StreamTokenEvent(BaseModel):
    """Token event for streaming responses."""
    type: Literal["token"] = RAGStreamEventType.TOKEN
    data: str


class StreamDoneEvent(BaseModel):
    """Done event for streaming responses."""
    type: Literal["done"] = RAGStreamEventType.DONE
    data: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        total_tokens: Optional[int] = None,
        sources_count: Optional[int] = None,
        guardrail: Optional[str] = None,
        prompt_version: str = PROMPT_VERSION
    ) -> "StreamDoneEvent":
        """Create a done event with standard metadata."""
        data = {"prompt_version": prompt_version}
        
        if total_tokens is not None:
            data["total_tokens"] = total_tokens
        if sources_count is not None:
            data["sources_count"] = sources_count
        if guardrail is not None:
            data["guardrail"] = guardrail
            
        return cls(data=data)


class StreamErrorEvent(BaseModel):
    """Error event for streaming responses."""
    type: Literal["error"] = RAGStreamEventType.ERROR
    data: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> "StreamErrorEvent":
        """Create an error event with standard structure."""
        data = {
            "error_code": error_code,
            "message": message,
            "prompt_version": PROMPT_VERSION
        }
        
        if details:
            data.update(details)
            
        return cls(data=data)


class StreamQueryRequest(BaseModel):
    """Request model for streaming RAG queries."""
    query: str
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the latest weather patterns affecting crops?"
            }
        }