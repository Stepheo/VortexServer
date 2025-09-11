"""Data Access Object (DAO) module."""

from app.dao.base import BaseDAO, get_dao
from app.dao.user import UserDAO, get_user_dao

__all__ = [
    "BaseDAO",
    "get_dao", 
    "UserDAO",
    "get_user_dao",
]