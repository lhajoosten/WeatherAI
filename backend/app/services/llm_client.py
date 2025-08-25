import logging
import time
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.db.repositories import LLMAuditRepository

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client wrapper with audit logging and mock fallback."""

    def __init__(self, audit_repo: LLMAuditRepository, openai_client: AsyncOpenAI | None = None):
        self.audit_repo = audit_repo
        self.openai_client = openai_client
        self.model = settings.openai_model
        self.has_openai_key = settings.openai_api_key is not None

        if not self.has_openai_key:
            logger.warning("No OpenAI API key provided - using mock responses")

    async def generate(
        self,
        prompt: str,
        user_id: int | None = None,
        endpoint: str = "generate",
        temperature: float = 0.0,
        max_tokens: int = 400,
        prompt_version: str | None = None,
        location_id: int | None = None
    ) -> dict[str, Any]:
        """Generate LLM response with audit logging.

        Args:
            prompt: The prompt to send to the LLM
            user_id: User ID for audit logging (optional)
            endpoint: Endpoint name for audit logging
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            prompt_version: Version of prompt template used (optional)
            location_id: Location ID for context (optional)

        Returns:
            Dict with text, tokens_in, tokens_out, and model
        """
        start_time = time.time()

        # Truncate prompt for audit logging (no PII)
        prompt_summary = prompt[:200]

        try:
            if self.has_openai_key and self.openai_client:
                # Real OpenAI call
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                content = response.choices[0].message.content or ""
                tokens_in = response.usage.prompt_tokens if response.usage else 0
                tokens_out = response.usage.completion_tokens if response.usage else 0

            else:
                # Mock response when no OpenAI key
                logger.info("Using mock LLM response")
                content = self._generate_mock_response(prompt)
                tokens_in = len(prompt.split()) * 1.3  # Rough estimate
                tokens_out = len(content.split()) * 1.3
                tokens_in = int(tokens_in)
                tokens_out = int(tokens_out)

            duration = time.time() - start_time

            # Record audit log - defensive against schema issues
            try:
                await self.audit_repo.record(
                    user_id=user_id,
                    endpoint=endpoint,
                    model=self.model,
                    prompt_summary=prompt_summary,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost=None  # TODO: Implement cost calculation
                )
            except Exception as audit_error:
                logger.warning(
                    "Failed to record LLM audit log",
                    extra={
                        "error": str(audit_error),
                        "endpoint": endpoint,
                        "user_id": user_id,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out
                    }
                )

            logger.info(
                "LLM call completed",
                extra={
                    "endpoint": endpoint,
                    "model": self.model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "duration_ms": int(duration * 1000),
                    "user_id": user_id,
                }
            )

            return {
                "text": content,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "model": self.model
            }

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}", exc_info=True)
            # Fallback to mock response on error
            content = self._generate_mock_response(prompt, error_fallback=True)
            return {
                "text": content,
                "tokens_in": 50,
                "tokens_out": 100,
                "model": f"{self.model}-mock"
            }

    def _generate_mock_response(self, prompt: str, error_fallback: bool = False) -> str:
        """Generate a mock response for testing/demo purposes."""
        if error_fallback:
            return (
                "Summary: Weather service temporarily unavailable. Please try again later.\n\n"
                "Actions:\n"
                "- Check back in a few minutes\n"
                "- Use alternative weather sources\n"
                "- Contact support if issue persists\n\n"
                "Driver: Service error - using fallback response"
            )

        # Extract location info from prompt if possible
        location_hint = "your location"
        if "location" in prompt.lower() or "lat" in prompt.lower():
            location_hint = "the specified location"

        return (
            f"Summary: Clear skies and mild temperatures expected for {location_hint} "
            "over the next 24 hours. Comfortable conditions for outdoor activities.\n\n"
            "Actions:\n"
            "- Perfect weather for outdoor plans\n"
            "- Light layers recommended for temperature changes\n"
            "- Good visibility for driving or walking\n\n"
            "Driver: High pressure system bringing stable, pleasant conditions"
        )


def create_llm_client(audit_repo: LLMAuditRepository) -> LLMClient:
    """Factory function to create LLMClient with proper OpenAI client."""
    openai_client = None

    if settings.openai_api_key:
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    return LLMClient(audit_repo=audit_repo, openai_client=openai_client)
