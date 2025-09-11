"""Data Access Object (DAO) module."""

from .base import BaseDAO, get_dao
from .user import UserDAO

__all__ = ["BaseDAO", "get_dao", "UserDAO"]