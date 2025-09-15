from enum import Enum
from sqlalchemy import String, Float, Enum as SAEnum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.case import case_gifts


class GiftRarity(str, Enum):
    rare = "rare"
    legendary = "legendary"
    ultra = "ultra"


class Gift(BaseModel):
    """Gift model."""

    __tablename__ = "gifts"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    img: Mapped[str | None] = mapped_column(String(255), nullable=True)
    real_rarity: Mapped[float] = mapped_column(Float, nullable=False)
    visual_rarity: Mapped[float] = mapped_column(Float, nullable=False)
    rarity_color: Mapped[GiftRarity] = mapped_column(
        SAEnum(GiftRarity, name="gift_rarity"),
        nullable=False,
        default=GiftRarity.rare,
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    inventory_items = relationship(
        "InventoryItem",
        back_populates="gift",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    cases = relationship(
        "Case",
        secondary=case_gifts,
        back_populates="gifts",
        lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - simple representation
        return f"Gift(id={self.id}, name={self.name})"