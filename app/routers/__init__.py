"""
All router imports for easy inclusion in main FastAPI app
"""
from .auth import router as auth_router
from .wallet import router as wallet_router
from .offers import offers_router, coupons_router
from .pdv import router as pdv_router

# Admin routers
from .admin import (
    business_router,
    users_router,
    config_router,
    coupons_router as admin_coupons_router,
    catalog_router,
    system_router
)

__all__ = [
    # Public/Marketplace routers
    'auth_router',
    'wallet_router', 
    'offers_router',
    'coupons_router',
    'pdv_router',
    # Admin routers
    'business_router',
    'users_router',
    'config_router',
    'admin_coupons_router',
    'catalog_router',
    'system_router'
]
