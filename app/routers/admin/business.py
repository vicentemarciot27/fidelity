"""
Business entity management routes for Admin API: Customer, Franchise, Store
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import UUID4
from typing import Optional
import math

from database import get_db
from ...models import business as business_models
from ...schemas.admin import business as business_schemas
from ...core.security import get_current_active_user
from ...models import user as user_models

router = APIRouter(prefix="/admin", tags=["admin-business"])


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


# ========= Customer endpoints =========
@router.post("/customers", response_model=business_schemas.CustomerResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar cliente")
def create_customer(
    data: business_schemas.CustomerCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente (tenant) no sistema.
    Requer permissão de ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create customers"
        )
    
    # Verificar se CNPJ já existe
    existing = db.query(business_models.Customer).filter(
        business_models.Customer.cnpj == data.cnpj
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ already registered"
        )
    
    try:
        customer = business_models.Customer(**data.model_dump())
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating customer"
        )


@router.get("/customers", summary="Listar clientes")
def list_customers(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou CNPJ"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os clientes com paginação.
    Acesso permitido para todos.
    """
    
    query = db.query(business_models.Customer)
    
    if search:
        query = query.filter(
            (business_models.Customer.name.ilike(f"%{search}%")) |
            (business_models.Customer.cnpj.ilike(f"%{search}%"))
        )
    
    query = query.order_by(business_models.Customer.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/customers/{customer_id}", response_model=business_schemas.CustomerResponse,
            summary="Obter detalhes do cliente")
def get_customer(
    customer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um cliente específico.
    Acesso permitido para usuários autenticados.
    """
    customer = db.query(business_models.Customer).filter(
        business_models.Customer.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.patch("/customers/{customer_id}", response_model=business_schemas.CustomerResponse,
              summary="Atualizar cliente")
def update_customer(
    customer_id: UUID4,
    data: business_schemas.CustomerUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um cliente.
    Requer permissão de ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update customers"
        )
    
    customer = db.query(business_models.Customer).filter(
        business_models.Customer.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer, key, value)
        
        db.commit()
        db.refresh(customer)
        return customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating customer"
        )


@router.delete("/customers/{customer_id}", summary="Deletar cliente")
def delete_customer(
    customer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um cliente (com cascata para franchises e stores).
    Requer permissão de ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete customers"
        )
    
    customer = db.query(business_models.Customer).filter(
        business_models.Customer.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    try:
        db.delete(customer)
        db.commit()
        return {"message": "Customer deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting customer"
        )


# ========= Franchise endpoints =========
@router.post("/franchises", response_model=business_schemas.FranchiseResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar franquia")
def create_franchise(
    data: business_schemas.FranchiseCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova franquia associada a um cliente.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se customer existe
    customer = db.query(business_models.Customer).filter(
        business_models.Customer.id == data.customer_id
    ).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verificar se CNPJ já existe (se fornecido)
    if data.cnpj:
        existing = db.query(business_models.Franchise).filter(
            business_models.Franchise.cnpj == data.cnpj
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ already registered"
            )
    
    try:
        franchise = business_models.Franchise(**data.model_dump())
        db.add(franchise)
        db.commit()
        db.refresh(franchise)
        return franchise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating franchise"
        )


@router.get("/franchises", summary="Listar franquias")
def list_franchises(
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista franquias com paginação.
    Pode filtrar por customer_id.
    """
    query = db.query(business_models.Franchise)
    
    if customer_id:
        query = query.filter(business_models.Franchise.customer_id == customer_id)
    
    query = query.order_by(business_models.Franchise.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/franchises/{franchise_id}", response_model=business_schemas.FranchiseResponse,
            summary="Obter detalhes da franquia")
def get_franchise(
    franchise_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma franquia específica.
    """
    franchise = db.query(business_models.Franchise).filter(
        business_models.Franchise.id == franchise_id
    ).first()
    
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Franchise not found"
        )
    
    return franchise


@router.patch("/franchises/{franchise_id}", response_model=business_schemas.FranchiseResponse,
              summary="Atualizar franquia")
def update_franchise(
    franchise_id: UUID4,
    data: business_schemas.FranchiseUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de uma franquia.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    franchise = db.query(business_models.Franchise).filter(
        business_models.Franchise.id == franchise_id
    ).first()
    
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Franchise not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(franchise, key, value)
        
        db.commit()
        db.refresh(franchise)
        return franchise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating franchise"
        )


@router.delete("/franchises/{franchise_id}", summary="Deletar franquia")
def delete_franchise(
    franchise_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma franquia (com cascata para stores).
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    franchise = db.query(business_models.Franchise).filter(
        business_models.Franchise.id == franchise_id
    ).first()
    
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Franchise not found"
        )
    
    try:
        db.delete(franchise)
        db.commit()
        return {"message": "Franchise deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting franchise"
        )


# ========= Store endpoints =========
@router.post("/stores", response_model=business_schemas.StoreResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar loja")
def create_store(
    data: business_schemas.StoreCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova loja associada a uma franquia.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se franchise existe
    franchise = db.query(business_models.Franchise).filter(
        business_models.Franchise.id == data.franchise_id
    ).first()
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Franchise not found"
        )
    
    # Verificar se CNPJ já existe (se fornecido)
    if data.cnpj:
        existing = db.query(business_models.Store).filter(
            business_models.Store.cnpj == data.cnpj
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ already registered"
            )
    
    try:
        store = business_models.Store(**data.model_dump())
        db.add(store)
        db.commit()
        db.refresh(store)
        return store
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating store"
        )


@router.get("/stores", summary="Listar lojas")
def list_stores(
    franchise_id: Optional[UUID4] = Query(None, description="Filtrar por franquia"),
    customer_id: Optional[UUID4] = Query(None, description="Filtrar por cliente"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista lojas com paginação.
    Pode filtrar por franchise_id ou customer_id.
    """
    query = db.query(business_models.Store)
    
    if franchise_id:
        query = query.filter(business_models.Store.franchise_id == franchise_id)
    
    if customer_id:
        # Join com franchise para filtrar por customer
        query = query.join(business_models.Franchise).filter(
            business_models.Franchise.customer_id == customer_id
        )
    
    query = query.order_by(business_models.Store.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/stores/{store_id}", response_model=business_schemas.StoreResponse,
            summary="Obter detalhes da loja")
def get_store(
    store_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma loja específica.
    """
    store = db.query(business_models.Store).filter(
        business_models.Store.id == store_id
    ).first()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    return store


@router.patch("/stores/{store_id}", response_model=business_schemas.StoreResponse,
              summary="Atualizar loja")
def update_store(
    store_id: UUID4,
    data: business_schemas.StoreUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de uma loja.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    store = db.query(business_models.Store).filter(
        business_models.Store.id == store_id
    ).first()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(store, key, value)
        
        db.commit()
        db.refresh(store)
        return store
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating store"
        )


@router.delete("/stores/{store_id}", summary="Deletar loja")
def delete_store(
    store_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma loja.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    store = db.query(business_models.Store).filter(
        business_models.Store.id == store_id
    ).first()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    try:
        db.delete(store)
        db.commit()
        return {"message": "Store deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting store"
        )
