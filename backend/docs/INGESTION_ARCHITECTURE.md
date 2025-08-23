# Ingestion Architecture

## Overview

The WeatherAI ingestion system provides a multi-provider architecture for collecting weather data, air quality, and astronomical information from various external sources. This document describes the architecture, data flow, and extensibility patterns.

## Architecture Diagram

```
External APIs         Provider Layer        Orchestrator         Data Layer
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  OpenMeteo API  │   │ ForecastProvider│   │                 │   │ forecast_hourly │
│  (Free)         │──▶│ Implementation  │──▶│                 │──▶│                 │
└─────────────────┘   └─────────────────┘   │                 │   └─────────────────┘
                                            │                 │
┌─────────────────┐   ┌─────────────────┐   │   Ingestion     │   ┌─────────────────┐
│  NOAA METAR     │   │ ObservationProv.│   │   Orchestrator  │   │observation_hour.│
│  (Optional)     │──▶│ Implementation  │──▶│                 │──▶│                 │
└─────────────────┘   └─────────────────┘   │                 │   └─────────────────┘
                                            │                 │
┌─────────────────┐   ┌─────────────────┐   │                 │   ┌─────────────────┐
│ Local Astral    │   │ AstronomyService│   │                 │   │ astronomy_daily │
│ Computation     │──▶│ (Local Compute) │──▶│                 │──▶│                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
                                                    │
                                            ┌─────────────────┐   ┌─────────────────┐
                                            │   Scheduler     │   │ provider_run    │
                                            │   (Periodic)    │──▶│ (Status Track)  │
                                            └─────────────────┘   └─────────────────┘
```

## Provider Abstractions

### ForecastProvider
Abstract base class for weather forecast data sources.

```python
class ForecastProvider(ABC):
    @abstractmethod
    async def fetch_forecast(self, location_id: int, lat: float, lon: float) -> list[dict]:
        pass
```

**Implementations:**
- `OpenMeteoForecastProvider`: Free API providing 3-day hourly forecasts
- Future: NOAA GFS, MET Norway (stubbed for extensibility)

### ObservationProvider
Abstract base class for weather observation data sources.

```python
class ObservationProvider(ABC):
    @abstractmethod
    async def fetch_observations(self, location_id: int, lat: float, lon: float, hours_back: int) -> list[dict]:
        pass
```

**Implementations:**
- `OpenMeteoObservationProvider`: Historical weather observations
- `MetarObservationProvider`: NOAA METAR data (config-enabled)

### AirQualityProvider
Abstract base class for air quality and pollen data sources.

```python
class AirQualityProvider(ABC):
    @abstractmethod
    async def fetch_air_quality(self, location_id: int, lat: float, lon: float, hours_back: int) -> list[dict]:
        pass
```

**Implementations:**
- `OpenMeteoAirQualityProvider`: PM2.5, PM10, O3, NO2, SO2, pollen data

## Data Normalization

All providers normalize their data to standard formats:

### Forecast Records
```python
{
    "location_id": int,
    "forecast_issue_time": datetime,
    "target_time": datetime,
    "temp_c": float | None,
    "precipitation_probability_pct": float | None,
    "wind_kph": float | None,
    "model_name": str,
    "source_run_id": str,
    "raw_json": str | None
}
```

### Observation Records
```python
{
    "location_id": int,
    "observed_at": datetime,
    "temp_c": float | None,
    "wind_kph": float | None,
    "precip_mm": float | None,
    "humidity_pct": float | None,
    "condition_code": str | None,
    "source": str,
    "raw_json": str | None
}
```

### Air Quality Records
```python
{
    "location_id": int,
    "observed_at": datetime,
    "pm10": float | None,
    "pm2_5": float | None,
    "ozone": float | None,
    "no2": float | None,
    "so2": float | None,
    "pollen_tree": float | None,
    "pollen_grass": float | None,
    "pollen_weed": float | None,
    "source": str,
    "raw_json": str | None
}
```

## Configuration

### Environment Variables
```bash
# OpenMeteo Configuration
OPENMETEO_BASE_URL=https://api.open-meteo.com

# METAR Configuration (Optional)
ENABLE_METAR=false
METAR_BASE_URL=https://aviationweather.gov/adds/dataserver_current/httpparam

# Ingestion Settings
INGEST_INTERVAL_MINUTES=120
MAX_LOCATIONS_PER_INGEST=25
```