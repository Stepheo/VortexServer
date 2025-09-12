"""Data Access Object (DAO) module."""

from app.dao.base import BaseDAO, get_dao
from app.dao.user import UserDAO, get_user_dao
from app.dao.gift import GiftDAO, get_gift_dao
from app.dao.inventory import InventoryDAO, get_inventory_dao
from app.dao.inventory_item import InventoryItemDAO, get_inventory_item_dao

__all__ = [
    "BaseDAO",
    "get_dao", 
    "UserDAO", "get_user_dao",
    "GiftDAO", "get_gift_dao",
    "InventoryDAO", "get_inventory_dao",
    "InventoryItemDAO", "get_inventory_item_dao",
]