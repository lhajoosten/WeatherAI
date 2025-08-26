import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.accuracy_repository import AccuracyRepository
from app.infrastructure.db.repositories.aggregation_repository import AggregationRepository
from app.infrastructure.db.repositories.trend_repository import TrendRepository

logger = logging.getLogger(__name__)


class SummaryPromptService:
    """Service for building structured prompts for analytics LLM summary generation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.trend_repo = TrendRepository(session)
        self.aggregation_repo = AggregationRepository(session)
        self.accuracy_repo = AccuracyRepository(session)

    async def build_analytics_prompt(
        self,
        location_id: int,
        period: str = '7d',
        metrics: list[str] | None = None
    ) -> dict[str, Any]:
        """Build structured prompt data for analytics summary generation.

        Returns a dictionary with structured data that will be serialized to JSON
        for the LLM prompt. This ensures no free-form user text leaks into prompts.
        """
        logger.info(f"Building analytics prompt for location {location_id}, period {period}")

        if metrics is None:
            metrics = ['avg_temp_c', 'total_precip_mm', 'max_wind_kph']

        # Get trends for the specified period
        trends = await self.trend_repo.get_by_location_and_metrics(
            location_id=location_id,
            period=period,
            metrics=metrics
        )

        # Get recent daily aggregations (last 7 days for context)
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)

        recent_aggregations = await self.aggregation_repo.get_by_location_and_period(
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )

        # Get recent accuracy metrics (last 7 days)
        accuracy_records = await self.accuracy_repo.get_by_location_and_period(
            location_id=location_id,
            start_time=start_date,
            end_time=end_date,
            variables=['temp_c', 'precipitation_probability_pct']
        )

        # Build structured prompt data
        prompt_data = {
            "location_id": location_id,
            "analysis_period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "trends": [
                {
                    "metric": trend.metric,
                    "period": trend.period,
                    "current_value": trend.current_value,
                    "previous_value": trend.previous_value,
                    "delta": trend.delta,
                    "pct_change": round(trend.pct_change, 1) if trend.pct_change else None,
                    "generated_at": trend.generated_at.isoformat() if trend.generated_at else None
                }
                for trend in trends
            ],
            "recent_daily_data": [
                {
                    "date": agg.date.date().isoformat(),
                    "temp_min_c": agg.temp_min_c,
                    "temp_max_c": agg.temp_max_c,
                    "avg_temp_c": agg.avg_temp_c,
                    "total_precip_mm": agg.total_precip_mm,
                    "max_wind_kph": agg.max_wind_kph,
                    "heating_degree_days": agg.heating_degree_days,
                    "cooling_degree_days": agg.cooling_degree_days
                }
                for agg in recent_aggregations[-5:]  # Last 5 days
            ],
            "forecast_accuracy_summary": self._summarize_accuracy_metrics(accuracy_records),
            "metadata": {
                "prompt_version": "analytics_summary_v2",
                "data_points": {
                    "trends": len(trends),
                    "daily_aggregations": len(recent_aggregations),
                    "accuracy_records": len(accuracy_records)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Built prompt with {len(trends)} trends, {len(recent_aggregations)} daily records")

        # Check if we have enough data for meaningful analysis
        total_data_points = len(trends) + len(recent_aggregations) + len(accuracy_records)
        prompt_data['metadata']['total_data_points'] = total_data_points
        prompt_data['metadata']['has_sufficient_data'] = total_data_points > 0

        return prompt_data

    def _summarize_accuracy_metrics(self, accuracy_records: list[Any]) -> dict[str, Any]:
        """Summarize accuracy metrics into structured data."""
        if not accuracy_records:
            return {"message": "No recent accuracy data available"}

        # Group by variable
        by_variable = {}
        for record in accuracy_records:
            if record.variable not in by_variable:
                by_variable[record.variable] = []
            by_variable[record.variable].append(record)

        summary = {}
        for variable, records in by_variable.items():
            # Filter out records with missing values
            valid_records = [r for r in records if r.abs_error is not None]

            if valid_records:
                avg_abs_error = sum(r.abs_error for r in valid_records) / len(valid_records)
                avg_pct_error = None
                if any(r.pct_error for r in valid_records):
                    pct_errors = [r.pct_error for r in valid_records if r.pct_error is not None]
                    avg_pct_error = sum(pct_errors) / len(pct_errors) if pct_errors else None

                summary[variable] = {
                    "sample_size": len(valid_records),
                    "avg_absolute_error": round(avg_abs_error, 2),
                    "avg_percentage_error": round(avg_pct_error, 1) if avg_pct_error else None
                }
            else:
                summary[variable] = {"message": "No valid accuracy data"}

        return summary

    def format_prompt_for_llm(self, prompt_data: dict[str, Any]) -> str:
        """Format the structured prompt data for LLM consumption with defensive truncation.

        This method converts the structured data into a human-readable format
        while maintaining the constraint that no user input is included.

        Includes defensive truncation if prompt would exceed safe token limits.
        """
        # Estimate token count (rough approximation: words * 1.3)
        full_json = json.dumps(prompt_data, indent=2, default=str)
        estimated_tokens = len(full_json.split()) * 1.3

        # Token limits - leave room for response (approximate)
        max_input_tokens = 3000  # Conservative limit

        if estimated_tokens > max_input_tokens:
            logger.warning(
                "Prompt would exceed token limit, applying defensive truncation",
                estimated_tokens=estimated_tokens,
                max_tokens=max_input_tokens
            )

            # Apply truncation strategy - keep most important data
            truncated_data = self._apply_defensive_truncation(prompt_data)
            json_data = json.dumps(truncated_data, indent=2, default=str)
        else:
            json_data = full_json

        # Check if we have sufficient data
        has_sufficient_data = prompt_data.get('metadata', {}).get('has_sufficient_data', False)

        if not has_sufficient_data:
            # Graceful degradation for insufficient data
            prompt = f"""System: You are a weather analytics assistant. The provided data is limited but analyze what's available and provide a brief summary.

