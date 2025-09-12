"""Inventory model (one per user)."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Inventory(BaseModel):
    """One inventory per user."""

    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_inventory_user"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="inventory", lazy="joined")
    items = relationship("InventoryItem", back_populates="inventory", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Inventory(id={self.id}, user_id={self.user_id})"