"""
Catalog management routes for Admin API: SKU, Category
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import UUID4
from typing import Optional
import math

from database import get_db
from ...models import orders as orders_models
from ...models import user as user_models
from ...schemas.admin import catalog as catalog_schemas
from ...core.security import get_current_active_user

router = APIRouter(prefix="/admin", tags=["admin-catalog"])


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


# ========= Category endpoints =========
@router.post("/categories", response_model=catalog_schemas.CategoryResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar categoria")
def create_category(
    data: catalog_schemas.CategoryCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova categoria de produtos.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        category = orders_models.Category(**data.model_dump())
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating category"
        )


@router.get("/categories", summary="Listar categorias")
def list_categories(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista categorias com paginação.
    """
    query = db.query(orders_models.Category).order_by(orders_models.Category.name)
    return paginate_query(query, page, page_size)


@router.get("/categories/{category_id}", response_model=catalog_schemas.CategoryResponse,
            summary="Obter detalhes da categoria")
def get_category(
    category_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma categoria específica.
    """
    category = db.query(orders_models.Category).filter(
        orders_models.Category.id == category_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.delete("/categories/{category_id}", summary="Deletar categoria")
def delete_category(
    category_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma categoria.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    category = db.query(orders_models.Category).filter(
        orders_models.Category.id == category_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    try:
        db.delete(category)
        db.commit()
        return {"message": "Category deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting category - may be in use by SKUs"
        )


# ========= SKU endpoints =========
@router.post("/skus", response_model=catalog_schemas.SKUResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar SKU")
def create_sku(
    data: catalog_schemas.SKUCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo SKU (produto) associado a um cliente.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se categoria existe (se fornecida)
    if data.category_id:
        category = db.query(orders_models.Category).filter(
            orders_models.Category.id == data.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    try:
        sku = orders_models.SKU(**data.model_dump())
        db.add(sku)
        db.commit()
        db.refresh(sku)
        return sku
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating SKU"
        )


@router.get("/skus", summary="Listar SKUs")
def list_skus(
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    category_id: Optional[UUID4] = Query(None, description="Filtrar por categoria"),
    search: Optional[str] = Query(None, description="Buscar por nome ou marca"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista SKUs com paginação.
    Pode filtrar por customer_id, category_id ou buscar por nome/marca.
    """
    query = db.query(orders_models.SKU)
    
    if customer_id:
        query = query.filter(orders_models.SKU.customer_id == customer_id)
    
    if category_id:
        query = query.filter(orders_models.SKU.category_id == category_id)
    
    if search:
        query = query.filter(
            (orders_models.SKU.name.ilike(f"%{search}%")) |
            (orders_models.SKU.brand.ilike(f"%{search}%"))
        )
    
    query = query.order_by(orders_models.SKU.name)
    return paginate_query(query, page, page_size)


@router.get("/skus/{sku_id}", response_model=catalog_schemas.SKUResponse,
            summary="Obter detalhes do SKU")
def get_sku(
    sku_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um SKU específico.
    """
    sku = db.query(orders_models.SKU).filter(
        orders_models.SKU.id == sku_id
    ).first()
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found"
        )
    
    return sku


@router.patch("/skus/{sku_id}", response_model=catalog_schemas.SKUResponse,
              summary="Atualizar SKU")
def update_sku(
    sku_id: UUID4,
    data: catalog_schemas.SKUUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um SKU.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    sku = db.query(orders_models.SKU).filter(
        orders_models.SKU.id == sku_id
    ).first()
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found"
        )
    
    # Verificar se categoria existe (se fornecida)
    if data.category_id:
        category = db.query(orders_models.Category).filter(
            orders_models.Category.id == data.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sku, key, value)
        
        db.commit()
        db.refresh(sku)
        return sku
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating SKU"
        )


@router.delete("/skus/{sku_id}", summary="Deletar SKU")
def delete_sku(
    sku_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um SKU.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    sku = db.query(orders_models.SKU).filter(
        orders_models.SKU.id == sku_id
    ).first()
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found"
        )
    
    try:
        db.delete(sku)
        db.commit()
        return {"message": "SKU deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting SKU"
        )
