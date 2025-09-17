"""
Points system schemas
"""
from pydantic import BaseModel, UUID4
from typing import Dict, Any, Optional

class EarnPointsRequest(BaseModel):
    person_id: Optional[UUID4] = None
    cpf: Optional[str] = None
    order: Dict[str, Any]
    store_id: UUID4

class EarnPointsResponse(BaseModel):
    order_id: UUID4
    points_earned: int
    wallet_snapshot: Dict[str, Any]
