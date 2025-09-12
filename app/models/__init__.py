"""Database models module.

Import model classes here so SQLAlchemy can resolve string-based relationships
without relying on import order elsewhere.
"""

from .base import BaseModel  # noqa: F401
from .user import User  # noqa: F401
from .gift import Gift  # noqa: F401
from .inventory import Inventory  # noqa: F401
from .inventory_item import InventoryItem  # noqa: F401