"""Forecast derivation utilities for computing digest metrics from weather data.

This module contains pure functions with type hints for deriving metrics
from forecast data. All functions are deterministic and stateless.
"""


from app.schemas.digest import ActivityBlock, Window


def compute_temp_range(hourly_data: list[dict]) -> tuple[float, float]:
    """Compute minimum and maximum temperature from hourly forecast data.

    Args:
        hourly_data: List of hourly forecast dictionaries with 'temperature' key

    Returns:
        Tuple of (temp_min_c, temp_max_c)

    Raises:
        ValueError: If no valid temperature data found
    """
    if not hourly_data:
        raise ValueError("No hourly data provided")

    temperatures = []
    for hour in hourly_data:
        if 'temperature' in hour and hour['temperature'] is not None:
            temperatures.append(float(hour['temperature']))

    if not temperatures:
        raise ValueError("No valid temperature data found")

    return min(temperatures), max(temperatures)


def find_peak_rain_window(hourly_data: list[dict], window_hours: int = 1) -> Window | None:
    """Find the 1-hour window with maximum rainfall.

    Args:
        hourly_data: List of hourly forecast dictionaries with 'precipitation' key
        window_hours: Size of window in hours (default 1)

    Returns:
        Window object with peak rain period, or None if no rain
    """
    if not hourly_data or window_hours <= 0:
        return None

    # Extract precipitation values with hour indices
    precip_data = []
    for i, hour in enumerate(hourly_data):
        precip = hour.get('precipitation', 0) or 0
        precip_data.append((i, float(precip)))

    if not precip_data:
        return None

    # Find window with maximum total precipitation
    max_precip = 0
    max_window_start = 0

    for i in range(len(precip_data) - window_hours + 1):
        window_precip = sum(precip_data[j][1] for j in range(i, i + window_hours))
        if window_precip > max_precip:
            max_precip = window_precip
            max_window_start = i

    # Return None if no significant rain (< 0.1mm)
    if max_precip < 0.1:
        return None

    return Window(
        start_hour=max_window_start,
        end_hour=max_window_start + window_hours - 1,
        duration_hours=window_hours
    )


def find_lowest_wind_window(hourly_data: list[dict], window_hours: int = 2) -> Window | None:
    """Find the window with lowest average wind speeds.

    Args:
        hourly_data: List of hourly forecast dictionaries with 'wind_speed' key
        window_hours: Size of window in hours (default 2)

    Returns:
        Window object with lowest wind period, or None if no wind data
    """
    if not hourly_data or window_hours <= 0:
        return None

    # Extract wind speed values
    wind_data = []
    for i, hour in enumerate(hourly_data):
        wind_speed = hour.get('wind_speed', 0) or 0
        wind_data.append((i, float(wind_speed)))

    if not wind_data:
        return None

    # Find window with minimum average wind speed
    min_avg_wind = float('inf')
    min_window_start = 0

    for i in range(len(wind_data) - window_hours + 1):
        window_avg = sum(wind_data[j][1] for j in range(i, i + window_hours)) / window_hours
        if window_avg < min_avg_wind:
            min_avg_wind = window_avg
            min_window_start = i

    return Window(
        start_hour=min_window_start,
        end_hour=min_window_start + window_hours - 1,
        duration_hours=window_hours
    )


def compute_comfort_score(temp_min: float, temp_max: float, total_precip: float,
                         avg_wind: float, avg_humidity: float) -> float:
    """Compute overall comfort score using simple heuristics.

    The comfort score is calculated using the following criteria:
    - Temperature: optimal range 18-24°C
    - Precipitation: penalize heavy rain
    - Wind: penalize high winds (>20 km/h)
    - Humidity: optimal range 40-60%

    Args:
        temp_min: Minimum temperature in Celsius
        temp_max: Maximum temperature in Celsius
        total_precip: Total precipitation in mm
        avg_wind: Average wind speed in km/h
        avg_humidity: Average humidity percentage (0-100)

    Returns:
        Comfort score between 0.0 and 1.0
    """
    score = 1.0

    # Temperature component (optimal 18-24°C)
    temp_avg = (temp_min + temp_max) / 2
    if temp_avg < 10 or temp_avg > 30:
        score *= 0.3  # Very uncomfortable
    elif temp_avg < 15 or temp_avg > 27:
        score *= 0.6  # Uncomfortable
    elif temp_avg < 18 or temp_avg > 24:
        score *= 0.8  # Slightly uncomfortable
    # else: optimal range, no penalty

    # Precipitation component
    if total_precip > 10:
        score *= 0.4  # Heavy rain
    elif total_precip > 5:
        score *= 0.6  # Moderate rain
    elif total_precip > 1:
        score *= 0.8  # Light rain
    # else: no rain, no penalty

    # Wind component (penalize >20 km/h)
    if avg_wind > 30:
        score *= 0.5  # Very windy
    elif avg_wind > 20:
        score *= 0.7  # Windy
    elif avg_wind > 15:
        score *= 0.9  # Slightly windy
    # else: calm, no penalty

    # Humidity component (optimal 40-60%)
    if avg_humidity < 20 or avg_humidity > 80:
        score *= 0.7  # Very dry or very humid
    elif avg_humidity < 30 or avg_humidity > 70:
        score *= 0.8  # Dry or humid
    elif avg_humidity < 40 or avg_humidity > 60:
        score *= 0.9  # Slightly off optimal
    # else: optimal range, no penalty

    return max(0.0, min(1.0, score))


