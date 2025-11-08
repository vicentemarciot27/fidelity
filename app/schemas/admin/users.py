"""
User and staff management schemas for Admin API
"""
from pydantic import BaseModel, UUID4, EmailStr, Field
from typing import Optional
from datetime import datetime


# User schemas (Admin version)
class UserCreateAdmin(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=6, description="Senha do usuário")
    name: str = Field(..., description="Nome completo da pessoa")
    cpf: str = Field(..., description="CPF da pessoa")
    phone: Optional[str] = Field(None, description="Telefone")
    role: str = Field("USER", description="Perfil do usuário")


class UserUpdateAdmin(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email do usuário")
    name: Optional[str] = Field(None, description="Nome completo da pessoa")
    phone: Optional[str] = Field(None, description="Telefone")
    role: Optional[str] = Field(None, description="Perfil do usuário")
    is_active: Optional[bool] = Field(None, description="Status ativo")


class UserResponse(BaseModel):
    id: UUID4
    person_id: UUID4
    email: str
    role: str
    is_active: bool
    created_at: datetime
    person: dict  # {id, cpf, name, phone}
    
    class Config:
        from_attributes = True


# Store Staff schemas
class StoreStaffCreate(BaseModel):
    user_id: UUID4 = Field(..., description="ID do usuário")
    store_id: UUID4 = Field(..., description="ID da loja")
    role: str = Field(..., description="Papel na loja (STORE_MANAGER, CASHIER)")


class StoreStaffResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    store_id: UUID4
    role: str
    
    class Config:
        from_attributes = True
