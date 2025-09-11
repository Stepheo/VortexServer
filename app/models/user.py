"""Example user model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """User model example."""
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    
    def __str__(self) -> str:
        return f"User(id={self.id}, username={self.username})"