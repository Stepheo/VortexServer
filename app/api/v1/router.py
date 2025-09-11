"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints.users import router as users_router
from app.config.settings import settings

# Create API v1 router
api_router = APIRouter(prefix=settings.api_v1_prefix)

# Include endpoint routers
api_router.include_router(users_router)


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "VortexServer is running"
    }