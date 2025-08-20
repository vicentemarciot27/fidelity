import enum

# Já existentes no models.py
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

# Novos enums baseados em strings hard-codadas

class UserRoleEnum(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    CUSTOMER_ADMIN = "CUSTOMER_ADMIN"
    FRANCHISE_MANAGER = "FRANCHISE_MANAGER"
    STORE_MANAGER = "STORE_MANAGER"
    CASHIER = "CASHIER"

class StaffRoleEnum(str, enum.Enum):
    STORE_MANAGER = "STORE_MANAGER"
    CASHIER = "CASHIER"

class ActionTypeEnum(str, enum.Enum):
    COUPON_ISSUE = "COUPON_ISSUE"
    COUPON_REDEEM = "COUPON_REDEEM"
    POINTS_EARNED = "POINTS_EARNED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_REGISTER = "USER_REGISTER"

class AssetTypeEnum(str, enum.Enum):
    BANNER = "BANNER"
    THUMB = "THUMB" 
    DETAIL = "DETAIL"

class OutboxStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class OrderSourceEnum(str, enum.Enum):
    PDV = "PDV"
    MARKETPLACE = "MARKETPLACE"
    ECOMMERCE = "ECOMMERCE"
