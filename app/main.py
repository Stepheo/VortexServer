"""Main FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.admin.views import create_admin
from app.api.v1.router import api_router
from app.config.settings import settings
from app.core.cache import cache_manager
from app.core.database import close_db_connection, create_db_and_tables

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting VortexServer...")
    
    # Initialize database
    logger.info("Initializing database...")
    await create_db_and_tables()
    
    # Initialize cache
    logger.info("Connecting to cache...")
    try:
        await cache_manager.connect()
        logger.info("Cache connected successfully")
    except Exception as e:
        logger.warning(f"Cache connection failed: {e}")
    
    logger.info("VortexServer started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VortexServer...")
    
    # Close cache connection
    await cache_manager.disconnect()
    
    # Close database connection
    await close_db_connection()
    
    logger.info("VortexServer shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="VortexServer",
        description="Extensible FastAPI server with SQLAlchemy, SQLAdmin, DAO pattern, asyncpg, and cache",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Security headers middleware (simple)
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection", "0")  # modern browsers rely on CSP
        # Minimal CSP (adjust as needed)
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
        )
        # HSTS only enable in production with HTTPS
        if not settings.debug:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response
    
    # Add API routes
    app.include_router(api_router)
    
    # Add admin interface
    admin = create_admin(app)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to VortexServer",
            "version": "0.1.0",
            "docs": "/docs",
            "admin": settings.admin_prefix,
            "api": settings.api_v1_prefix,
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )