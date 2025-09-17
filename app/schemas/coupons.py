"""
Coupon-related schemas
"""
from pydantic import BaseModel, UUID4
from decimal import Decimal
from typing import List, Dict, Any, Optional

class BuyCouponRequest(BaseModel):
    offer_id: UUID4

class BuyCouponResponse(BaseModel):
    coupon_id: UUID4
    code: str
    qr: Dict[str, str]

class AttemptCouponRequest(BaseModel):
    code: str
    order_total_brl: Decimal
    items: Optional[List[Dict[str, Any]]] = None
    store_id: UUID4

class AttemptCouponResponse(BaseModel):
    coupon_id: UUID4
    redeemable: bool
    discount: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class RedeemCouponRequest(BaseModel):
    coupon_id: UUID4
    order_id: Optional[str] = None
    order: Optional[Dict[str, Any]] = None
