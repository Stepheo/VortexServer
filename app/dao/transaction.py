"""Transaction Data Access Object."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.models.transaction import Transaction


class TransactionDAO(BaseDAO[Transaction]):
    """Transaction DAO for specialized queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)


def get_transaction_dao(session: AsyncSession) -> TransactionDAO:
    """Factory function for TransactionDAO."""
    return TransactionDAO(session)
