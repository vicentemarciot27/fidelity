"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from pydantic import UUID4
import bcrypt
import secrets

from database import get_db
from ..models import user as user_models
from ..models import business as business_models
from ..schemas.auth import Token, UserLogin, UserCreate
from ..core.security import create_access_token, get_password_hash, verify_password, get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED,
             summary="Registrar novo usuário")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário no sistema e cria um perfil de pessoa associado.
    
    - **email**: Email do usuário (deve ser único)
    - **password**: Senha do usuário (será criptografada)
    - **name**: Nome completo da pessoa
    - **cpf**: CPF da pessoa (deve ser único)
    - **phone**: Número de telefone (opcional)
    - **role**: Perfil do usuário (padrão: USER)
    
    Retorna tokens de acesso e refresh para autenticação imediata.
    """
    # Verificar se email já existe
    if db.query(user_models.AppUser).filter(user_models.AppUser.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Verificar se CPF já existe
    if db.query(user_models.Person).filter(user_models.Person.cpf == user_data.cpf).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já registrado"
        )
    
    try:
        # Criar pessoa
        new_person = user_models.Person(
            cpf=user_data.cpf,
            name=user_data.name,
            phone=user_data.phone
        )
        db.add(new_person)
        db.flush()  # Para obter o ID
        
        # Criar usuário
        password_hash = get_password_hash(user_data.password)
        new_user = user_models.AppUser(
            person_id=new_person.id,
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        
        # Criar token de acesso
        token_data = {
            "sub": str(new_user.id),
            "user_id": str(new_user.id),
            "role": new_user.role,
            "person_id": str(new_user.person_id)
        }
        access_token = create_access_token(token_data)
        
        # Criar refresh token
        refresh_token_value = secrets.token_urlsafe(32)
        refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
        
        db_refresh_token = user_models.RefreshToken(
            user_id=new_user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(db_refresh_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer"
        }
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar usuário"
        )

@router.post("/login", response_model=Token,
             summary="Login de usuário")
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica um usuário existente e retorna tokens de acesso.
    
    - **email**: Email do usuário cadastrado
    - **password**: Senha do usuário
    
    Retorna tokens de acesso e refresh para autenticação.
    """
    user = db.query(user_models.AppUser).filter(user_models.AppUser.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    token_data = {
        "sub": str(user.id),
        "user_id": str(user.id),
        "role": user.role,
        "person_id": str(user.person_id) if user.person_id else None,
    }
    
    # Adicionar customer_id para roles específicas
    if user.role in ["CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
        # Obter customer_id, franchise_id, store_id conforme a role
        if user.role == "CUSTOMER_ADMIN":
            # Lógica para obter customer_id para admin de cliente
            pass
        elif user.role in ["FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
            # Obter store_staff e relacionados
            staff = db.query(user_models.StoreStaff).filter(user_models.StoreStaff.user_id == user.id).first()
            if staff:
                store = db.query(business_models.Store).filter(business_models.Store.id == staff.store_id).first()
                if store:
                    token_data["store_id"] = str(store.id)
                    
                    # Obter franchise
                    franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == store.franchise_id).first()
                    if franchise:
                        token_data["franchise_id"] = str(franchise.id)
                        token_data["customer_id"] = str(franchise.customer_id)
    
    # Criar tokens
    access_token = create_access_token(token_data)
    
    # Criar refresh token
    refresh_token_value = secrets.token_urlsafe(32)
    refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
    
    # Salvar refresh token
    db_refresh_token = user_models.RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }

@router.post("/token", response_model=Token,
             summary="Login OAuth2 (para Swagger UI)",
             description="Endpoint compatível com OAuth2PasswordRequestForm para uso no Swagger UI",
             include_in_schema=True)
def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint de login compatível com OAuth2PasswordRequestForm.
    Este endpoint é usado pelo Swagger UI para autenticação.
    
    - **username**: Email do usuário (campo username é usado como email)
    - **password**: Senha do usuário
    
    Retorna apenas o access_token para compatibilidade com OAuth2.
    """
    # Usar o username como email
    user = db.query(user_models.AppUser).filter(user_models.AppUser.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso (simplificado para OAuth2)
    token_data = {
        "sub": str(user.id),
        "user_id": str(user.id),
        "role": user.role,
        "person_id": str(user.person_id) if user.person_id else None,
    }
    
    # Adicionar customer_id para roles específicas
    if user.role in ["CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
        if user.role in ["FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
            staff = db.query(user_models.StoreStaff).filter(user_models.StoreStaff.user_id == user.id).first()
            if staff:
                store = db.query(business_models.Store).filter(business_models.Store.id == staff.store_id).first()
                if store:
                    token_data["store_id"] = str(store.id)
                    franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == store.franchise_id).first()
                    if franchise:
                        token_data["franchise_id"] = str(franchise.id)
                        token_data["customer_id"] = str(franchise.customer_id)
    
    access_token = create_access_token(token_data)
    
    # Criar refresh token simples para OAuth2
    refresh_token_value = secrets.token_urlsafe(32)
    refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
    
    db_refresh_token = user_models.RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token,
             summary="Renovar token de acesso")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Renovação de token de acesso expirado usando um token de refresh válido.
    
    - **refresh_token**: Token de refresh obtido anteriormente
    
    Retorna um novo par de tokens de acesso e refresh.
    """
    # Verificar refresh token
    db_refresh_tokens = db.query(user_models.RefreshToken).filter(
        user_models.RefreshToken.revoked_at == None,
        user_models.RefreshToken.expires_at > datetime.now(timezone.utc)
    ).all()
    
    user = None
    db_token = None
    
    for token in db_refresh_tokens:
        if bcrypt.checkpw(refresh_token.encode(), token.token_hash):
            db_token = token
            user = db.query(user_models.AppUser).filter(user_models.AppUser.id == token.user_id).first()
            break
    
    if not user or not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    token_data = {
        "sub": str(user.id),
        "user_id": str(user.id),
        "role": user.role,
        "person_id": str(user.person_id) if user.person_id else None,
    }
    
    # Adicionar customer_id para roles específicas (similar à rota de login)
    if user.role in ["CUSTOMER_ADMIN", "FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
        # Obter customer_id, franchise_id, store_id conforme a role
        if user.role == "CUSTOMER_ADMIN":
            # Lógica para obter customer_id para admin de cliente
            pass
        elif user.role in ["FRANCHISE_MANAGER", "STORE_MANAGER", "CASHIER"]:
            # Obter store_staff e relacionados
            staff = db.query(user_models.StoreStaff).filter(user_models.StoreStaff.user_id == user.id).first()
            if staff:
                store = db.query(business_models.Store).filter(business_models.Store.id == staff.store_id).first()
                if store:
                    token_data["store_id"] = str(store.id)
                    
                    # Obter franchise
                    franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == store.franchise_id).first()
                    if franchise:
                        token_data["franchise_id"] = str(franchise.id)
                        token_data["customer_id"] = str(franchise.customer_id)
    
    # Gerar novo access token
    access_token = create_access_token(token_data)
    
    # Gerar novo refresh token
    new_refresh_token = secrets.token_urlsafe(32)
    new_refresh_token_hash = bcrypt.hashpw(new_refresh_token.encode(), bcrypt.gensalt())
    
    # Revogar token antigo
    db_token.revoked_at = datetime.now(timezone.utc)
    
    # Salvar novo refresh token
    db_refresh_token = user_models.RefreshToken(
        user_id=user.id,
        token_hash=new_refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", summary="Logout de usuário")
def logout(
    current_user: user_models.AppUser = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Realiza logout do usuário atual, revogando todos os seus tokens de refresh.
    
    Requer autenticação via token de acesso (Bearer token).
    """
    # Revogar todos os refresh tokens do usuário
    db.query(user_models.RefreshToken).filter(
        user_models.RefreshToken.user_id == current_user.id,
        user_models.RefreshToken.revoked_at == None
    ).update({"revoked_at": datetime.now(timezone.utc)})
    
    db.commit()
    
    return {"message": "Logout successful"}

@router.post("/pdv/register-device", summary="Registrar dispositivo PDV")
def register_device(
    store_id: UUID4,
    registration_code: str,
    db: Session = Depends(get_db)
):
    """
    Registra um dispositivo PDV usando um código de registro pré-gerado.
    
    - **store_id**: ID da loja onde o dispositivo será registrado
    - **registration_code**: Código de registro gerado no Admin
    
    Retorna um token de dispositivo para uso nas operações de PDV.
    """
    # Verificar se o registration code é válido e não utilizado
    device = db.query(business_models.Device).filter(
        business_models.Device.store_id == store_id,
        business_models.Device.registration_code == registration_code,
        business_models.Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid registration code or store"
        )
    
    # Marcar device como utilizado/registrado
    device.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "message": "Device registered successfully",
        "device_id": device.id,
        "store_id": device.store_id
    }
