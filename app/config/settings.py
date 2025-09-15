"""Application settings using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.main import create_app
from aiogram import Bot, Dispatcher


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
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    admin_prefix: str = Field(default="/admin", description="Admin interface prefix")
    
    # Server settings
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    webhook_url: str = ""
    webapp_url: str = ""



# Global settings instance
settings = Settings()

bot = Bot(settings.bot_token)
dp = Dispatcher()
app = create_app()