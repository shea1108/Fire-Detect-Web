from .routes import bp as admin_routes
from .models import bp as  admin_models
from .users import bp as admin_users
from .rbac import bp as admin_rbac
from .stats import bp as admin_stats
__all__ = [
    "admin_routes",
    "admin_models",
    "admin_users",
    "admin_rbac",
    "admin_stats"
]

