"""
Business entity schemas for Admin API: Customer, Franchise, Store
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


# Customer schemas
class CustomerCreate(BaseModel):
    cnpj: str = Field(..., description="CNPJ do cliente")
    name: str = Field(..., description="Nome do cliente")
    contact_email: Optional[str] = Field(None, description="Email de contato")
    phone: Optional[str] = Field(None, description="Telefone")


class CustomerUpdate(BaseModel):
    cnpj: Optional[str] = Field(None, description="CNPJ do cliente")
    name: Optional[str] = Field(None, description="Nome do cliente")
    contact_email: Optional[str] = Field(None, description="Email de contato")
    phone: Optional[str] = Field(None, description="Telefone")


class CustomerResponse(BaseModel):
    id: UUID4
    cnpj: str
    name: str
    contact_email: Optional[str]
    phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Franchise schemas
class FranchiseCreate(BaseModel):
    customer_id: UUID4 = Field(..., description="ID do cliente")
    cnpj: Optional[str] = Field(None, description="CNPJ da franquia")
    name: str = Field(..., description="Nome da franquia")


class FranchiseUpdate(BaseModel):
    cnpj: Optional[str] = Field(None, description="CNPJ da franquia")
    name: Optional[str] = Field(None, description="Nome da franquia")


class FranchiseResponse(BaseModel):
    id: UUID4
    customer_id: UUID4
    cnpj: Optional[str]
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Store schemas
class StoreCreate(BaseModel):
    franchise_id: UUID4 = Field(..., description="ID da franquia")
    cnpj: Optional[str] = Field(None, description="CNPJ da loja")
    name: str = Field(..., description="Nome da loja")
    location: Optional[dict] = Field(None, description="Localização (JSONB)")


class StoreUpdate(BaseModel):
    cnpj: Optional[str] = Field(None, description="CNPJ da loja")
    name: Optional[str] = Field(None, description="Nome da loja")
    location: Optional[dict] = Field(None, description="Localização (JSONB)")


class StoreResponse(BaseModel):
    id: UUID4
    franchise_id: UUID4
    cnpj: Optional[str]
    name: str
    location: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True
