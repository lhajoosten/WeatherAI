"""Placeholder providers for digest service dependencies.

These are simple implementations for PR1 to allow testing the digest
functionality without requiring full forecast ingestion or user
preferences systems.
"""

import random
from datetime import datetime, timedelta
from typing import Any


class PlaceholderForecastProvider:
    """Placeholder forecast provider for PR1 testing."""

    async def get_forecast(self, location_id: int, date: str) -> dict[str, Any]:
        """Get placeholder forecast data for a location and date.

        Args:
            location_id: Location identifier
            date: Date string (YYYY-MM-DD)

        Returns:
            Dictionary with hourly forecast data
        """
        # Generate 24 hours of synthetic forecast data
        base_date = datetime.strptime(date, "%Y-%m-%d")
        hourly_data = []

        # Simulate realistic weather patterns
        base_temp = 18 + random.gauss(0, 5)  # Base temperature around 18°C

        for hour in range(24):
            hour_time = base_date + timedelta(hours=hour)

            # Temperature variation throughout the day
            temp_variation = 5 * (1 + 0.8 * (hour - 12) / 12) if hour > 6 and hour < 18 else -2
            temperature = base_temp + temp_variation + random.gauss(0, 1)

            # Precipitation with some clustering
            precip_chance = 0.3 if hour >= 14 and hour <= 18 else 0.1
            precipitation = random.uniform(0, 5) if random.random() < precip_chance else 0

            # Wind speed
            wind_speed = random.uniform(5, 25) + (3 if precipitation > 0 else 0)

            # Humidity
            humidity = random.uniform(40, 85) + (10 if precipitation > 0 else 0)
            humidity = min(100, humidity)

            hourly_data.append({
                "time": hour_time.isoformat(),
                "temperature": round(temperature, 1),
                "precipitation": round(precipitation, 1),
                "wind_speed": round(wind_speed, 1),
                "humidity": round(humidity, 1)
            })

        return {
            "location_id": location_id,
            "date": date,
            "last_updated": datetime.utcnow().isoformat(),
            "hourly": hourly_data
        }


class PlaceholderPreferencesProvider:
    """Placeholder user preferences provider for PR1 testing."""

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Get placeholder user preferences.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with user preferences
        """
        # Generate consistent preferences based on user_id hash
        user_hash = hash(user_id) % 1000

        return {
            "outdoor_activities": user_hash % 3 != 0,  # 66% prefer outdoor
            "temperature_tolerance": ["low", "normal", "high"][user_hash % 3],
            "rain_tolerance": ["low", "normal", "high"][(user_hash // 3) % 3],
            "units_system": "metric",
            "time_zone": "UTC",
            "activity_preferences": ["walking", "cycling", "gardening"] if user_hash % 2 == 0 else ["reading", "cooking", "indoor_exercise"]
        }
