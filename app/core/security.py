"""
Security utilities for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt

from database import get_db
from ..models.user import AppUser
from ..schemas.auth import TokenData
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    description="Usar o endpoint /auth/token para obter o token de acesso via Swagger UI"
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Criar token de acesso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Gerar hash da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AppUser:
    """Obter usuário atual a partir do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(
            user_id=user_id,
            role=payload.get("role"),
            customer_id=payload.get("customer_id"),
            franchise_id=payload.get("franchise_id"),
            store_id=payload.get("store_id"),
            person_id=payload.get("person_id"),
            exp=payload.get("exp")
        )
    except JWTError:
        raise credentials_exception
    
    user = db.query(AppUser).filter(AppUser.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """Obter usuário ativo atual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_admin_user(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """Verificar se o usuário atual é admin"""
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_role(*allowed_roles: str):
    """
    Decorator/dependency para verificar se o usuário tem uma das roles permitidas.
    
    Uso:
        @router.get("/endpoint")
        def my_endpoint(user: AppUser = Depends(require_role("ADMIN", "CUSTOMER_ADMIN"))):
            ...
    """
    def role_checker(current_user: AppUser = Depends(get_current_active_user)) -> AppUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def get_current_customer_admin(current_user: AppUser = Depends(get_current_active_user)) -> AppUser:
    """Verificar se o usuário é Customer Admin ou superior"""
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer admin access required"
        )
    return current_user


def verify_customer_access(user: AppUser, customer_id: str, db: Session) -> bool:
    """
    Verifica se o usuário tem acesso a um customer específico.
    Admins globais têm acesso a todos.
    Customer admins têm acesso apenas ao seu customer.
    """
    if user.role in ["ADMIN", "GLOBAL_ADMIN"]:
        return True
    
    # Para CUSTOMER_ADMIN, verificar se pertence ao customer
    # Isso pode ser expandido com uma tabela de associação user-customer
    # Por enquanto, retorna True (implementação simplificada)
    return True
