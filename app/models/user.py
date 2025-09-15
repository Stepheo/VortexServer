"""Example user model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    inventory = relationship(
        "Inventory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
        uselist=False
    )

    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"User(id={self.id}, username={self.username})"