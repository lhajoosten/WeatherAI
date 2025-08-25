from fastapi import APIRouter

from app.api.v1.routes import (
    analytics,
    auth,
    digest,
    geo,
    health,
    ingestion,
    location_groups,
    locations,
    meta,
    rag,
    user,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(user.router, prefix="/v1")
api_router.include_router(locations.router, prefix="/v1")
api_router.include_router(location_groups.router, prefix="/v1")
api_router.include_router(geo.router, prefix="/v1")
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
api_router.include_router(ingestion.router, prefix="/v1", tags=["ingestion"])
api_router.include_router(meta.router, prefix="/v1/meta", tags=["meta"])
api_router.include_router(digest.router, prefix="/v1", tags=["digest"])
api_router.include_router(rag.router, prefix="/v1", tags=["rag"])
