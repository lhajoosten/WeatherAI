"""Placeholder narrative generator for digest responses.

This module provides deterministic placeholder content for PR1, replacing
the LLM integration that will be added in PR2. The output is static but
context-influenced to ensure validity.
"""


from app.schemas.digest import Bullet, Summary
from app.domain.weather_calculations import ActivityBlock


def build_placeholder_summary(derived_metrics: dict, preferences: dict) -> Summary:
    """Build placeholder summary with deterministic but context-influenced content.

    Args:
        derived_metrics: Dictionary with derived weather metrics
        preferences: User preferences dictionary

    Returns:
        Summary object with narrative, bullets, and driver
    """
    temp_min = derived_metrics.get('temp_min_c', 20)
    temp_max = derived_metrics.get('temp_max_c', 25)
    comfort_score = derived_metrics.get('comfort_score', 0.5)
    activity_blocks = derived_metrics.get('activity_blocks', [])
    derived_metrics.get('peak_rain_window')

    # Determine main weather driver based on conditions
    driver = _determine_weather_driver(derived_metrics)

    # Build context-influenced narrative
    narrative = _build_narrative(temp_min, temp_max, comfort_score, driver)

    # Generate exactly 3 bullets as specified
    bullets = _generate_bullets(derived_metrics, activity_blocks, preferences)

    return Summary(
        narrative=narrative,
        bullets=bullets,
        driver=driver
    )


def _determine_weather_driver(derived_metrics: dict) -> str:
    """Determine the main weather driver for the day."""
    peak_rain_window = derived_metrics.get('peak_rain_window')
    comfort_score = derived_metrics.get('comfort_score', 0.5)
    temp_max = derived_metrics.get('temp_max_c', 20)
    temp_min = derived_metrics.get('temp_min_c', 20)

    # Priority order: rain > extreme temps > comfort > default
    if peak_rain_window:
        return "precipitation"
    elif temp_max > 30 or temp_min < 5:
        return "temperature extremes"
    elif comfort_score < 0.4:
        return "challenging weather conditions"
    elif comfort_score > 0.8:
        return "favorable weather conditions"
    else:
        return "mixed weather conditions"


def _build_narrative(temp_min: float, temp_max: float, comfort_score: float, driver: str) -> str:
    """Build main narrative text based on weather conditions."""
    temp_range = f"{temp_min:.0f}°C to {temp_max:.0f}°C"

    if driver == "precipitation":
        return (f"Today's weather will be dominated by rainfall, with temperatures ranging from {temp_range}. "
                f"Plan indoor activities during rain periods and take advantage of drier windows for outdoor tasks.")
    elif driver == "temperature extremes":
        if temp_max > 30:
            return (f"A hot day ahead with temperatures reaching {temp_max:.0f}°C. "
                    f"Stay hydrated and seek shade during peak hours. Morning and evening activities are recommended.")
        else:
            return (f"Cold conditions expected with temperatures dropping to {temp_min:.0f}°C. "
                    f"Dress warmly and consider indoor alternatives for extended outdoor activities.")
    elif driver == "favorable weather conditions":
        return (f"Excellent weather conditions today with temperatures from {temp_range}. "
                f"Perfect opportunity for outdoor activities and errands. Make the most of these pleasant conditions.")
    elif driver == "challenging weather conditions":
        return (f"Challenging weather conditions expected today with temperatures from {temp_range}. "
                f"Multiple weather factors may impact outdoor plans. Stay flexible and monitor conditions throughout the day.")
    else:
        return (f"Mixed weather conditions today with temperatures ranging from {temp_range}. "
                f"Variable conditions throughout the day - plan accordingly and stay prepared for changes.")


def _generate_bullets(derived_metrics: dict, activity_blocks: list[ActivityBlock], preferences: dict) -> list[Bullet]:
    """Generate exactly 3 bullets as specified in requirements."""
    bullets = []

    # Bullet 1: Temperature-focused action item
    temp_max = derived_metrics.get('temp_max_c', 20)
    temp_min = derived_metrics.get('temp_min_c', 20)

    if temp_max > 28:
        bullets.append(Bullet(
            text=f"High temperature of {temp_max:.0f}°C expected - plan outdoor activities for early morning or evening",
            category="weather",
            priority=1
        ))
    elif temp_min < 8:
        bullets.append(Bullet(
            text=f"Cold start with {temp_min:.0f}°C - dress in layers and allow extra time for warming up vehicles",
            category="weather",
            priority=1
        ))
    else:
        bullets.append(Bullet(
            text=f"Comfortable temperature range {temp_min:.0f}°C-{temp_max:.0f}°C - ideal for most outdoor activities",
            category="weather",
            priority=2
        ))

    # Bullet 2: Activity recommendation
    if activity_blocks:
        best_block = max(activity_blocks, key=lambda b: b.suitability_score)
        time_desc = _format_time_window(best_block.time_window.start_hour, best_block.time_window.end_hour)
        bullets.append(Bullet(
            text=f"Best time for {best_block.activity_type} activities: {time_desc} ({best_block.conditions})",
            category="activity",
            priority=1 if best_block.suitability_score > 0.7 else 2
        ))
    else:
        bullets.append(Bullet(
            text="Monitor weather conditions throughout the day for optimal activity timing",
            category="activity",
            priority=3
        ))

    # Bullet 3: Precipitation or wind alert
    peak_rain_window = derived_metrics.get('peak_rain_window')
    lowest_wind_window = derived_metrics.get('lowest_wind_window')

    if peak_rain_window:
        rain_time = _format_time_window(peak_rain_window.start_hour, peak_rain_window.end_hour)
        bullets.append(Bullet(
            text=f"Heaviest rainfall expected around {rain_time} - plan indoor activities during this period",
            category="alert",
            priority=1
        ))
    elif lowest_wind_window:
        wind_time = _format_time_window(lowest_wind_window.start_hour, lowest_wind_window.end_hour)
        bullets.append(Bullet(
            text=f"Calmest conditions expected {wind_time} - ideal for outdoor activities requiring precision",
            category="weather",
            priority=2
        ))
    else:
        comfort_score = derived_metrics.get('comfort_score', 0.5)
        if comfort_score > 0.8:
            bullets.append(Bullet(
                text="Excellent overall conditions - perfect day for any planned outdoor activities",
                category="weather",
                priority=2
            ))
        else:
            bullets.append(Bullet(
                text="Variable conditions expected - stay flexible and be prepared to adjust plans",
                category="alert",
                priority=2
            ))

    return bullets


def _format_time_window(start_hour: int, end_hour: int) -> str:
    """Format time window for display."""
    def format_hour(hour: int) -> str:
        if hour == 0:
            return "12 AM"
        elif hour < 12:
            return f"{hour} AM"
        elif hour == 12:
            return "12 PM"
        else:
            return f"{hour - 12} PM"

    if start_hour == end_hour:
        return format_hour(start_hour)
    else:
        return f"{format_hour(start_hour)}-{format_hour(end_hour)}"
