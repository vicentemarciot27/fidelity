"""
Catalog schemas for Admin API: SKU, Category
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


# Category schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., description="Nome da categoria")


class CategoryResponse(BaseModel):
    id: UUID4
    name: str
    
    class Config:
        from_attributes = True


# SKU schemas
class SKUCreate(BaseModel):
    customer_id: UUID4 = Field(..., description="ID do cliente")
    name: str = Field(..., description="Nome do SKU")
    brand: Optional[str] = Field(None, description="Marca")
    category_id: Optional[UUID4] = Field(None, description="ID da categoria")
    custom_metadata: Optional[dict] = Field(None, description="Metadados customizados (JSONB)")


class SKUUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nome do SKU")
    brand: Optional[str] = Field(None, description="Marca")
    category_id: Optional[UUID4] = Field(None, description="ID da categoria")
    custom_metadata: Optional[dict] = Field(None, description="Metadados customizados (JSONB)")


class SKUResponse(BaseModel):
    id: UUID4
    customer_id: UUID4
    name: str
    brand: Optional[str]
    category_id: Optional[UUID4]
    custom_metadata: Optional[dict]
    
    class Config:
        from_attributes = True
