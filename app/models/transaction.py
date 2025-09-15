"""Transaction model."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Transaction(BaseModel):
    """Transaction model."""

    __tablename__ = "transactions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)

    user: Mapped["User"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type='{self.type}')"
