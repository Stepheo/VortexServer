from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Gift(BaseModel):
    """Gift model."""

    __tablename__ = "gifts"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    real_rarity: Mapped[float] = mapped_column(Float, nullable=False)
    visual_rarity: Mapped[float] = mapped_column(Float, nullable=False)
    rarity_color: Mapped[str] = mapped_column(String(20), nullable=False)

    inventory_items = relationship(
        "InventoryItem",
        back_populates="gift",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - simple representation
        return f"Gift(id={self.id}, name={self.name})"