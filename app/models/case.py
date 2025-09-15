"""Case model."""
from __future__ import annotations

from sqlalchemy import String, Float, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, Base

# Association table between cases and gifts
case_gifts = Table(
    "case_gifts",
    Base.metadata,
    Column("case_id", ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("gift_id", ForeignKey("gifts.id", ondelete="CASCADE"), primary_key=True),
)


class Case(BaseModel):
    __tablename__ = "cases"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    img: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    gifts = relationship(
        "Gift",
        secondary=case_gifts,
        back_populates="cases",
        lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Case(id={self.id}, name={self.name}, price={self.price})"