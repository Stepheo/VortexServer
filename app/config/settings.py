"""Application settings using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Bot settings
    bot_token: str = Field(
        default="your-bot-token-here",
        description="Telegram bot token"
    )
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/vortex_db",
        description="Database URL for asyncpg connection"
    )
    
    # Cache settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching"
    )
    
    # Application settings
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for session management"
    )
    
    # Admin settings
    admin_secret_key: str = Field(
        default="dev-admin-secret-key-change-in-production",
        description="Secret key for admin interface"
    )
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    admin_prefix: str = Field(default="/admin", description="Admin interface prefix")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    # Token / cookie settings
    access_token_expire_minutes: int = Field(
        default=60 * 24,
        description="Access token lifetime in minutes"
    )
    token_cookie_name: str = Field(
        default="access_token",
        description="Name of the cookie to store the access token"
    )
    token_cookie_secure: bool = Field(
        default=False,
        description="Set cookie Secure flag (only sent over HTTPS)"
    )
    token_cookie_httponly: bool = Field(
        default=True,
        description="Set cookie HttpOnly flag (not accessible via JS)"
    )
    token_cookie_samesite: str = Field(
        default="lax",
        description="SameSite attribute for cookie (lax/strict/none)"
    )




# Global settings instance
settings = Settings()