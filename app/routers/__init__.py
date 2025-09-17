"""
All router imports for easy inclusion in main FastAPI app
"""
from .auth import router as auth_router
from .wallet import router as wallet_router
from .offers import offers_router, coupons_router
from .pdv import router as pdv_router

__all__ = [
    'auth_router',
    'wallet_router', 
    'offers_router',
    'coupons_router',
    'pdv_router'
]
