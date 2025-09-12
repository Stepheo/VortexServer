"""SQLAdmin views and configuration."""

from sqladmin import Admin, ModelView
from starlette.applications import Starlette

from app.config.settings import settings
from app.core.database import engine
from app.models.user import User
from app.models.gift import Gift


class UserAdmin(ModelView, model=User):
    """User admin view."""
    
    column_list = [User.id, User.username, User.email, User.full_name, User.created_at, User.inventory]
    column_searchable_list = [User.username, User.email, User.full_name]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    form_excluded_columns = [User.created_at, User.updated_at]
    
    
class GiftAdmin(ModelView, model=Gift):
    column_list = [Gift.id, Gift.name, Gift.real_rarity, Gift.visual_rarity, Gift.rarity_color, Gift.inventory_items]
    form_excluded_columns = [User.created_at, User.updated_at]


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
    
    return admin