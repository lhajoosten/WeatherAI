from typing import Dict, Any, List
import json
import logging
from datetime import datetime, timedelta
from app.services.llm_client import LLMClient
from app.db.repositories import ForecastRepository
from app.db.models import Location

logger = logging.getLogger(__name__)


class ExplainService:
    """Service for generating weather explanations using structured facts."""
    
    def __init__(self, llm_client: LLMClient, forecast_repo: ForecastRepository):
        self.llm_client = llm_client
        self.forecast_repo = forecast_repo
    
    async def explain_location_weather(self, location: Location, user_id: int) -> Dict[str, Any]:
        """Generate weather explanation for a location using structured facts.
        
        Args:
            location: Location to explain weather for
            user_id: User ID for audit logging
            
        Returns:
            Dict with summary, actions, driver, and token metadata
        """
        logger.info(f"Generating weather explanation for location {location.id}")
        
        # Get cached forecast data
        forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)
        
        if not forecast_cache:
            # Create mock forecast data for demo
            logger.info("No cached forecast found, creating mock data")
            await self._create_mock_forecast(location.id)
            forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)
        
        # Build structured facts from forecast data
        structured_facts = self._build_structured_facts(location, forecast_cache)
        
        # Generate prompt using template
        prompt = self._build_explain_prompt(structured_facts)
        
        # Call LLM
        llm_response = await self.llm_client.generate(
            prompt=prompt,
            user_id=user_id,
            endpoint="explain",
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=400
        )
        
        # Parse response into structured format
        parsed_response = self._parse_explain_response(llm_response["text"])
        
        return {
            "summary": parsed_response["summary"],
            "actions": parsed_response["actions"],
            "driver": parsed_response["driver"],
            "tokens_in": llm_response["tokens_in"],
            "tokens_out": llm_response["tokens_out"],
            "model": llm_response["model"]
        }
    
    def _build_structured_facts(self, location: Location, forecast_cache) -> Dict[str, Any]:
        """Build structured facts from forecast data to prevent hallucination."""
        if not forecast_cache:
            return {
                "location": {
                    "name": location.name,
                    "lat": location.lat,
                    "lon": location.lon,
                    "timezone": location.timezone or "UTC"
                },
                "error": "No forecast data available"
            }
        
        try:
            forecast_data = json.loads(forecast_cache.payload_json)
        except json.JSONDecodeError:
            forecast_data = {"error": "Invalid forecast data"}
        
        return {
            "location": {
                "name": location.name,
                "lat": location.lat,
                "lon": location.lon,
                "timezone": location.timezone or "UTC"
            },
            "forecast": forecast_data,
            "data_source": forecast_cache.source,
            "fetched_at": forecast_cache.fetched_at.isoformat(),
            "expires_at": forecast_cache.expires_at.isoformat()
        }
    
    def _build_explain_prompt(self, structured_facts: Dict[str, Any]) -> str:
        """Build prompt using explain_v1 template with guardrails."""
        facts_json = json.dumps(structured_facts, indent=2)
        
        return f"""System: You are a concise weather assistant. Use ONLY the data provided in the Data section below. Do not invent, estimate, or hallucinate any weather measurements, temperatures, or conditions not explicitly provided.

Data:
{facts_json}

Task: Based ONLY on the provided data, produce:
1. A 2-3 sentence summary of the weather conditions
2. Exactly 3 practical action items (bullet points)
3. A brief explanation of the main weather driver/pattern

Format your response as:
Summary: [your summary here]

Actions:
- [action 1]
- [action 2]  
- [action 3]

Driver: [main weather driver explanation]

If any required data is missing or unclear, state "Information unavailable" for that section rather than guessing."""
    
    def _parse_explain_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured components with fallback."""
        try:
            lines = response_text.strip().split('\n')
            summary = ""
            actions = []
            driver = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("Summary:"):
                    current_section = "summary"
                    summary = line[8:].strip()
                elif line.startswith("Actions:"):
                    current_section = "actions"
                elif line.startswith("Driver:"):
                    current_section = "driver"
                    driver = line[7:].strip()
                elif line.startswith("- ") and current_section == "actions":
                    actions.append(line[2:].strip())
                elif current_section == "summary" and summary:
                    summary += " " + line
                elif current_section == "driver" and driver:
                    driver += " " + line
            
            # Ensure we have at least something
            if not summary:
                summary = "Weather information processed successfully."
            if not actions:
                actions = ["Check weather updates regularly", "Plan accordingly", "Stay informed"]
            if not driver:
                driver = "Standard weather patterns observed."
            
            return {
                "summary": summary,
                "actions": actions[:3],  # Limit to 3 actions
                "driver": driver
            }
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "summary": "Weather analysis completed.",
                "actions": ["Check current conditions", "Monitor for updates", "Plan outdoor activities accordingly"],
                "driver": "Unable to parse detailed weather analysis."
            }
    
    async def _create_mock_forecast(self, location_id: int):
        """Create mock forecast data for demo purposes."""
        mock_forecast = {
            "current": {
                "temperature": 22.5,
                "humidity": 65,
                "wind_speed": 8.5,
                "wind_direction": "SW",
                "conditions": "partly cloudy",
                "visibility": 10
            },
            "hourly_48h": [
                {
                    "time": (datetime.utcnow() + timedelta(hours=i)).isoformat(),
                    "temperature": 22.5 - (i * 0.3),
                    "precipitation_probability": min(20 + i * 2, 60),
                    "wind_speed": 8.5 + (i * 0.2),
                    "conditions": "partly cloudy" if i < 12 else "cloudy"
                }
                for i in range(48)
            ],
            "daily_7d": [
                {
                    "date": (datetime.utcnow() + timedelta(days=i)).date().isoformat(),
                    "temp_high": 25 - i,
                    "temp_low": 15 - i,
                    "precipitation_probability": min(20 + i * 5, 70),
                    "conditions": "partly cloudy"
                }
                for i in range(7)
            ]
        }
        
        expires_at = datetime.utcnow() + timedelta(hours=6)
        
        await self.forecast_repo.create(
            location_id=location_id,
            source="mock",
            payload_json=json.dumps(mock_forecast),
            expires_at=expires_at
        )