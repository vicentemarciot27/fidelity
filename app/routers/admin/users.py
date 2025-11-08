"""
User and staff management routes for Admin API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import UUID4
from typing import Optional
import math

from database import get_db
from ...models import user as user_models
from ...models import business as business_models
from ...schemas.admin import users as user_schemas
from ...core.security import get_current_active_user, get_password_hash

router = APIRouter(prefix="/admin", tags=["admin-users"])


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


# ========= User endpoints =========
@router.post("/users", response_model=user_schemas.UserResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar usuário")
def create_user(
    data: user_schemas.UserCreateAdmin,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo usuário com pessoa associada.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se email já existe
    if db.query(user_models.AppUser).filter(
        user_models.AppUser.email == data.email
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verificar se CPF já existe
    if db.query(user_models.Person).filter(
        user_models.Person.cpf == data.cpf
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF already registered"
        )
    
    try:
        # Criar pessoa
        person = user_models.Person(
            cpf=data.cpf,
            name=data.name,
            phone=data.phone
        )
        db.add(person)
        db.flush()
        
        # Criar usuário
        password_hash = get_password_hash(data.password)
        user = user_models.AppUser(
            person_id=person.id,
            email=data.email,
            password_hash=password_hash,
            role=data.role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Preparar resposta com dados da pessoa
        return {
            "id": user.id,
            "person_id": user.person_id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "person": {
                "id": person.id,
                "cpf": person.cpf,
                "name": person.name,
                "phone": person.phone
            }
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user"
        )


@router.get("/users", summary="Listar usuários")
def list_users(
    role: Optional[str] = Query(None, description="Filtrar por role"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista usuários com paginação.
    Pode filtrar por role e status ativo.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(user_models.AppUser)
    
    if role:
        query = query.filter(user_models.AppUser.role == role)
    
    if is_active is not None:
        query = query.filter(user_models.AppUser.is_active == is_active)
    
    query = query.order_by(user_models.AppUser.created_at.desc())
    
    result = paginate_query(query, page, page_size)
    
    # Enriquecer com dados da pessoa
    users_with_person = []
    for user in result["items"]:
        person = db.query(user_models.Person).filter(
            user_models.Person.id == user.person_id
        ).first()
        users_with_person.append({
            "id": user.id,
            "person_id": user.person_id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "person": {
                "id": person.id,
                "cpf": person.cpf,
                "name": person.name,
                "phone": person.phone
            } if person else None
        })
    
    result["items"] = users_with_person
    return result


@router.get("/users/{user_id}", response_model=user_schemas.UserResponse,
            summary="Obter detalhes do usuário")
def get_user(
    user_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um usuário específico.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    user = db.query(user_models.AppUser).filter(
        user_models.AppUser.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    person = db.query(user_models.Person).filter(
        user_models.Person.id == user.person_id
    ).first()
    
    return {
        "id": user.id,
        "person_id": user.person_id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "person": {
            "id": person.id,
            "cpf": person.cpf,
            "name": person.name,
            "phone": person.phone
        } if person else None
    }


@router.patch("/users/{user_id}", response_model=user_schemas.UserResponse,
              summary="Atualizar usuário")
def update_user(
    user_id: UUID4,
    data: user_schemas.UserUpdateAdmin,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um usuário (incluindo role e status).
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    user = db.query(user_models.AppUser).filter(
        user_models.AppUser.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        
        # Atualizar dados da pessoa se fornecidos
        if "name" in update_data or "phone" in update_data:
            person = db.query(user_models.Person).filter(
                user_models.Person.id == user.person_id
            ).first()
            if person:
                if "name" in update_data:
                    person.name = update_data.pop("name")
                if "phone" in update_data:
                    person.phone = update_data.pop("phone")
        
        # Atualizar dados do usuário
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        person = db.query(user_models.Person).filter(
            user_models.Person.id == user.person_id
        ).first()
        
        return {
            "id": user.id,
            "person_id": user.person_id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "person": {
                "id": person.id,
                "cpf": person.cpf,
                "name": person.name,
                "phone": person.phone
            } if person else None
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating user"
        )


@router.delete("/users/{user_id}", summary="Desativar usuário")
def deactivate_user(
    user_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Desativa um usuário (soft delete via is_active=False).
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    user = db.query(user_models.AppUser).filter(
        user_models.AppUser.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        user.is_active = False
        db.commit()
        return {"message": "User deactivated successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deactivating user"
        )


# ========= Store Staff endpoints =========
@router.post("/store-staff", response_model=user_schemas.StoreStaffResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Atribuir staff a loja")
def create_store_staff(
    data: user_schemas.StoreStaffCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atribui um usuário como staff de uma loja.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se usuário existe
    user = db.query(user_models.AppUser).filter(
        user_models.AppUser.id == data.user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verificar se loja existe
    store = db.query(business_models.Store).filter(
        business_models.Store.id == data.store_id
    ).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Verificar se já existe atribuição
    existing = db.query(user_models.StoreStaff).filter(
        user_models.StoreStaff.user_id == data.user_id,
        user_models.StoreStaff.store_id == data.store_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already staff at this store"
        )
    
    try:
        staff = user_models.StoreStaff(**data.model_dump())
        db.add(staff)
        db.commit()
        db.refresh(staff)
        return staff
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating store staff assignment"
        )


@router.get("/store-staff", summary="Listar atribuições de staff")
def list_store_staff(
    store_id: Optional[UUID4] = Query(None, description="Filtrar por loja"),
    user_id: Optional[UUID4] = Query(None, description="Filtrar por usuário"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista atribuições de staff com paginação.
    Pode filtrar por store_id ou user_id.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(user_models.StoreStaff)
    
    if store_id:
        query = query.filter(user_models.StoreStaff.store_id == store_id)
    
    if user_id:
        query = query.filter(user_models.StoreStaff.user_id == user_id)
    
    return paginate_query(query, page, page_size)


@router.delete("/store-staff/{staff_id}", summary="Remover staff da loja")
def delete_store_staff(
    staff_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove atribuição de staff de uma loja.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    staff = db.query(user_models.StoreStaff).filter(
        user_models.StoreStaff.id == staff_id
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store staff assignment not found"
        )
    
    try:
        db.delete(staff)
        db.commit()
        return {"message": "Store staff assignment removed successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error removing store staff assignment"
        )
