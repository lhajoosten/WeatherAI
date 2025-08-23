import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.repositories.trend_repository import TrendRepository
from app.analytics.repositories.aggregation_repository import AggregationRepository
from app.analytics.repositories.accuracy_repository import AccuracyRepository

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
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
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
        start_date = end_date - datetime.timedelta(days=7)
        
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
                "prompt_version": "analytics_summary_v1",
                "data_points": {
                    "trends": len(trends),
                    "daily_aggregations": len(recent_aggregations),
                    "accuracy_records": len(accuracy_records)
                }
            }
        }
        
        logger.info(f"Built prompt with {len(trends)} trends, {len(recent_aggregations)} daily records")
        return prompt_data
    
    def _summarize_accuracy_metrics(self, accuracy_records: List[Any]) -> Dict[str, Any]:
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
    
    def format_prompt_for_llm(self, prompt_data: Dict[str, Any]) -> str:
        """Format the structured prompt data for LLM consumption.
        
        This method converts the structured data into a human-readable format
        while maintaining the constraint that no user input is included.
        """
        # Serialize to clean JSON
        json_data = json.dumps(prompt_data, indent=2, default=str)
        
        prompt = f"""System: You are a weather analytics assistant. Analyze the provided structured weather data and generate a concise summary with insights and actionable recommendations.

Data: {json_data}

Generate a structured response with these sections:
1. Overview: Brief summary of key weather patterns
2. Notable Changes: Significant trends or anomalies 
3. Accuracy: Forecast performance assessment
4. Actions: 2-3 specific recommendations based on the data

Keep the response concise (3-4 sentences per section). Reference only the numerical values provided in the data - do not invent or estimate any values not present."""

        return prompt