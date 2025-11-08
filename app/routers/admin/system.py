"""
System resource management routes for Admin API: Device, ApiKey, AuditLog
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import UUID4
from typing import Optional
from datetime import datetime, timezone
import math
import secrets
import string
import bcrypt

from database import get_db
from ...models import business as business_models
from ...models import system as system_models
from ...models import user as user_models
from ...schemas.admin import system as system_schemas
from ...core.security import get_current_active_user

router = APIRouter(prefix="/admin", tags=["admin-system"])


def paginate_query(query, page: int, page_size: int):
    """Helper function for pagination"""
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if page_size > 0 else 0
    }


def generate_registration_code(length: int = 8) -> str:
    """Generate a short alphanumeric registration code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key(length: int = 32) -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(length)


# ========= Device endpoints =========
@router.post("/devices", response_model=system_schemas.DeviceResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Registrar dispositivo PDV")
def create_device(
    data: system_schemas.DeviceCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Registra um novo dispositivo PDV e gera código de pareamento.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se store existe
    store = db.query(business_models.Store).filter(
        business_models.Store.id == data.store_id
    ).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    try:
        # Gerar código de registro
        registration_code = generate_registration_code()
        
        device = business_models.Device(
            store_id=data.store_id,
            name=data.name,
            registration_code=registration_code,
            is_active=True
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating device"
        )


@router.get("/devices", summary="Listar dispositivos")
def list_devices(
    store_id: Optional[UUID4] = Query(None, description="Filtrar por loja"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista dispositivos com paginação.
    Pode filtrar por store_id e status ativo.
    """
    query = db.query(business_models.Device)
    
    if store_id:
        query = query.filter(business_models.Device.store_id == store_id)
    
    if is_active is not None:
        query = query.filter(business_models.Device.is_active == is_active)
    
    query = query.order_by(business_models.Device.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/devices/{device_id}", response_model=system_schemas.DeviceResponse,
            summary="Obter detalhes do dispositivo")
def get_device(
    device_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um dispositivo específico.
    """
    device = db.query(business_models.Device).filter(
        business_models.Device.id == device_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device


@router.patch("/devices/{device_id}", response_model=system_schemas.DeviceResponse,
              summary="Atualizar dispositivo")
def update_device(
    device_id: UUID4,
    data: system_schemas.DeviceUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um dispositivo (ex: nome, status ativo).
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    device = db.query(business_models.Device).filter(
        business_models.Device.id == device_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)
        
        db.commit()
        db.refresh(device)
        return device
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating device"
        )


@router.delete("/devices/{device_id}", summary="Remover dispositivo")
def delete_device(
    device_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove um dispositivo.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    device = db.query(business_models.Device).filter(
        business_models.Device.id == device_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    try:
        db.delete(device)
        db.commit()
        return {"message": "Device deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting device"
        )


# ========= API Key endpoints =========
@router.post("/api-keys", response_model=system_schemas.ApiKeyResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar chave de API")
def create_api_key(
    data: system_schemas.ApiKeyCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova chave de API.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    
    IMPORTANTE: A chave é retornada apenas nesta chamada e não pode ser recuperada depois.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        # Gerar chave de API
        api_key = generate_api_key()
        key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())
        
        api_key_record = system_models.ApiKey(
            customer_id=data.customer_id,
            name=data.name,
            key_hash=key_hash,
            scopes=data.scopes
        )
        db.add(api_key_record)
        db.commit()
        db.refresh(api_key_record)
        
        # Retornar resposta com a chave (apenas nesta chamada)
        return {
            "id": api_key_record.id,
            "customer_id": api_key_record.customer_id,
            "name": api_key_record.name,
            "key": api_key,  # Retorna a chave apenas nesta chamada
            "scopes": api_key_record.scopes,
            "created_at": api_key_record.created_at,
            "revoked_at": api_key_record.revoked_at
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating API key"
        )


@router.get("/api-keys", summary="Listar chaves de API")
def list_api_keys(
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    include_revoked: bool = Query(False, description="Incluir chaves revogadas"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista chaves de API com paginação.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(system_models.ApiKey)
    
    if customer_id:
        query = query.filter(system_models.ApiKey.customer_id == customer_id)
    
    if not include_revoked:
        query = query.filter(system_models.ApiKey.revoked_at == None)
    
    query = query.order_by(system_models.ApiKey.created_at.desc())
    
    result = paginate_query(query, page, page_size)
    
    # Formatar resposta (sem retornar a chave)
    items_formatted = []
    for item in result["items"]:
        items_formatted.append({
            "id": item.id,
            "customer_id": item.customer_id,
            "name": item.name,
            "key": None,  # Não retornar a chave
            "scopes": item.scopes,
            "created_at": item.created_at,
            "revoked_at": item.revoked_at
        })
    
    result["items"] = items_formatted
    return result


@router.delete("/api-keys/{key_id}", summary="Revogar chave de API")
def revoke_api_key(
    key_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoga uma chave de API (soft delete).
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    api_key = db.query(system_models.ApiKey).filter(
        system_models.ApiKey.id == key_id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )
    
    try:
        api_key.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "API key revoked successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error revoking API key"
        )


# ========= Audit Log endpoints =========
@router.get("/audit-log", summary="Listar logs de auditoria")
def list_audit_logs(
    actor_user_id: Optional[UUID4] = Query(None, description="Filtrar por usuário"),
    action: Optional[str] = Query(None, description="Filtrar por ação"),
    target_table: Optional[str] = Query(None, description="Filtrar por tabela alvo"),
    start_date: Optional[datetime] = Query(None, description="Data de início"),
    end_date: Optional[datetime] = Query(None, description="Data de fim"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista logs de auditoria com paginação e filtros.
    Requer permissão de ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view audit logs"
        )
    
    query = db.query(system_models.AuditLog)
    
    if actor_user_id:
        query = query.filter(system_models.AuditLog.actor_user_id == actor_user_id)
    
    if action:
        query = query.filter(system_models.AuditLog.action == action)
    
    if target_table:
        query = query.filter(system_models.AuditLog.target_table == target_table)
    
    if start_date:
        query = query.filter(system_models.AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(system_models.AuditLog.created_at <= end_date)
    
    query = query.order_by(system_models.AuditLog.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/audit-log/{log_id}", response_model=system_schemas.AuditLogResponse,
            summary="Obter detalhes do log de auditoria")
def get_audit_log(
    log_id: int,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um log de auditoria específico.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view audit logs"
        )
    
    log = db.query(system_models.AuditLog).filter(
        system_models.AuditLog.id == log_id
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return log
