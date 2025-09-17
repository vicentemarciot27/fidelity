"""
Authentication and token schemas
"""
from pydantic import BaseModel, UUID4
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: UUID4
    role: str
    customer_id: Optional[UUID4] = None
    franchise_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None
    person_id: Optional[UUID4] = None
    exp: int

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    cpf: str
    phone: Optional[str] = None
    role: str = "USER"
