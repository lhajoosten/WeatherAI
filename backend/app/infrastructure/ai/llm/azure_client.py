"""Azure OpenAI client for morning digest generation.

This module provides a specialized interface for generating morning digest summaries
using Azure OpenAI, with retry logic, JSON validation, and proper error handling.
"""

import json
import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings
from app.infrastructure.ai.llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMResult(BaseModel):
    """Result from LLM generation with metadata."""
    content: str = Field(..., description="Generated content")
    tokens_in: int = Field(..., description="Input tokens consumed")
    tokens_out: int = Field(..., description="Output tokens generated")
    model: str = Field(..., description="Model used for generation")
    duration_ms: int = Field(..., description="Generation duration in milliseconds")
    cost_usd: float | None = Field(None, description="Estimated cost in USD")


class DigestSummary(BaseModel):
    """Parsed digest summary from LLM output."""
    narrative: str = Field(..., description="Main summary narrative")
    bullets: list[dict[str, Any]] = Field(..., description="Bullet points")
    driver: str = Field(..., description="Main weather driver")


class AzureDigestClient:
    """Azure OpenAI client specialized for morning digest generation."""

    def __init__(self, llm_client: LLMClient):
        """Initialize with base LLM client.

        Args:
            llm_client: Base LLM client for OpenAI interactions
        """
        self.llm_client = llm_client
        self.model = settings.openai_model
        self.temperature = 0.1  # Low for factual, consistent responses
        self.max_tokens = 500   # Sufficient for digest JSON response
        self.max_retries = 3

    async def generate_digest_summary(
        self,
        context: dict[str, Any],
        prompt: str,
        user_id: int | None = None,
        location_id: int | None = None
    ) -> LLMResult:
        """Generate digest summary from structured context.

        Args:
            context: Structured context dictionary for the digest
            prompt: Complete prompt with context embedded
            user_id: Optional user ID for audit logging
            location_id: Optional location ID for audit logging

        Returns:
            LLMResult with generated content and metadata

        Raises:
            DigestGenerationError: If generation fails after retries
            ValidationError: If LLM output doesn't match expected format
        """
        logger.info(
            "Starting digest generation",
            extra={
                "model": self.model,
                "user_id": user_id,
                "location_id": location_id
            }
        )

        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{self.max_retries}")

                # Call base LLM client
                result = await self.llm_client.generate(
                    prompt=prompt,
                    user_id=user_id,
                    endpoint="morning_digest",
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    prompt_version="morning_digest_v1",
                    location_id=location_id
                )

                # Validate and parse JSON response
                content = result["text"]
                parsed_summary = self._parse_and_validate_response(content)

                # Calculate duration
                duration_ms = max(1, int((time.time() - start_time) * 1000))  # Ensure at least 1ms

                # Estimate cost (rough approximation based on OpenAI pricing)
                estimated_cost = self._estimate_cost(
                    result.get("tokens_in", 0),
                    result.get("tokens_out", 0),
                    result.get("model", self.model)
                )

                logger.info(
                    "Digest generation successful",
                    extra={
                        "attempt": attempt + 1,
                        "duration_ms": duration_ms,
                        "tokens_in": result.get("tokens_in", 0),
                        "tokens_out": result.get("tokens_out", 0)
                    }
                )

                return LLMResult(
                    content=content,
                    tokens_in=result.get("tokens_in", 0),
                    tokens_out=result.get("tokens_out", 0),
                    model=result.get("model", self.model),
                    duration_ms=duration_ms,
                    cost_usd=estimated_cost
                )

            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON response: {e}"
                preview = None
                raw_content = locals().get('content')
                if isinstance(raw_content, str):
                    preview = raw_content[:200]
                logger.warning(
                    "JSON parsing failed, retrying",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(e),
                        "content_preview": preview
                    }
                )

            except Exception as e:
                last_error = f"Generation error: {e}"
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 1 * (2 ** attempt)  # 1s, 2s, 4s
                logger.debug(f"Waiting {wait_time}s before retry")
                await self._async_sleep(wait_time)

        # All retries failed
        logger.error(
            f"Digest generation failed after all retries: {self.max_retries} attempts, "
            f"final_error: {last_error}"
        )

        from app.core.exceptions import DigestGenerationError
        raise DigestGenerationError(f"Failed to generate digest after {self.max_retries} attempts: {last_error}")

    def _parse_and_validate_response(self, content: str) -> DigestSummary:
        """Parse and validate LLM response JSON.

        Args:
            content: Raw LLM response content

        Returns:
            Parsed and validated DigestSummary

        Raises:
            json.JSONDecodeError: If content is not valid JSON
            ValidationError: If JSON doesn't match expected schema
        """
        # Parse JSON
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from content if wrapped in text
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(content[start:end])
            else:
                raise e

        # Validate required fields
        required_fields = ["narrative", "bullets", "driver"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")

        # Validate bullets structure
        bullets = parsed["bullets"]
        if not isinstance(bullets, list) or len(bullets) != 3:
            raise ValueError(f"Expected exactly 3 bullets, got {len(bullets) if isinstance(bullets, list) else 'non-list'}")

        for i, bullet in enumerate(bullets):
            if not isinstance(bullet, dict):
                raise ValueError(f"Bullet {i} is not a dictionary")

            required_bullet_fields = ["text", "category", "priority"]
            for field in required_bullet_fields:
                if field not in bullet:
                    raise ValueError(f"Bullet {i} missing required field: {field}")

            # Validate category
            valid_categories = {"weather", "activity", "alert"}
            if bullet["category"] not in valid_categories:
                raise ValueError(f"Bullet {i} has invalid category: {bullet['category']}")

            # Validate priority
            if bullet["priority"] not in [1, 2, 3]:
                raise ValueError(f"Bullet {i} has invalid priority: {bullet['priority']}")

        return DigestSummary(**parsed)

    def _estimate_cost(self, tokens_in: int, tokens_out: int, model: str) -> float:
        """Estimate cost in USD based on token usage.

        Args:
            tokens_in: Input tokens
            tokens_out: Output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        # Rough cost estimates (as of 2024) - update as needed
        cost_per_1k_tokens = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }

        # Default to gpt-4 pricing if model not found
        model_costs = cost_per_1k_tokens.get(model, cost_per_1k_tokens["gpt-4"])

        input_cost = (tokens_in / 1000) * model_costs["input"]
        output_cost = (tokens_out / 1000) * model_costs["output"]

        return round(input_cost + output_cost, 6)

    async def _async_sleep(self, seconds: float) -> None:
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)


def create_azure_digest_client(llm_client: LLMClient) -> AzureDigestClient:
    """Factory function to create AzureDigestClient.

    Args:
        llm_client: Base LLM client instance

    Returns:
        Configured AzureDigestClient
    """
    return AzureDigestClient(llm_client)
