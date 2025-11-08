"""
Coupon and offer management schemas for Admin API
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# Coupon Type schemas
class CouponTypeCreate(BaseModel):
    sku_specific: bool = Field(False, description="Se é específico para SKUs")
    redeem_type: str = Field(..., description="Tipo de resgate (BRL, PERCENTAGE, FREE_SKU)")
    discount_amount_brl: Optional[Decimal] = Field(None, description="Valor de desconto em BRL")
    discount_amount_percentage: Optional[Decimal] = Field(None, description="Percentual de desconto")
    valid_skus: Optional[List[str]] = Field(None, description="SKUs válidos (se aplicável)")


class CouponTypeResponse(BaseModel):
    id: UUID4
    sku_specific: bool
    redeem_type: str
    discount_amount_brl: Optional[Decimal]
    discount_amount_percentage: Optional[Decimal]
    valid_skus: Optional[List[str]]
    
    class Config:
        from_attributes = True


# Coupon Offer schemas
class CouponOfferCreate(BaseModel):
    entity_scope: str = Field(..., description="Escopo da entidade (CUSTOMER, FRANCHISE, STORE)")
    entity_id: UUID4 = Field(..., description="ID da entidade")
    coupon_type_id: UUID4 = Field(..., description="ID do tipo de cupom")
    customer_segment: Optional[dict] = Field(None, description="Segmentação de clientes (JSONB)")
    initial_quantity: int = Field(0, ge=0, description="Quantidade inicial")
    max_per_customer: int = Field(0, ge=0, description="Máximo por cliente (0 = ilimitado)")
    is_active: bool = Field(True, description="Se a oferta está ativa")
    start_at: Optional[datetime] = Field(None, description="Data de início")
    end_at: Optional[datetime] = Field(None, description="Data de término")


class CouponOfferUpdate(BaseModel):
    customer_segment: Optional[dict] = Field(None, description="Segmentação de clientes (JSONB)")
    initial_quantity: Optional[int] = Field(None, ge=0, description="Quantidade inicial")
    current_quantity: Optional[int] = Field(None, ge=0, description="Quantidade atual (incremental)")
    max_per_customer: Optional[int] = Field(None, ge=0, description="Máximo por cliente")
    is_active: Optional[bool] = Field(None, description="Se a oferta está ativa")
    start_at: Optional[datetime] = Field(None, description="Data de início")
    end_at: Optional[datetime] = Field(None, description="Data de término")


class CouponOfferResponse(BaseModel):
    id: UUID4
    entity_scope: str
    entity_id: UUID4
    coupon_type_id: UUID4
    customer_segment: Optional[dict]
    initial_quantity: int
    current_quantity: int
    max_per_customer: int
    is_active: bool
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Offer Asset schemas
class OfferAssetCreate(BaseModel):
    offer_id: UUID4 = Field(..., description="ID da oferta")
    kind: str = Field(..., description="Tipo de asset (BANNER, THUMB, DETAIL)")
    url: str = Field(..., description="URL do asset")
    position: int = Field(0, description="Posição de exibição")


class OfferAssetResponse(BaseModel):
    id: UUID4
    offer_id: UUID4
    kind: str
    url: str
    position: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Statistics schemas
class CouponOfferStatsResponse(BaseModel):
    total_issued: int
    total_reserved: int
    total_redeemed: int
    total_cancelled: int
    total_expired: int
    redemption_by_store: List[Dict[str, Any]]
    redemption_timeline: List[Dict[str, Any]]


# Bulk issue schemas
class BulkIssueCouponRequest(BaseModel):
    offer_id: UUID4 = Field(..., description="ID da oferta")
    quantity: int = Field(..., gt=0, description="Quantidade de cupons a emitir")
    segment_criteria: Optional[dict] = Field(None, description="Critérios de segmentação (JSONB)")


class BulkIssueCouponResponse(BaseModel):
    job_id: UUID4
    offer_id: UUID4
    quantity_requested: int
    status: str
    message: str


# Cancel coupon schema
class CancelCouponRequest(BaseModel):
    reason: str = Field(..., description="Motivo do cancelamento")