def generate_activity_blocks(hourly_data: list[dict], user_preferences: dict) -> list[ActivityBlock]:
    """Generate activity recommendation blocks using basic heuristics.

    Args:
        hourly_data: List of hourly forecast dictionaries
        user_preferences: User preferences dictionary with activity preferences

    Returns:
        List of ActivityBlock recommendations
    """
    if not hourly_data:
        return []

    blocks = []

    # Get user preferences (with defaults)
    prefers_outdoor = user_preferences.get('outdoor_activities', True)
    temp_tolerance = user_preferences.get('temperature_tolerance', 'normal')  # low/normal/high
    rain_tolerance = user_preferences.get('rain_tolerance', 'low')  # low/normal/high

    # Analyze morning (6-12), afternoon (12-18), evening (18-22) periods
    periods = [
        ('morning', 6, 12, 'Morning activities'),
        ('afternoon', 12, 18, 'Afternoon activities'),
        ('evening', 18, 22, 'Evening activities')
    ]

    for _period_name, start_hour, end_hour, _description in periods:
        if start_hour >= len(hourly_data):
            continue

        # Analyze weather for this period
        period_hours = hourly_data[start_hour:min(end_hour, len(hourly_data))]
        if not period_hours:
            continue

        # Calculate period averages
        temps = [h.get('temperature', 20) or 20 for h in period_hours]
        precips = [h.get('precipitation', 0) or 0 for h in period_hours]
        winds = [h.get('wind_speed', 0) or 0 for h in period_hours]

        avg_temp = sum(temps) / len(temps)
        total_precip = sum(precips)
        avg_wind = sum(winds) / len(winds)

        # Determine activity type and suitability
        activity_type = "mixed"  # default
        suitability = 0.5  # default
        conditions = f"Average {avg_temp:.1f}°C"

        # Outdoor suitability logic
        outdoor_suitable = True
        if total_precip > 2:  # More than 2mm rain
            outdoor_suitable = False
            conditions += f", {total_precip:.1f}mm rain"
        elif total_precip > 0.5:
            conditions += f", light rain ({total_precip:.1f}mm)"

        if avg_wind > 25:
            outdoor_suitable = False
            conditions += f", windy ({avg_wind:.1f} km/h)"
        elif avg_wind > 15:
            conditions += f", breezy ({avg_wind:.1f} km/h)"

        # Temperature suitability
        if avg_temp < 5 or avg_temp > 35:
            outdoor_suitable = False
        elif avg_temp < 10 or avg_temp > 30:
            if temp_tolerance != 'high':
                outdoor_suitable = False

        # Determine activity type and score
        if outdoor_suitable and prefers_outdoor:
            activity_type = "outdoor"
            suitability = 0.8
        elif outdoor_suitable:
            activity_type = "mixed"
            suitability = 0.7
        else:
            activity_type = "indoor"
            suitability = 0.6

        # Adjust for rain tolerance
        if total_precip > 0 and rain_tolerance == 'high' and activity_type == "indoor":
            activity_type = "mixed"
            suitability = min(0.8, suitability + 0.2)

        blocks.append(ActivityBlock(
            activity_type=activity_type,
            time_window=Window(
                start_hour=start_hour,
                end_hour=min(end_hour - 1, len(hourly_data) - 1),
                duration_hours=min(end_hour - start_hour, len(hourly_data) - start_hour)
            ),
            conditions=conditions,
            suitability_score=suitability
        ))

    return blocks


def derive_all_metrics(hourly_data: list[dict], user_preferences: dict) -> dict:
    """Derive all metrics needed for the digest in one call.

    Args:
        hourly_data: List of hourly forecast dictionaries
        user_preferences: User preferences dictionary

    Returns:
        Dictionary with all derived metrics
    """
    if not hourly_data:
        raise ValueError("No hourly data provided")

    # Basic temperature range
    temp_min, temp_max = compute_temp_range(hourly_data)

    # Windows for specific conditions
    peak_rain_window = find_peak_rain_window(hourly_data)
    lowest_wind_window = find_lowest_wind_window(hourly_data)

    # Calculate aggregates for comfort score
    all_precip = [h.get('precipitation', 0) or 0 for h in hourly_data]
    all_wind = [h.get('wind_speed', 0) or 0 for h in hourly_data]
    all_humidity = [h.get('humidity', 50) or 50 for h in hourly_data]

    total_precip = sum(all_precip)
    avg_wind = sum(all_wind) / len(all_wind) if all_wind else 0
    avg_humidity = sum(all_humidity) / len(all_humidity) if all_humidity else 50

    # Comfort score
    comfort_score = compute_comfort_score(temp_min, temp_max, total_precip, avg_wind, avg_humidity)

    # Activity blocks
    activity_blocks = generate_activity_blocks(hourly_data, user_preferences)

    return {
        'temp_min_c': temp_min,
        'temp_max_c': temp_max,
        'peak_rain_window': peak_rain_window,
        'lowest_wind_window': lowest_wind_window,
        'comfort_score': comfort_score,
        'activity_blocks': activity_blocks
    }
