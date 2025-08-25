import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import check_rate_limit, get_current_user
from app.infrastructure.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geo", tags=["geocoding"])

# Simple in-memory cache for geocoding results
_geocoding_cache: dict[str, list[dict[str, Any]]] = {}


class GeocodingService:
    """Service for geocoding location searches."""

    def __init__(self):
        self.base_url = "https://geocoding-api.open-meteo.com/v1/search"

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for locations using Open-Meteo Geocoding API."""
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in _geocoding_cache:
            logger.info(f"Returning cached geocoding result for: {query}")
            return _geocoding_cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "name": query,
                        "count": 10,
                        "language": "en",
                        "format": "json"
                    },
                    headers={"User-Agent": "WeatherAI-Geocoder"}
                )
                response.raise_for_status()
                data = response.json()

                # Transform results to standardized format
                results = []
                if "results" in data:
                    for item in data["results"]:
                        result = {
                            "name": item.get("name", ""),
                            "country": item.get("country", ""),
                            "lat": item.get("latitude"),
                            "lon": item.get("longitude"),
                            "timezone": item.get("timezone", "UTC"),
                            "admin1": item.get("admin1", ""),  # State/Province
                            "admin2": item.get("admin2", ""),  # County/District
                        }
                        # Create display name
                        name_parts = [result["name"]]
                        if result["admin1"]:
                            name_parts.append(result["admin1"])
                        if result["country"]:
                            name_parts.append(result["country"])
                        result["display_name"] = ", ".join(name_parts)
                        results.append(result)

                # Cache results (simple TTL would be better in production)
                _geocoding_cache[cache_key] = results
                logger.info(f"Cached geocoding result for: {query}, found {len(results)} results")
                return results

        except httpx.TimeoutException as e:
            logger.error(f"Geocoding request timed out for query: {query}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Geocoding service temporarily unavailable"
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Geocoding API error for query {query}: {e.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Geocoding service error"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected geocoding error for query {query}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Geocoding search failed"
            ) from e


# Dependency to get geocoding service
async def get_geocoding_service() -> GeocodingService:
    """Dependency to get GeocodingService."""
    return GeocodingService()


@router.get("/search")
async def search_locations(
    query: str = Query(..., min_length=2, max_length=100, description="Location search query"),
    current_user: User = Depends(get_current_user),
    geocoding_service: GeocodingService = Depends(get_geocoding_service),
):
    """Search for locations using geocoding service.

    Requires authentication to prevent abuse. Results are cached for performance.
    """
    await check_rate_limit("geo_search", current_user)

    if len(query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters long"
        )

    results = await geocoding_service.search(query)

    return {
        "query": query,
        "results": results,
        "count": len(results)
    }
