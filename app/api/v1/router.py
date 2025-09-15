"""API v1 router (public minimal surface for frontend).

Includes only authentication, current user, and read-only cases endpoints.
"""

from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.upgrade import router as upgrade_router
from app.config.settings import settings

# Create API v1 router
api_router = APIRouter(prefix=settings.api_v1_prefix)

# Include only required endpoint routers
api_router.include_router(cases_router)
api_router.include_router(inventory_router)
api_router.include_router(upgrade_router)


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "VortexServer is running"
    }


# Example protected endpoint
@api_router.get("/me", tags=["auth"])
async def get_me(user=Depends(get_current_user)):
    """Get current Telegram-authenticated user (from JWT cookie)."""
    return {"user": user}