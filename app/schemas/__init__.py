"""
All schema imports for easy access
"""
from .auth import Token, TokenData, UserLogin, UserCreate
from .wallet import PointBalance, CouponBalance, WalletResponse
from .coupons import BuyCouponRequest, BuyCouponResponse, AttemptCouponRequest, AttemptCouponResponse, RedeemCouponRequest
from .points import EarnPointsRequest, EarnPointsResponse

__all__ = [
    # Auth schemas
    'Token', 'TokenData', 'UserLogin', 'UserCreate',
    # Wallet schemas
    'PointBalance', 'CouponBalance', 'WalletResponse',
    # Coupon schemas
    'BuyCouponRequest', 'BuyCouponResponse', 'AttemptCouponRequest', 'AttemptCouponResponse', 'RedeemCouponRequest',
    # Points schemas
    'EarnPointsRequest', 'EarnPointsResponse'
]
