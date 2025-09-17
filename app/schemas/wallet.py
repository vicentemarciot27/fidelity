"""
Wallet and points balance schemas
"""
from pydantic import BaseModel, UUID4
from typing import List, Optional

class PointBalance(BaseModel):
    scope: str
    scope_id: Optional[UUID4]
    points: int
    as_brl: Optional[float] = None

class CouponBalance(BaseModel):
    offer_id: UUID4
    available_count: int
    redeemed_count: int

class WalletResponse(BaseModel):
    balances: List[PointBalance]
    coupons: List[CouponBalance]
