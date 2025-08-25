"""LLM generation for RAG pipeline with Phase 4 resilience."""

import asyncio
import structlog
from typing import Dict, Any, Optional

from .models import PromptParts, GenerationResult
from app.domain.exceptions import InternalProcessingError
from app.core.constants import PROMPT_VERSION

logger = structlog.get_logger(__name__)


class LLMGenerator:
    """
    LLM generation with Phase 4 resilience enhancements.
    """
    
    def __init__(self, llm_client=None, max_retries: int = 2, base_delay: float = 1.0):
        """
        Initialize LLM generator with retry configuration.
        
        Args:
            llm_client: Existing LLM client instance
            max_retries: Maximum number of retries for failed requests (Phase 4: 2)
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.llm_client = llm_client
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        if self.llm_client is None:
            logger.warning("No LLM client provided - using mock implementation")
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Implements Phase 4 resilience requirements:
        - Retry 2x with exponential backoff
        - Handle provider 429/5xx errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a retryable error
                error_type = type(e).__name__
                error_message = str(e).lower()
                
                is_retryable = (
                    # Rate limiting (429)
                    "429" in error_message or "rate limit" in error_message or
                    # Server errors (5xx)
                    "500" in error_message or "502" in error_message or 
                    "503" in error_message or "504" in error_message or
                    "internal server error" in error_message or
                    "service unavailable" in error_message or
                    "timeout" in error_message or
                    # Connection issues
                    "connection" in error_message or
                    "network" in error_message
                )
                
                if not is_retryable or attempt >= self.max_retries:
                    logger.error(
                        "LLM generation failed - not retrying",
                        attempt=attempt,
                        max_retries=self.max_retries,
                        error_type=error_type,
                        is_retryable=is_retryable,
                        error=str(e)
                    )
                    break
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                
                logger.warning(
                    "LLM generation failed - retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                    error_type=error_type,
                    error=str(e)
                )
                
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise InternalProcessingError(
            f"LLM generation failed after {self.max_retries} retries",
            original_error=last_exception
        )
    
    async def generate(
        self, 
        prompt_parts: PromptParts,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> GenerationResult:
        """
        Generate response using LLM with Phase 4 resilience.
        
        Args:
            prompt_parts: Complete prompt components
            temperature: Generation temperature (0 = deterministic, 1 = creative)
            max_tokens: Maximum tokens to generate
            
        Returns:
            GenerationResult with response text and metadata
            
        Raises:
            InternalProcessingError: If generation fails after retries
        """
        
        async def _do_generation():
            """Internal generation function for retry logic."""
            if self.llm_client is None:
                # Mock implementation for development
                return self._mock_generate(prompt_parts)
            
            # TODO: Implement actual LLM client call
            # This should be updated once the actual LLM client interface is confirmed
            
            # Example of what the call might look like:
            # response = await self.llm_client.chat_completion(
            #     messages=[
            #         {"role": "system", "content": prompt_parts.system_prompt},
            #         {"role": "user", "content": prompt_parts.user_prompt}
            #     ],
            #     temperature=temperature,
            #     max_tokens=max_tokens
            # )
            
            # For now, return mock result
            return self._mock_generate(prompt_parts)
        
        # Execute with retry logic
        try:
            return await self._retry_with_backoff(_do_generation)
        except InternalProcessingError:
            # Already wrapped, re-raise
            raise
        except Exception as e:
            # Wrap other exceptions
            logger.error(
                "LLM generation failed",
                error=str(e),
                prompt_version=prompt_parts.prompt_version
            )
            raise InternalProcessingError(f"LLM generation failed: {e}", original_error=e)
    
    def _mock_generate(self, prompt_parts: PromptParts) -> GenerationResult:
        """
        Mock implementation for development and testing.
        
        Args:
            prompt_parts: Prompt components
            
        Returns:
            Mock GenerationResult
        """
        # Simple mock response based on context
        if "No relevant context" in prompt_parts.context:
            mock_text = "I don't have enough context to answer this question."
        else:
            mock_text = "Based on the provided context, here is a summary response. This is a mock implementation that should be replaced with actual LLM generation."
        
        return GenerationResult(
            text=mock_text,
            tokens_in=self._estimate_input_tokens(prompt_parts),
            tokens_out=len(mock_text.split()),
            model="mock-model",
            metadata={
                "prompt_version": prompt_parts.prompt_version or PROMPT_VERSION,
                "mock": True
            }
        )
    
    def _estimate_input_tokens(self, prompt_parts: PromptParts) -> int:
        """Estimate input token count."""
        total_text = prompt_parts.system_prompt + " " + prompt_parts.user_prompt
        return len(total_text.split())
    
    def estimate_cost(self, generation_result: GenerationResult) -> float:
        """
        Estimate cost of generation.
        
        TODO: Implement actual cost calculation based on model and token usage.
        
        Args:
            generation_result: Result from generation
            
        Returns:
            Estimated cost in USD
        """
        if not generation_result.tokens_in or not generation_result.tokens_out:
            return 0.0
        
        # Mock cost calculation - should be replaced with actual pricing
        # Example: GPT-4 pricing (as of 2024)
        input_cost_per_1k = 0.03  # $0.03 per 1K input tokens
        output_cost_per_1k = 0.06  # $0.06 per 1K output tokens
        
        input_cost = (generation_result.tokens_in / 1000) * input_cost_per_1k
        output_cost = (generation_result.tokens_out / 1000) * output_cost_per_1k
        
        return input_cost + output_cost