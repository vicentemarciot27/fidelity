"""
System resource schemas for Admin API: Device, ApiKey, AuditLog
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime


# Device schemas
class DeviceCreate(BaseModel):
    store_id: UUID4 = Field(..., description="ID da loja")
    name: str = Field(..., description="Nome do dispositivo")


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nome do dispositivo")
    is_active: Optional[bool] = Field(None, description="Status ativo")


class DeviceResponse(BaseModel):
    id: UUID4
    store_id: UUID4
    name: str
    registration_code: str
    last_seen_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# API Key schemas
class ApiKeyCreate(BaseModel):
    customer_id: Optional[UUID4] = Field(None, description="ID do cliente (None para global)")
    name: str = Field(..., description="Nome da chave")
    scopes: List[str] = Field(default_factory=list, description="Escopos de acesso")


class ApiKeyResponse(BaseModel):
    id: UUID4
    customer_id: Optional[UUID4]
    name: str
    key: Optional[str]  # Only returned on creation
    scopes: List[str]
    created_at: datetime
    revoked_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Audit Log schemas
class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: Optional[UUID4]
    actor_device_id: Optional[UUID4]
    action: str
    target_table: Optional[str]
    target_id: Optional[str]
    before: Optional[dict]
    after: Optional[dict]
    ip: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
