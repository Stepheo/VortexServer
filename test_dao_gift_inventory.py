"""Basic tests for GiftDAO, InventoryDAO, InventoryItemDAO factories and simple logic.
These are light tests using mocks (no DB integration) to validate wiring.
"""

from unittest.mock import Mock

from app.dao.gift import GiftDAO, get_gift_dao
from app.dao.inventory import InventoryDAO, get_inventory_dao
from app.dao.inventory_item import InventoryItemDAO, get_inventory_item_dao
from app.models.gift import Gift
from app.models.inventory import Inventory
from app.models.inventory_item import InventoryItem


def test_gift_dao_factory():
    session = Mock()
    dao = get_gift_dao(session)
    assert isinstance(dao, GiftDAO)
    assert dao.model is Gift
    assert dao.session is session


def test_inventory_dao_factory():
    session = Mock()
    dao = get_inventory_dao(session)
    assert isinstance(dao, InventoryDAO)
    assert dao.model is Inventory


def test_inventory_item_dao_factory():
    session = Mock()
    dao = get_inventory_item_dao(session)
    assert isinstance(dao, InventoryItemDAO)
    assert dao.model is InventoryItem