Data: {json_data}

Since data is limited, provide a short summary (2-3 sentences) acknowledging the data limitations and mentioning any patterns visible in the available data. Do not invent values not present in the data."""
        else:
            # Full structured prompt for sufficient data
            prompt = f"""System: You are a weather analytics assistant. Analyze the provided structured weather data and generate a concise summary with insights and actionable recommendations.

Requirements:
- Use ONLY the numerical values provided in the data
- Do not invent, estimate, or hallucinate any values
- Reference specific metrics when available (temperatures, precipitation, wind speeds)
- Keep each section to 2-3 sentences maximum

Data: {json_data}

Generate a structured response with these sections:

## Metrics Overview
Provide a brief summary of current weather metrics including temperature ranges, precipitation totals, and wind speeds from the recent daily data.

## Trend Analysis
Analyze the trend data to identify significant changes over the 7-day and 30-day periods. Mention specific percentage changes where available.

## Forecast Performance
Assess forecast accuracy using the provided accuracy metrics. Mention which weather variables show better or worse forecast performance.

## Key Insights
Provide 2-3 actionable insights or patterns based on the data analysis.

Important: Reference only values explicitly provided in the Data section above. If insufficient data is available for any section, state that clearly rather than making estimates."""

        return prompt

    def _apply_defensive_truncation(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        """Apply defensive truncation to keep most important data within token limits."""
        truncated = {
            "metadata": prompt_data.get("metadata", {}),
            "location_info": prompt_data.get("location_info", {})
        }

        # Keep most recent trends (prioritize shorter periods)
        trends = prompt_data.get("trends", [])
        if trends:
            # Keep 7d trends first, then 30d for top metrics
            priority_trends = []
            for trend in trends:
                if trend.get("period") == "7d":
                    priority_trends.append(trend)
                elif trend.get("period") == "30d" and len(priority_trends) < 6:
                    priority_trends.append(trend)
            truncated["trends"] = priority_trends[:8]  # Limit to 8 trends

        # Keep last 3 days of daily data instead of 5
        daily_data = prompt_data.get("recent_daily_data", [])
        if daily_data:
            truncated["recent_daily_data"] = daily_data[-3:]

        # Keep simplified accuracy summary
        accuracy = prompt_data.get("forecast_accuracy_summary", {})
        if accuracy and accuracy != {"message": "No recent accuracy data available"}:
            # Keep only temp_c and precip_mm accuracy (most important)
            simplified_accuracy = {}
            for var in ["temp_c", "precip_mm"]:
                if var in accuracy:
                    simplified_accuracy[var] = accuracy[var]
            truncated["forecast_accuracy_summary"] = simplified_accuracy or {"message": "Limited accuracy data"}
        else:
            truncated["forecast_accuracy_summary"] = accuracy

        return truncated

    def _truncate_prompt(self, prompt: str) -> str:
        """Truncate prompt to allowed length and return the truncated value."""
        truncated = prompt[:2000]
        return truncated
