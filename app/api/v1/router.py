"""API v1 router."""

from fastapi import APIRouter, Depends

from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.auth_telegram import router as auth_router
from app.api.v1.endpoints.gifts import router as gifts_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.deps.current_user import get_current_user
from app.config.settings import settings

# Create API v1 router
api_router = APIRouter(prefix=settings.api_v1_prefix)

# Include endpoint routers
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(gifts_router)
api_router.include_router(inventory_router)


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