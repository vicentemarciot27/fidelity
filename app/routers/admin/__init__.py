"""
Admin routers exports
"""
from .business import router as business_router
from .users import router as users_router
from .config import router as config_router
from .coupons import router as coupons_router
from .catalog import router as catalog_router
from .system import router as system_router

__all__ = [
    'business_router',
    'users_router',
    'config_router',
    'coupons_router',
    'catalog_router',
    'system_router'
]
