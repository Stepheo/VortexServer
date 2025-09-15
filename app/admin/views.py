"""SQLAdmin views and configuration."""

from sqladmin import Admin, ModelView
from starlette.applications import Starlette

from app.config.settings import settings
from app.core.database import engine
from app.models.gift import Gift
from app.models.inventory import Inventory
from app.models.transaction import Transaction
from app.models.user import User
from app.models.case import Case


class UserAdmin(ModelView, model=User):
    """User admin view."""

    column_list = [User.id, User.username, User.first_name, User.last_name, User.created_at]
    column_details_list = [
        User.id,
        User.tg_id,
        User.username,
        User.first_name,
        User.last_name,
        User.created_at,
        User.updated_at,
        User.inventory,
        User.transactions,
    ]
    column_searchable_list = [User.username, User.first_name, User.last_name, User.tg_id]
    column_sortable_list = [User.id, User.username, User.created_at]
    column_labels = {
        User.id: "ID",
        User.tg_id: "Telegram ID",
        User.username: "Username",
        User.first_name: "First Name",
        User.last_name: "Last Name",
        User.created_at: "Created",
        User.updated_at: "Updated",
        User.inventory: "Inventory",
        User.transactions: "Transactions",
    }
    form_excluded_columns = [
        User.created_at,
        User.updated_at,
        User.inventory,
        User.transactions,
    ]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class GiftAdmin(ModelView, model=Gift):
    """Gift admin view."""

    column_list = [
        Gift.id,
        Gift.name,
        Gift.real_rarity,
        Gift.visual_rarity,
        Gift.rarity_color,
        Gift.img
    ]
    column_searchable_list = [Gift.name]
    column_sortable_list = [Gift.id, Gift.name, Gift.real_rarity, Gift.visual_rarity]
    column_labels = {
        Gift.real_rarity: "Real Rarity",
        Gift.visual_rarity: "Visual Rarity",
        Gift.rarity_color: "Rarity Color",
    }
    form_excluded_columns = [Gift.created_at, Gift.updated_at, Gift.inventory_items]
    name = "Gift"
    name_plural = "Gifts"
    icon = "fa-solid fa-gift"


class InventoryAdmin(ModelView, model=Inventory):
    """Inventory admin view."""

    column_list = [Inventory.id, Inventory.user, Inventory.items, Inventory.updated_at]
    column_details_list = [
        Inventory.id,
        Inventory.user,
        Inventory.items,
        Inventory.created_at,
        Inventory.updated_at,
        Inventory.items
    ]
    column_labels = {
        Inventory.id: "ID",
        Inventory.user: "User",
        Inventory.items: "Items",
        Inventory.created_at: "Created",
        Inventory.updated_at: "Updated",
    }
    form_excluded_columns = [Inventory.created_at, Inventory.updated_at, Inventory.items]
    name = "Inventory"
    name_plural = "Inventories"
    icon = "fa-solid fa-box"


class TransactionAdmin(ModelView, model=Transaction):
    """Transaction admin view."""

    column_list = [
        Transaction.id,
        Transaction.user,
        Transaction.amount,
        Transaction.type,
        Transaction.status,
        Transaction.created_at,
    ]
    column_details_list = [
        Transaction.id,
        Transaction.user,
        Transaction.amount,
        Transaction.type,
        Transaction.description,
        Transaction.status,
        Transaction.created_at,
        Transaction.updated_at,
    ]
    column_searchable_list = [Transaction.type, Transaction.status]
    column_sortable_list = [
        Transaction.id,
        Transaction.amount,
        Transaction.created_at,
    ]
    column_labels = {
        Transaction.id: "ID",
        Transaction.user: "User",
        Transaction.amount: "Amount",
        Transaction.type: "Type",
        Transaction.description: "Description",
        Transaction.status: "Status",
        Transaction.created_at: "Created",
        Transaction.updated_at: "Updated",
    }
    form_excluded_columns = [Transaction.created_at, Transaction.updated_at, Transaction.user]
    name = "Transaction"
    name_plural = "Transactions"
    icon = "fa-solid fa-money-bill-transfer"


class CaseAdmin(ModelView, model=Case):
    """Case admin view."""

    column_list = [Case.id, Case.name, Case.price, Case.img, Case.gifts, Case.created_at]
    column_searchable_list = [Case.name]
    column_sortable_list = [Case.id, Case.name, Case.price, Case.created_at]
    form_excluded_columns = [Case.created_at, Case.updated_at]
    name = "Case"
    name_plural = "Cases"
    icon = "fa-solid fa-box-open"


def create_admin(app: Starlette) -> Admin:
    """Create and configure SQLAdmin instance."""
    admin = Admin(
        app=app,
        engine=engine,
        title="VortexServer Admin",
        base_url=settings.admin_prefix,
    )

    # Add model views
    admin.add_view(UserAdmin)
    admin.add_view(GiftAdmin)
    admin.add_view(InventoryAdmin)
    admin.add_view(TransactionAdmin)
    admin.add_view(CaseAdmin)

    return admin