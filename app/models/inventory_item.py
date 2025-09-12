"""InventoryItem model linking inventory and gifts."""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class InventoryItem(BaseModel):
    """Gift entry inside a user's inventory."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("inventory_id", "gift_id", name="uq_inventory_gift"),
    )

    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventories.id"), nullable=False)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gifts.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    inventory = relationship("Inventory", back_populates="items", lazy="joined")
    gift = relationship("Gift", back_populates="inventory_items", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"InventoryItem(id={self.id}, inventory_id={self.inventory_id}, gift_id={self.gift_id}, quantity={self.quantity})"
