from fastapi import APIRouter
from app.api.v1.routes import auth, locations, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(locations.router, prefix="/v1")