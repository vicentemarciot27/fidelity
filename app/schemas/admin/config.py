"""
Configuration schemas for Admin API: PointRules, MarketplaceRules
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Point Rules schemas
class PointRulesCreate(BaseModel):
    scope: str = Field(..., description="Escopo da regra (GLOBAL, CUSTOMER, FRANCHISE, STORE)")
    customer_id: Optional[UUID4] = Field(None, description="ID do cliente (se scope=CUSTOMER)")
    franchise_id: Optional[UUID4] = Field(None, description="ID da franquia (se scope=FRANCHISE)")
    store_id: Optional[UUID4] = Field(None, description="ID da loja (se scope=STORE)")
    points_per_brl: Optional[Decimal] = Field(None, description="Pontos por BRL gasto")
    expires_in_days: Optional[int] = Field(None, description="Dias até expiração dos pontos")
    extra: Optional[dict] = Field(None, description="Configurações extras (JSONB)")


class PointRulesUpdate(BaseModel):
    points_per_brl: Optional[Decimal] = Field(None, description="Pontos por BRL gasto")
    expires_in_days: Optional[int] = Field(None, description="Dias até expiração dos pontos")
    extra: Optional[dict] = Field(None, description="Configurações extras (JSONB)")


class PointRulesResponse(BaseModel):
    id: UUID4
    scope: str
    customer_id: Optional[UUID4]
    franchise_id: Optional[UUID4]
    store_id: Optional[UUID4]
    points_per_brl: Optional[Decimal]
    expires_in_days: Optional[int]
    extra: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Marketplace Rules schemas
class MarketplaceRulesCreate(BaseModel):
    customer_id: UUID4 = Field(..., description="ID do cliente")
    rules: dict = Field(default_factory=dict, description="Regras do marketplace (JSONB)")


class MarketplaceRulesUpdate(BaseModel):
    rules: dict = Field(..., description="Regras do marketplace (JSONB)")


class MarketplaceRulesResponse(BaseModel):
    id: UUID4
    customer_id: UUID4
    rules: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
