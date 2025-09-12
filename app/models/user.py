"""Example user model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))

    inventory = relationship(
        "Inventory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
        uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"User(id={self.id}, username={self.username})"