"""Metrics scaffolding for digest operations.

This module defines Prometheus-style instruments for monitoring digest
generation performance, cache behavior, and error rates. In PR1, this
provides a foundation for observability without requiring a full metrics
infrastructure.
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class DigestMetrics:
    """Metrics collector for digest operations.

    This class provides a simple metrics interface that can be easily
    upgraded to use Prometheus or other metrics systems in the future.
    """

    def __init__(self):
        """Initialize metrics collector."""
        # Simple counters and histograms (in-memory for PR1)
        self._counters: dict[str, int] = {}
        self._histograms: dict[str, list] = {}
        # Track token usage for averaging
        self._token_usage_history: list[int] = []
        # Track digest opens for daily rate calculation
        self._daily_opens: dict[str, int] = {}  # date -> count

    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            labels: Optional labels dictionary
        """
        key = self._build_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + 1

        logger.debug(
            "Counter incremented",
            action="digest_metrics.counter",
            metric=name,
            labels=labels or {},
            value=self._counters[key]
        )

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
            labels: Optional labels dictionary
        """
        key = self._build_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

        logger.debug(
            "Histogram value recorded",
            action="digest_metrics.histogram",
            metric=name,
            labels=labels or {},
            value=value
        )

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        """Get current counter value.

        Args:
            name: Counter name
            labels: Optional labels dictionary

        Returns:
            Current counter value
        """
        key = self._build_key(name, labels)
        return self._counters.get(key, 0)

    def get_histogram_stats(self, name: str, labels: dict[str, str] | None = None) -> dict[str, float]:
        """Get histogram statistics.

        Args:
            name: Histogram name
            labels: Optional labels dictionary

        Returns:
            Dictionary with min, max, avg, count statistics
        """
        key = self._build_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics for inspection/debugging.

        Returns:
            Dictionary with all counters, histogram stats, and derived metrics
        """
        all_metrics = {
            "counters": dict(self._counters),
            "histograms": {},
            "derived": {}
        }

        for key in self._histograms:
            all_metrics["histograms"][key] = self.get_histogram_stats(
                key.split("|")[0],
                self._parse_labels_from_key(key)
            )

        # Add derived metrics
        all_metrics["derived"] = {
            "digest_cache_hit_ratio": self.get_cache_hit_ratio(),
            "avg_tokens_per_digest": self.get_avg_tokens_per_digest(),
            "daily_digest_open_rate": self.get_daily_digest_open_rate(),
            "total_digest_opens": sum(self._daily_opens.values())
        }

        return all_metrics

    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio.
        
        Returns:
            Cache hit ratio between 0.0 and 1.0
        """
        hits = self.get_counter("digest_cache_hit_count")
        misses = self.get_counter("digest_cache_miss_count")
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total

    def get_avg_tokens_per_digest(self) -> float:
        """Calculate average tokens per digest.
        
        Returns:
            Average token count, or 0.0 if no data
        """
        if not self._token_usage_history:
            return 0.0
        
        return sum(self._token_usage_history) / len(self._token_usage_history)

    def get_daily_digest_open_rate(self, date_str: str | None = None) -> float:
        """Calculate daily digest open rate.
        
        Args:
            date_str: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Number of digest opens for the specified date
        """
        if date_str is None:
            from datetime import date
            date_str = date.today().isoformat()
        
        return float(self._daily_opens.get(date_str, 0))

    def record_token_usage(self, token_count: int) -> None:
        """Record token usage for averaging.
        
        Args:
            token_count: Number of tokens used in this request
        """
        self._token_usage_history.append(token_count)
        
        # Keep only last 1000 entries to prevent memory growth
        if len(self._token_usage_history) > 1000:
            self._token_usage_history = self._token_usage_history[-1000:]
            
        logger.debug(
            "Token usage recorded",
            action="digest_metrics.token_usage",
            token_count=token_count,
            avg_tokens=self.get_avg_tokens_per_digest()
        )

    def record_digest_open(self, date_str: str | None = None) -> None:
        """Record a digest being opened/accessed.
        
        Args:
            date_str: Date string (YYYY-MM-DD), defaults to today
        """
        if date_str is None:
            from datetime import date
            date_str = date.today().isoformat()
        
        self._daily_opens[date_str] = self._daily_opens.get(date_str, 0) + 1
        
        logger.debug(
            "Digest open recorded",
            action="digest_metrics.digest_open",
            date=date_str,
            daily_count=self._daily_opens[date_str]
        )

    def _build_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Build a unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_str}"

    def _parse_labels_from_key(self, key: str) -> dict[str, str] | None:
        """Parse labels from a metric key."""
        if "|" not in key:
            return None
        _, label_str = key.split("|", 1)
        labels = {}
        for pair in label_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        return labels if labels else None


class InstrumentedDigestService:
    """Wrapper that adds metrics instrumentation to digest service operations."""

    def __init__(self, metrics: DigestMetrics):
        """Initialize with metrics collector.

        Args:
            metrics: DigestMetrics instance for recording metrics
        """
        self.metrics = metrics

    @asynccontextmanager
    async def measure_digest_generation(self, operation: str = "generate") -> AsyncGenerator[None, None]:
        """Context manager for measuring digest generation operations.

        Args:
            operation: Operation name for labeling
        """
        start_time = time.time()
        success = False

        try:
            yield
            success = True
        except Exception as e:
            # Record failure
            self.metrics.increment_counter(
                "digest_generation_failure_count",
                labels={"operation": operation, "stage": "execution"}
            )
            logger.error(
                "Digest generation failed",
                action="digest_metrics.failure",
                operation=operation,
                error=str(e)
            )
            raise
        finally:
            # Record latency
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_histogram(
                "digest_latency_ms",
                duration_ms,
                labels={"operation": operation}
            )

            # Record success if no exception
            if success:
                self.metrics.increment_counter(
                    "digest_generation_success_count",
                    labels={"operation": operation}
                )
                logger.info(
                    "Digest generation completed",
                    action="digest_metrics.success",
                    operation=operation,
                    duration_ms=duration_ms
                )

    def record_cache_event(self, event_type: str, hit: bool) -> None:
        """Record cache hit/miss events.

        Args:
            event_type: Type of cache operation (get, set)
            hit: Whether it was a cache hit (True) or miss (False)
        """
        self.metrics.increment_counter(
            "digest_cache_hit_count" if hit else "digest_cache_miss_count",
            labels={"operation": event_type}
        )

        logger.debug(
            "Cache event recorded",
            action="digest_metrics.cache",
            event_type=event_type,
            cache_hit=hit
        )

    @asynccontextmanager
    async def measure_preprocessing(self) -> AsyncGenerator[None, None]:
        """Context manager for measuring preprocessing operations.
        
        Measures time spent on data fetching, derivation, and preparation
        before LLM generation.
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_histogram(
                "digest_preprocessing_latency_ms",
                duration_ms
            )

    @asynccontextmanager
    async def measure_llm_generation(self) -> AsyncGenerator[None, None]:
        """Context manager for measuring LLM generation operations.
        
        Measures time spent on actual LLM API calls and response processing.
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_histogram(
                "digest_llm_latency_ms",
                duration_ms
            )

    def record_digest_access(self, date_str: str | None = None) -> None:
        """Record a digest being accessed/opened.
        
        Args:
            date_str: Date string (YYYY-MM-DD), defaults to today
        """
        self.metrics.record_digest_open(date_str)

    def record_token_usage(self, tokens_in: int, tokens_out: int) -> None:
        """Record token usage for a digest generation.
        
        Args:
            tokens_in: Input tokens
            tokens_out: Output tokens
        """
        total_tokens = tokens_in + tokens_out
        self.metrics.record_token_usage(total_tokens)


# Global metrics instance
digest_metrics = DigestMetrics()
digest_instrumentation = InstrumentedDigestService(digest_metrics)
