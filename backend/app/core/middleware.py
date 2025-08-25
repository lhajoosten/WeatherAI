"""Unified observability middleware for WeatherAI.

This module provides FastAPI middleware that adds correlation IDs, timing,
metrics, and tracing to all HTTP requests.
"""

from __future__ import annotations

import time
from typing import Callable, Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    set_correlation_id, 
    generate_request_id, 
    get_correlation_context,
    get_logger
)
from app.core.metrics import record_metric, is_prometheus_enabled
from app.core.tracing import get_current_trace_id, add_span_attribute

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that adds observability to all HTTP requests.
    
    This middleware:
    1. Generates and sets correlation IDs (request_id, trace_id)
    2. Measures request duration and records metrics
    3. Logs request/response information
    4. Adds tracing attributes
    5. Handles user context extraction
    """
    
    def __init__(
        self,
        app,
        service_name: str = "weatherai-backend",
        log_requests: bool = True,
        log_responses: bool = True,
        exclude_paths: list[str] | None = None
    ):
        """Initialize observability middleware.
        
        Args:
            app: FastAPI application
            service_name: Service name for metrics and logs
            log_requests: Whether to log incoming requests
            log_responses: Whether to log outgoing responses  
            exclude_paths: List of paths to exclude from observability (e.g., health checks)
        """
        super().__init__(app)
        self.service_name = service_name
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics"])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with full observability."""
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate correlation IDs
        request_id = self._extract_or_generate_request_id(request)
        trace_id = get_current_trace_id() or request_id  # Use OpenTel trace ID if available
        user_id = self._extract_user_id(request)
        
        # Set correlation context
        set_correlation_id(request_id=request_id, trace_id=trace_id, user_id=user_id)
        
        # Add to request state for access in route handlers
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.user_id = user_id
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        if self.log_requests:
            self._log_request(request)
        
        # Add tracing attributes
        self._add_tracing_attributes(request, user_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            self._record_metrics(request, response, duration)
            
            # Add response headers
            self._add_response_headers(response, request_id, trace_id)
            
            # Log response
            if self.log_responses:
                self._log_response(request, response, duration)
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests too
            duration = time.time() - start_time
            
            # Record error metrics
            self._record_error_metrics(request, e, duration)
            
            # Log error
            logger.error(
                "Request failed",
                path=request.url.path,
                method=request.method,
                duration_seconds=duration,
                error_type=type(e).__name__,
                error_message=str(e),
                component="api"
            )
            
            # Re-raise the exception
            raise
    
    def _extract_or_generate_request_id(self, request: Request) -> str:
        """Extract request ID from headers or generate a new one."""
        # Try to extract from common header names
        for header in ["x-request-id", "request-id", "x-correlation-id"]:
            if request_id := request.headers.get(header):
                return request_id
        
        # Generate new request ID
        return generate_request_id()
    
    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from request context if available."""
        # This would typically extract from JWT token or session
        # For now, return None - can be enhanced based on auth implementation
        return None
    
    def _add_tracing_attributes(self, request: Request, user_id: str | None) -> None:
        """Add attributes to current tracing span."""
        add_span_attribute("http.method", request.method)
        add_span_attribute("http.url", str(request.url))
        add_span_attribute("http.scheme", request.url.scheme)
        add_span_attribute("http.host", request.url.hostname or "unknown")
        add_span_attribute("http.target", request.url.path)
        add_span_attribute("service.name", self.service_name)
        
        if user_id:
            add_span_attribute("user.id", user_id)
        
        # Add query parameters (excluding sensitive ones)
        if request.query_params:
            # Filter out potentially sensitive parameters
            filtered_params = {
                k: v for k, v in request.query_params.items() 
                if k.lower() not in ["password", "token", "secret", "key"]
            }
            if filtered_params:
                add_span_attribute("http.query", str(filtered_params))
    
    def _record_metrics(self, request: Request, response: Response, duration: float) -> None:
        """Record request metrics."""
        method = request.method
        path = request.url.path
        status_code = str(response.status_code)
        
        # Basic HTTP metrics
        record_metric(
            "http.requests.total",
            1,
            {"method": method, "endpoint": path, "status_code": status_code}
        )
        
        record_metric(
            "http.request.duration_seconds",
            duration,
            {"method": method, "endpoint": path}
        )
        
        # Status code category metrics
        status_category = f"{status_code[0]}xx"
        record_metric(
            "http.responses.total",
            1,
            {"method": method, "status_category": status_category}
        )
        
        # Error rate metrics
        if response.status_code >= 400:
            record_metric(
                "http.errors.total",
                1,
                {"method": method, "status_code": status_code}
            )
    
    def _record_error_metrics(self, request: Request, error: Exception, duration: float) -> None:
        """Record metrics for request errors."""
        method = request.method
        path = request.url.path
        error_type = type(error).__name__
        
        record_metric(
            "http.requests.total",
            1,
            {"method": method, "endpoint": path, "status_code": "500"}
        )
        
        record_metric(
            "http.request.duration_seconds",
            duration,
            {"method": method, "endpoint": path}
        )
        
        record_metric(
            "http.exceptions.total",
            1,
            {"method": method, "exception_type": error_type}
        )
    
    def _add_response_headers(self, response: Response, request_id: str, trace_id: str) -> None:
        """Add observability headers to response."""
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = trace_id
    
    def _log_request(self, request: Request) -> None:
        """Log incoming request details."""
        correlation = get_correlation_context()
        
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
            content_length=request.headers.get("content-length"),
            component="api",
            **correlation
        )
    
    def _log_response(self, request: Request, response: Response, duration: float) -> None:
        """Log response details."""
        correlation = get_correlation_context()
        
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 4),
            response_size=response.headers.get("content-length"),
            component="api",
            **correlation
        )


def get_request_correlation(request: Request) -> dict[str, str | None]:
    """Extract correlation IDs from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with correlation IDs
    """
    return {
        "request_id": getattr(request.state, "request_id", None),
        "trace_id": getattr(request.state, "trace_id", None),
        "user_id": getattr(request.state, "user_id", None),
    }