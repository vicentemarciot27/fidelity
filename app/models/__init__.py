"""
Base definitions for all models
"""
from database import Base

# Import all model classes to ensure they are registered with SQLAlchemy
from .user import AppUser, Person, RefreshToken, StoreStaff
from .business import Customer, Franchise, Store, Device
from .points import PointRules, PointTransaction
from .coupons import CouponType, CouponOffer, Coupon, OfferAsset
from .orders import Order, SKU, Category
from .config import CustomerMarketplaceRules
from .system import ApiKey, IdempotencyKey, RateLimitCounter, AuditLog, OutboxEvent

# Views
from .views import create_views

# Make Base available for imports
__all__ = ['Base', 'create_views']
