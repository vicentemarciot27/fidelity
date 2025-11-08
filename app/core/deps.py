"""
Common dependencies used across routers
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from .security import (
    get_current_active_user,
    get_admin_user,
    get_current_customer_admin,
    require_role
)
from ..models.user import AppUser

# Database dependency
def get_database() -> Session:
    """Database dependency"""
    return Depends(get_db)

# User dependencies
def get_active_user() -> AppUser:
    """Active user dependency"""
    return Depends(get_current_active_user)

def get_admin() -> AppUser:
    """Admin user dependency"""
    return Depends(get_admin_user)

def get_customer_admin() -> AppUser:
    """Customer admin dependency"""
    return Depends(get_current_customer_admin)
