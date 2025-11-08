"""
Configuration management routes for Admin API: PointRules, MarketplaceRules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import UUID4
from typing import Optional
import math

from database import get_db
from ...models import points as points_models
from ...models import config as config_models
from ...models import user as user_models
from ...schemas.admin import config as config_schemas
from ...core.security import get_current_active_user

router = APIRouter(prefix="/admin", tags=["admin-config"])


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


# ========= Point Rules endpoints =========
@router.post("/point-rules", response_model=config_schemas.PointRulesResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar regra de pontos")
def create_point_rule(
    data: config_schemas.PointRulesCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova regra de pontos para um escopo específico.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Validar scope
    if data.scope not in ["GLOBAL", "CUSTOMER", "FRANCHISE", "STORE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scope"
        )
    
    # Validar IDs de acordo com o scope
    if data.scope == "CUSTOMER" and not data.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_id required for CUSTOMER scope"
        )
    elif data.scope == "FRANCHISE" and not data.franchise_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="franchise_id required for FRANCHISE scope"
        )
    elif data.scope == "STORE" and not data.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="store_id required for STORE scope"
        )
    elif data.scope == "GLOBAL" and (data.customer_id or data.franchise_id or data.store_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GLOBAL scope should not have customer_id, franchise_id, or store_id"
        )
    
    try:
        rule = points_models.PointRules(**data.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating point rule"
        )


@router.get("/point-rules", summary="Listar regras de pontos")
def list_point_rules(
    scope: Optional[str] = Query(None, description="Filtrar por escopo"),
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    franchise_id: Optional[UUID4] = Query(None, description="Filtrar por franquia"),
    store_id: Optional[UUID4] = Query(None, description="Filtrar por loja"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista regras de pontos com paginação.
    Pode filtrar por scope e IDs de entidades.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(points_models.PointRules)
    
    if scope:
        query = query.filter(points_models.PointRules.scope == scope)
    
    if customer_id:
        query = query.filter(points_models.PointRules.customer_id == customer_id)
    
    if franchise_id:
        query = query.filter(points_models.PointRules.franchise_id == franchise_id)
    
    if store_id:
        query = query.filter(points_models.PointRules.store_id == store_id)
    
    query = query.order_by(points_models.PointRules.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/point-rules/{rule_id}", response_model=config_schemas.PointRulesResponse,
            summary="Obter detalhes da regra de pontos")
def get_point_rule(
    rule_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma regra de pontos específica.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    rule = db.query(points_models.PointRules).filter(
        points_models.PointRules.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point rule not found"
        )
    
    return rule


@router.patch("/point-rules/{rule_id}", response_model=config_schemas.PointRulesResponse,
              summary="Atualizar regra de pontos")
def update_point_rule(
    rule_id: UUID4,
    data: config_schemas.PointRulesUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza uma regra de pontos existente.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    rule = db.query(points_models.PointRules).filter(
        points_models.PointRules.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point rule not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        db.commit()
        db.refresh(rule)
        return rule
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating point rule"
        )


@router.delete("/point-rules/{rule_id}", summary="Deletar regra de pontos")
def delete_point_rule(
    rule_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma regra de pontos.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    rule = db.query(points_models.PointRules).filter(
        points_models.PointRules.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point rule not found"
        )
    
    try:
        db.delete(rule)
        db.commit()
        return {"message": "Point rule deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting point rule"
        )


# ========= Marketplace Rules endpoints =========
@router.post("/marketplace-rules", response_model=config_schemas.MarketplaceRulesResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar regras de marketplace")
def create_marketplace_rules(
    data: config_schemas.MarketplaceRulesCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria regras de marketplace para um cliente.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se já existe regra para este cliente
    existing = db.query(config_models.CustomerMarketplaceRules).filter(
        config_models.CustomerMarketplaceRules.customer_id == data.customer_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Marketplace rules already exist for this customer"
        )
    
    try:
        rules = config_models.CustomerMarketplaceRules(**data.model_dump())
        db.add(rules)
        db.commit()
        db.refresh(rules)
        return rules
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating marketplace rules"
        )


@router.get("/marketplace-rules", summary="Listar regras de marketplace")
def list_marketplace_rules(
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista regras de marketplace com paginação.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(config_models.CustomerMarketplaceRules)
    
    if customer_id:
        query = query.filter(config_models.CustomerMarketplaceRules.customer_id == customer_id)
    
    query = query.order_by(config_models.CustomerMarketplaceRules.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/marketplace-rules/{customer_id}", response_model=config_schemas.MarketplaceRulesResponse,
            summary="Obter regras de marketplace do cliente")
def get_marketplace_rules(
    customer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna regras de marketplace de um cliente específico.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    rules = db.query(config_models.CustomerMarketplaceRules).filter(
        config_models.CustomerMarketplaceRules.customer_id == customer_id
    ).first()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketplace rules not found for this customer"
        )
    
    return rules


@router.patch("/marketplace-rules/{customer_id}", response_model=config_schemas.MarketplaceRulesResponse,
              summary="Atualizar regras de marketplace")
def update_marketplace_rules(
    customer_id: UUID4,
    data: config_schemas.MarketplaceRulesUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza regras de marketplace de um cliente.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    rules = db.query(config_models.CustomerMarketplaceRules).filter(
        config_models.CustomerMarketplaceRules.customer_id == customer_id
    ).first()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketplace rules not found for this customer"
        )
    
    try:
        rules.rules = data.rules
        db.commit()
        db.refresh(rules)
        return rules
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating marketplace rules"
        )


@router.delete("/marketplace-rules/{customer_id}", summary="Deletar regras de marketplace")
def delete_marketplace_rules(
    customer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta regras de marketplace de um cliente.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only global admins can delete marketplace rules"
        )
    
    rules = db.query(config_models.CustomerMarketplaceRules).filter(
        config_models.CustomerMarketplaceRules.customer_id == customer_id
    ).first()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketplace rules not found for this customer"
        )
    
    try:
        db.delete(rules)
        db.commit()
        return {"message": "Marketplace rules deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting marketplace rules"
        )
