"""
Base enums and types used across models
"""
import enum

class ScopeEnum(str, enum.Enum):
    GLOBAL = "GLOBAL"
    CUSTOMER = "CUSTOMER"
    FRANCHISE = "FRANCHISE"
    STORE = "STORE"

class RedeemTypeEnum(str, enum.Enum):
    BRL = "BRL"
    PERCENTAGE = "PERCENTAGE"
    FREE_SKU = "FREE_SKU"

class CouponStatusEnum(str, enum.Enum):
    CREATED = "CREATED"
    ISSUED = "ISSUED"
    RESERVED = "RESERVED"
    REDEEMED = "REDEEMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
