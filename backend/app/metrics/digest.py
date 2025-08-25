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
            Dictionary with all counters and histogram stats
        """
        all_metrics = {
            "counters": dict(self._counters),
            "histograms": {}
        }

        for key in self._histograms:
            all_metrics["histograms"][key] = self.get_histogram_stats(
                key.split("|")[0],
                self._parse_labels_from_key(key)
            )

        return all_metrics

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


# Global metrics instance
digest_metrics = DigestMetrics()
digest_instrumentation = InstrumentedDigestService(digest_metrics)
