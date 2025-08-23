from fastapi import APIRouter

from app.api.v1.routes import analytics, auth, health, locations, ingestion, location_groups, geo

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(locations.router, prefix="/v1")
api_router.include_router(location_groups.router, prefix="/v1")
api_router.include_router(geo.router, prefix="/v1")
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
api_router.include_router(ingestion.router, prefix="/v1", tags=["ingestion"])
