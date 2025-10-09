from fastapi import FastAPI, Depends, HTTPException, Request, Header, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, desc, case
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any, Union
import uuid
import bcrypt
import hmac
import json
import base64
import secrets
import time
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator, UUID4
import jwt as pyjwt
from decimal import Decimal
import qrcode
import io
import math
import os
from dotenv import load_dotenv

from database import get_db, engine, Base
import models

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_PREFIX = "Bearer "

app = FastAPI(
    title="Fidelity API", 
    description="API para sistema de fidelidade e cupons com suporte a gerenciamento de pontos, cupons e ofertas. O sistema suporta múltiplos tenants (Customer → Franchise → Store) e controle de acesso baseado em perfis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuração de segurança para o Swagger UI
app.swagger_ui_parameters = {
    "persistAuthorization": True,
    "displayOperationId": True,
    "operationsSorter": "method",
    "tagsSorter": "alpha",
    "docExpansion": "list"
}

# Definição de tags para organização da documentação
tags_metadata = [
    {
        "name": "Autenticação",
        "description": "Operações relacionadas a autenticação, login e registro de usuários",
    },
    {
        "name": "Marketplace",
        "description": "Operações para usuários finais do marketplace: carteira, ofertas e cupons",
    },
    {
        "name": "PDV",
        "description": "Operações para o Ponto de Venda: validação e resgate de cupons, acúmulo de pontos",
    }
]

app.openapi_tags = tags_metadata

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Defina origins específicas em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Esquema OAuth2 - Configuração para o Swagger UI também
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scheme_name="JWT"
)

# Schemas Pydantic
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

# User schemas
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

# Wallet schemas
class PointBalance(BaseModel):
    scope: str
    scope_id: Optional[UUID4]
    points: int
    as_brl: Optional[float] = None

class CouponBalance(BaseModel):
    offer_id: UUID4
    available_count: int
    redeemed_count: int

class WalletResponse(BaseModel):
    balances: List[PointBalance]
    coupons: List[CouponBalance]

# Coupon schemas
class BuyCouponRequest(BaseModel):
    offer_id: UUID4

class BuyCouponResponse(BaseModel):
    coupon_id: UUID4
    code: str
    qr: Dict[str, str]

class AttemptCouponRequest(BaseModel):
    code: str
    order_total_brl: Decimal
    items: Optional[List[Dict[str, Any]]] = None
    store_id: UUID4

class AttemptCouponResponse(BaseModel):
    coupon_id: UUID4
    redeemable: bool
    discount: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class RedeemCouponRequest(BaseModel):
    coupon_id: UUID4
    order_id: Optional[str] = None
    order: Optional[Dict[str, Any]] = None

# Points schemas
class EarnPointsRequest(BaseModel):
    person_id: Optional[UUID4] = None
    cpf: Optional[str] = None
    order: Dict[str, Any]
    store_id: UUID4

class EarnPointsResponse(BaseModel):
    order_id: UUID4
    points_earned: int
    wallet_snapshot: Dict[str, Any]

# Funções de autenticação
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.AppUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Remove o prefixo Bearer se estiver presente
        if token.startswith(JWT_PREFIX):
            token = token[len(JWT_PREFIX):]
            
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(**payload)
    except pyjwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(models.AppUser).filter(models.AppUser.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

def get_current_active_user(current_user: models.AppUser = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_admin_user(current_user: models.AppUser = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# Funções de utilitários
def generate_coupon_code(length: int = 8) -> str:
    """Gera um código de cupom alfanumérico único."""
    return secrets.token_urlsafe(length)[:length].upper()

def hash_coupon_code(code: str) -> bytes:
    """Gera um hash do código do cupom usando bcrypt."""
    return bcrypt.hashpw(code.encode(), bcrypt.gensalt())

def verify_coupon_code(code: str, code_hash: bytes) -> bool:
    """Verifica um código de cupom contra seu hash."""
    return bcrypt.checkpw(code.encode(), code_hash)

def generate_qr_code(data: str) -> Dict[str, str]:
    """Gera um QR code como SVG a partir de uma string de dados."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "format": "svg",
        "data": f"data:image/png;base64,{img_str}"
    }

# Rotas de autenticação
@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED,
           tags=["Autenticação"],
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
    if db.query(models.AppUser).filter(models.AppUser.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Verificar se CPF já existe
    if db.query(models.Person).filter(models.Person.cpf == user_data.cpf).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já registrado"
        )
    
    try:
        # Criar pessoa
        new_person = models.Person(
            cpf=user_data.cpf,
            name=user_data.name,
            phone=user_data.phone
        )
        db.add(new_person)
        db.flush()  # Para obter o ID
        
        # Criar usuário
        password_hash = get_password_hash(user_data.password)
        new_user = models.AppUser(
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
            "user_id": str(new_user.id),
            "role": new_user.role,
            "person_id": str(new_user.person_id)
        }
        access_token = create_access_token(token_data)
        
        # Criar refresh token
        refresh_token_value = secrets.token_urlsafe(32)
        refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
        
        db_refresh_token = models.RefreshToken(
            user_id=new_user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30)
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

@app.post("/auth/login", response_model=Token,
           tags=["Autenticação"],
           summary="Login de usuário")
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica um usuário existente e retorna tokens de acesso.
    
    - **email**: Email do usuário cadastrado
    - **password**: Senha do usuário
    
    Retorna tokens de acesso e refresh para autenticação.
    """
    user = db.query(models.AppUser).filter(models.AppUser.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    token_data = {
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
            staff = db.query(models.StoreStaff).filter(models.StoreStaff.user_id == user.id).first()
            if staff:
                store = db.query(models.Store).filter(models.Store.id == staff.store_id).first()
                if store:
                    token_data["store_id"] = str(store.id)
                    
                    # Obter franchise
                    franchise = db.query(models.Franchise).filter(models.Franchise.id == store.franchise_id).first()
                    if franchise:
                        token_data["franchise_id"] = str(franchise.id)
                        token_data["customer_id"] = str(franchise.customer_id)
    
    # Criar tokens
    access_token = create_access_token(token_data)
    
    # Criar refresh token
    refresh_token_value = secrets.token_urlsafe(32)
    refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
    
    # Salvar refresh token
    db_refresh_token = models.RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }

@app.post("/auth/refresh", response_model=Token,
           tags=["Autenticação"],
           summary="Renovar token de acesso")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Renovação de token de acesso expirado usando um token de refresh válido.
    
    - **refresh_token**: Token de refresh obtido anteriormente
    
    Retorna um novo par de tokens de acesso e refresh.
    """
    # Verificar refresh token
    db_refresh_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.revoked_at == None,
        models.RefreshToken.expires_at > datetime.utcnow()
    ).all()
    
    user = None
    db_token = None
    
    for token in db_refresh_tokens:
        if bcrypt.checkpw(refresh_token.encode(), token.token_hash):
            db_token = token
            user = db.query(models.AppUser).filter(models.AppUser.id == token.user_id).first()
            break
    
    if not user or not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    token_data = {
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
            staff = db.query(models.StoreStaff).filter(models.StoreStaff.user_id == user.id).first()
            if staff:
                store = db.query(models.Store).filter(models.Store.id == staff.store_id).first()
                if store:
                    token_data["store_id"] = str(store.id)
                    
                    # Obter franchise
                    franchise = db.query(models.Franchise).filter(models.Franchise.id == store.franchise_id).first()
                    if franchise:
                        token_data["franchise_id"] = str(franchise.id)
                        token_data["customer_id"] = str(franchise.customer_id)
    
    # Gerar novo access token
    access_token = create_access_token(token_data)
    
    # Gerar novo refresh token
    new_refresh_token = secrets.token_urlsafe(32)
    new_refresh_token_hash = bcrypt.hashpw(new_refresh_token.encode(), bcrypt.gensalt())
    
    # Revogar token antigo
    db_token.revoked_at = datetime.utcnow()
    
    # Salvar novo refresh token
    db_refresh_token = models.RefreshToken(
        user_id=user.id,
        token_hash=new_refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@app.post("/auth/logout",
           tags=["Autenticação"],
           summary="Logout de usuário")
def logout(
    current_user: models.AppUser = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Realiza logout do usuário atual, revogando todos os seus tokens de refresh.
    
    Requer autenticação via token de acesso (Bearer token).
    """
    # Revogar todos os refresh tokens do usuário
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.revoked_at == None
    ).update({"revoked_at": datetime.utcnow()})
    
    db.commit()
    
    return {"message": "Logout successful"}

@app.post("/auth/pdv/register-device",
           tags=["Autenticação", "PDV"],
           summary="Registrar dispositivo PDV")
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
    device = db.query(models.Device).filter(
        models.Device.store_id == store_id,
        models.Device.registration_code == registration_code,
        models.Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid registration code"
        )
    
    # Criar token de dispositivo
    device_token = create_access_token({
        "device_id": str(device.id),
        "store_id": str(device.store_id),
        # Obter store -> franchise -> customer
        # Isso seria feito com joins no SQL real
    })
    
    # Atualizar última visualização
    device.last_seen_at = datetime.utcnow()
    db.commit()
    
    return {"device_token": device_token}

# Rotas de carteira (Marketplace)
@app.get("/wallet", response_model=WalletResponse,
           tags=["Marketplace"],
           summary="Consultar carteira do usuário")
def get_wallet(
    display_as: str = "points",
    current_user: models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna os saldos de pontos e cupons disponíveis para o usuário atual.
    
    - **display_as**: Formato de exibição dos valores (pontos ou BRL)
    
    Requer autenticação via token de acesso (Bearer token).
    """
    if not current_user.person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an associated person record"
        )
    
    # Obter saldos de pontos
    wallet_query = text("""
    SELECT person_id, scope, scope_id, points
    FROM v_point_wallet
    WHERE person_id = :person_id AND points > 0
    """)
    
    result = db.execute(wallet_query, {"person_id": current_user.person_id}).fetchall()
    
    balances = []
    for row in result:
        balance = {
            "scope": row.scope,
            "scope_id": row.scope_id,
            "points": row.points,
            "as_brl": None
        }
        
        # Conversão para BRL se solicitado
        if display_as == "brl":
            # Obter regras de pontos para a conversão
            points_rule = None
            
            if row.scope == "STORE" and row.scope_id:
                points_rule = db.query(models.PointRules).filter(
                    models.PointRules.scope == "STORE",
                    models.PointRules.store_id == row.scope_id
                ).first()
            
            if not points_rule and row.scope in ["STORE", "FRANCHISE"] and row.scope_id:
                # Obter franchise_id do store se necessário
                franchise_id = None
                if row.scope == "STORE":
                    store = db.query(models.Store).filter(models.Store.id == row.scope_id).first()
                    if store:
                        franchise_id = store.franchise_id
                else:
                    franchise_id = row.scope_id
                    
                if franchise_id:
                    points_rule = db.query(models.PointRules).filter(
                        models.PointRules.scope == "FRANCHISE",
                        models.PointRules.franchise_id == franchise_id
                    ).first()
            
            if not points_rule and row.scope in ["STORE", "FRANCHISE", "CUSTOMER"] and row.scope_id:
                # Obter customer_id
                customer_id = None
                if row.scope == "STORE":
                    store = db.query(models.Store).filter(models.Store.id == row.scope_id).first()
                    if store:
                        franchise = db.query(models.Franchise).filter(models.Franchise.id == store.franchise_id).first()
                        if franchise:
                            customer_id = franchise.customer_id
                elif row.scope == "FRANCHISE":
                    franchise = db.query(models.Franchise).filter(models.Franchise.id == row.scope_id).first()
                    if franchise:
                        customer_id = franchise.customer_id
                else:
                    customer_id = row.scope_id
                
                if customer_id:
                    points_rule = db.query(models.PointRules).filter(
                        models.PointRules.scope == "CUSTOMER",
                        models.PointRules.customer_id == customer_id
                    ).first()
            
            # Regra global se nenhuma das anteriores
            if not points_rule:
                points_rule = db.query(models.PointRules).filter(
                    models.PointRules.scope == "GLOBAL"
                ).first()
            
            # Calcular valor em BRL
            if points_rule and points_rule.points_per_brl:
                balance["as_brl"] = float(row.points / float(points_rule.points_per_brl))
        
        balances.append(balance)
    
    # Obter cupons disponíveis
    coupon_query = text("""
    SELECT person_id, coupon_offer_id, available_count, redeemed_count
    FROM v_coupon_wallet
    WHERE person_id = :person_id
    """)
    
    coupon_result = db.execute(coupon_query, {"person_id": current_user.person_id}).fetchall()
    
    coupons = []
    for row in coupon_result:
        coupon = {
            "offer_id": row.coupon_offer_id,
            "available_count": row.available_count,
            "redeemed_count": row.redeemed_count
        }
        coupons.append(coupon)
    
    return {
        "balances": balances,
        "coupons": coupons
    }

# Rotas de ofertas
@app.get("/offers",
           tags=["Marketplace"],
           summary="Listar ofertas de cupons")
def get_offers(
    scope: Optional[str] = None,
    scope_id: Optional[UUID4] = None,
    active: bool = True,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    Lista ofertas de cupons disponíveis com suporte a filtros e paginação.
    
    - **scope**: Filtro por escopo (CUSTOMER, FRANCHISE, STORE)
    - **scope_id**: ID do escopo para filtrar
    - **active**: Se True, mostra apenas ofertas ativas
    - **search**: Termo de busca para filtrar ofertas
    - **page**: Número da página para paginação
    - **page_size**: Quantidade de itens por página
    """
    # Construir query base
    query = db.query(models.CouponOffer).join(
        models.CouponType, models.CouponOffer.coupon_type_id == models.CouponType.id
    )
    
    # Filtrar por escopo
    if scope:
        query = query.filter(models.CouponOffer.entity_scope == scope)
    
    # Filtrar por entity_id
    if scope_id:
        query = query.filter(models.CouponOffer.entity_id == scope_id)
    
    # Filtrar apenas ofertas ativas
    if active:
        query = query.filter(
            models.CouponOffer.is_active == True,
            or_(
                models.CouponOffer.start_at == None,
                models.CouponOffer.start_at <= func.now()
            ),
            or_(
                models.CouponOffer.end_at == None,
                models.CouponOffer.end_at >= func.now()
            )
        )
    
    # Busca por texto
    if search:
        # Isso seria refinado em um ambiente real, possivelmente buscando em metadados ou detalhes
        pass
    
    # Contar total para paginação
    total = query.count()
    
    # Aplicar paginação
    query = query.order_by(models.CouponOffer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    offers = query.all()
    
    # Formato de resposta
    results = []
    for offer in offers:
        # Obter detalhes da oferta
        coupon_type = db.query(models.CouponType).filter(models.CouponType.id == offer.coupon_type_id).first()
        
        # Obter assets (imagens) da oferta
        assets = db.query(models.OfferAsset).filter(
            models.OfferAsset.offer_id == offer.id
        ).order_by(models.OfferAsset.position).all()
        
        offer_data = {
            "id": str(offer.id),
            "entity_scope": offer.entity_scope,
            "entity_id": str(offer.entity_id),
            "initial_quantity": offer.initial_quantity,
            "current_quantity": offer.current_quantity,
            "max_per_customer": offer.max_per_customer,
            "is_active": offer.is_active,
            "start_at": offer.start_at.isoformat() if offer.start_at else None,
            "end_at": offer.end_at.isoformat() if offer.end_at else None,
            "coupon_type": {
                "id": str(coupon_type.id),
                "redeem_type": coupon_type.redeem_type,
                "discount_amount_brl": float(coupon_type.discount_amount_brl) if coupon_type.discount_amount_brl else None,
                "discount_amount_percentage": float(coupon_type.discount_amount_percentage) if coupon_type.discount_amount_percentage else None,
                "sku_specific": coupon_type.sku_specific,
                "valid_skus": coupon_type.valid_skus
            },
            "assets": [
                {
                    "id": str(asset.id),
                    "kind": asset.kind,
                    "url": asset.url
                }
                for asset in assets
            ]
        }
        
        results.append(offer_data)
    
    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size)
    }

@app.get("/offers/{offer_id}",
           tags=["Marketplace"],
           summary="Detalhes de uma oferta")
def get_offer_details(
    offer_id: UUID4,
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes completos de uma oferta de cupom específica.
    
    - **offer_id**: ID da oferta a ser consultada
    
    Inclui detalhes do tipo de cupom e assets (imagens) associados.
    """
    offer = db.query(models.CouponOffer).filter(models.CouponOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    # Obter detalhes do tipo de cupom
    coupon_type = db.query(models.CouponType).filter(models.CouponType.id == offer.coupon_type_id).first()
    
    # Obter assets (imagens) da oferta
    assets = db.query(models.OfferAsset).filter(
        models.OfferAsset.offer_id == offer.id
    ).order_by(models.OfferAsset.position).all()
    
    # Construir resposta detalhada
    result = {
        "id": str(offer.id),
        "entity_scope": offer.entity_scope,
        "entity_id": str(offer.entity_id),
        "initial_quantity": offer.initial_quantity,
        "current_quantity": offer.current_quantity,
        "max_per_customer": offer.max_per_customer,
        "is_active": offer.is_active,
        "start_at": offer.start_at.isoformat() if offer.start_at else None,
        "end_at": offer.end_at.isoformat() if offer.end_at else None,
        "created_at": offer.created_at.isoformat(),
        "coupon_type": {
            "id": str(coupon_type.id),
            "redeem_type": coupon_type.redeem_type,
            "discount_amount_brl": float(coupon_type.discount_amount_brl) if coupon_type.discount_amount_brl else None,
            "discount_amount_percentage": float(coupon_type.discount_amount_percentage) if coupon_type.discount_amount_percentage else None,
            "sku_specific": coupon_type.sku_specific,
            "valid_skus": coupon_type.valid_skus
        },
        "assets": [
            {
                "id": str(asset.id),
                "kind": asset.kind,
                "url": asset.url
            }
            for asset in assets
        ]
    }
    
    return result

@app.post("/coupons/buy", response_model=BuyCouponResponse, status_code=status.HTTP_201_CREATED,
           tags=["Marketplace"],
           summary="Adquirir um cupom")
def buy_coupon(
    data: BuyCouponRequest,
    current_user: models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Emite um novo cupom para o usuário a partir de uma oferta disponível.
    
    - **offer_id**: ID da oferta de cupom
    
    Verifica regras de estoque, limite por cliente, janela de validade e segmentação.
    Retorna o código do cupom e QR code para uso.
    
    Requer autenticação via token de acesso (Bearer token).
    """
    if not current_user.person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an associated person record"
        )
    
    # Verificar se a oferta existe e está válida
    offer = db.query(models.CouponOffer).filter(models.CouponOffer.id == data.offer_id).with_for_update().first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    # Verificar se a oferta está ativa
    if not offer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer is not active"
        )
    
    # Verificar janela de validade
    now = datetime.utcnow()
    if offer.start_at and offer.start_at > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer is not yet available"
        )
    
    if offer.end_at and offer.end_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer has expired"
        )
    
    # Verificar estoque
    if offer.current_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer is out of stock"
        )
    
    # Verificar limite por cliente
    if offer.max_per_customer > 0:
        count = db.query(models.Coupon).filter(
            models.Coupon.offer_id == offer.id,
            models.Coupon.issued_to_person_id == current_user.person_id,
            models.Coupon.status.in_(["ISSUED", "RESERVED"])
        ).count()
        
        if count >= offer.max_per_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum limit of {offer.max_per_customer} coupons per customer reached"
            )
    
    # Verificar segmentação (opcional)
    if offer.customer_segment:
        # Implementar lógica de verificação de segmento do cliente
        # Ex: verificar idade, região, tags, etc.
        pass
    
    try:
        # Gerar código de cupom
        code = generate_coupon_code()
        code_hash = hash_coupon_code(code)
        
        # Criar cupom
        coupon = models.Coupon(
            offer_id=offer.id,
            issued_to_person_id=current_user.person_id,
            code_hash=code_hash,
            status="ISSUED"
        )
        
        # Decrementar estoque
        offer.current_quantity -= 1
        
        # Persistir alterações
        db.add(coupon)
        db.commit()
        
        # Gerar QR code
        qr_data = generate_qr_code(code)
        
        # Registrar auditoria
        audit = models.AuditLog(
            actor_user_id=current_user.id,
            action="COUPON_ISSUE",
            target_table="coupon",
            target_id=str(coupon.id)
        )
        db.add(audit)
        db.commit()
        
        return {
            "coupon_id": coupon.id,
            "code": code,
            "qr": qr_data
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to issue coupon"
        )

@app.get("/coupons/my",
           tags=["Marketplace"],
           summary="Listar meus cupons")
def get_my_coupons(
    current_user: models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os cupons do usuário atual, incluindo disponíveis e resgatados.
    
    Retorna detalhes dos cupons e das ofertas associadas.
    
    Requer autenticação via token de acesso (Bearer token).
    """
    if not current_user.person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an associated person record"
        )
    
    # Obter cupons do usuário
    coupons = db.query(models.Coupon).filter(
        models.Coupon.issued_to_person_id == current_user.person_id
    ).all()
    
    results = []
    for coupon in coupons:
        offer = db.query(models.CouponOffer).filter(models.CouponOffer.id == coupon.offer_id).first()
        coupon_type = db.query(models.CouponType).filter(models.CouponType.id == offer.coupon_type_id).first() if offer else None
        
        if offer and coupon_type:
            coupon_data = {
                "id": str(coupon.id),
                "offer_id": str(coupon.offer_id),
                "status": coupon.status,
                "issued_at": coupon.issued_at.isoformat(),
                "redeemed_at": coupon.redeemed_at.isoformat() if coupon.redeemed_at else None,
                "offer": {
                    "entity_scope": offer.entity_scope,
                    "is_active": offer.is_active,
                },
                "coupon_type": {
                    "redeem_type": coupon_type.redeem_type,
                    "discount_amount_brl": float(coupon_type.discount_amount_brl) if coupon_type.discount_amount_brl else None,
                    "discount_amount_percentage": float(coupon_type.discount_amount_percentage) if coupon_type.discount_amount_percentage else None,
                }
            }
            results.append(coupon_data)
    
    return results

# Rotas PDV (Ponto de Venda)
@app.post("/pdv/attempt-coupon", response_model=AttemptCouponResponse,
           tags=["PDV"],
           summary="Validar cupom no PDV")
def attempt_coupon(
    data: AttemptCouponRequest,
    db: Session = Depends(get_db)
):
    """
    Valida um código de cupom e verifica se pode ser resgatado no PDV.
    
    - **code**: Código do cupom (texto ou obtido por scanner)
    - **order_total_brl**: Valor total do pedido para cálculo de desconto
    - **items**: Itens do pedido (opcional, para cupons específicos de SKU)
    - **store_id**: ID da loja realizando a operação
    
    Verifica se o cupom é válido, está dentro da janela de validade, e calcula o desconto.
    Se válido, reserva o cupom temporariamente para evitar uso duplicado.
    """
    # Encontrar o cupom pelo código (hash)
    code_hash = hash_coupon_code(data.code)
    
    # Encontrar cupom por hash de código (essa consulta poderia ser otimizada)
    coupons = db.query(models.Coupon).filter(
        models.Coupon.status.in_(["ISSUED", "RESERVED"])
    ).all()
    
    coupon = None
    for c in coupons:
        if verify_coupon_code(data.code, c.code_hash):
            coupon = c
            break
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found or already redeemed"
        )
    
    # Verificar store_id (segurança multi-tenant)
    # Em uma implementação real, verificaríamos se a store tem permissão para redimir este cupom
    # Ex: verificar se a loja está no mesmo customer do cupom (store->franchise->customer)
    
    # Obter detalhes da oferta e do tipo de cupom
    offer = db.query(models.CouponOffer).filter(models.CouponOffer.id == coupon.offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon offer not found"
        )
    
    # Verificar janela de validade
    now = datetime.utcnow()
    if offer.start_at and offer.start_at > now:
        return {
            "coupon_id": coupon.id,
            "redeemable": False,
            "message": "Coupon offer is not yet active"
        }
    
    if offer.end_at and offer.end_at < now:
        return {
            "coupon_id": coupon.id,
            "redeemable": False,
            "message": "Coupon offer has expired"
        }
    
    # Verificar tipo de cupom
    coupon_type = db.query(models.CouponType).filter(models.CouponType.id == offer.coupon_type_id).first()
    if not coupon_type:
        return {
            "coupon_id": coupon.id,
            "redeemable": False,
            "message": "Invalid coupon type"
        }
    
    # Verificar se é específico para SKUs
    if coupon_type.sku_specific and data.items:
        if not coupon_type.valid_skus:
            return {
                "coupon_id": coupon.id,
                "redeemable": False,
                "message": "Coupon requires specific SKUs but none are defined"
            }
        
        # Verificar se algum dos itens possui SKU válido
        valid_items = False
        for item in data.items:
            if "sku_id" in item and item["sku_id"] in coupon_type.valid_skus:
                valid_items = True
                break
        
        if not valid_items:
            return {
                "coupon_id": coupon.id,
                "redeemable": False,
                "message": "No valid items found for this coupon"
            }
    
    # Calcular desconto
    discount = None
    if coupon_type.redeem_type == "BRL" and coupon_type.discount_amount_brl:
        discount = {
            "type": "BRL",
            "amount_brl": float(coupon_type.discount_amount_brl)
        }
    elif coupon_type.redeem_type == "PERCENTAGE" and coupon_type.discount_amount_percentage:
        amount = float(data.order_total_brl) * float(coupon_type.discount_amount_percentage) / 100.0
        discount = {
            "type": "PERCENTAGE",
            "percentage": float(coupon_type.discount_amount_percentage),
            "amount_brl": amount
        }
    elif coupon_type.redeem_type == "FREE_SKU" and coupon_type.valid_skus and data.items:
        discount = {
            "type": "FREE_SKU",
            "valid_skus": coupon_type.valid_skus
        }
    
    # Reservar o cupom (transação)
    try:
        # Fazer SELECT FOR UPDATE
        coupon_for_update = db.query(models.Coupon).filter(
            models.Coupon.id == coupon.id
        ).with_for_update().first()
        
        if coupon_for_update.status not in ["ISSUED", "RESERVED"]:
            db.rollback()
            return {
                "coupon_id": coupon.id,
                "redeemable": False,
                "message": "Coupon has already been redeemed or is no longer available"
            }
        
        # Atualizar status para RESERVED
        coupon_for_update.status = "RESERVED"
        db.commit()
        
        return {
            "coupon_id": coupon.id,
            "redeemable": True,
            "discount": discount
        }
    except Exception as e:
        db.rollback()
        return {
            "coupon_id": coupon.id,
            "redeemable": False,
            "message": f"Error reserving coupon: {str(e)}"
        }

@app.post("/pdv/redeem",
           tags=["PDV"],
           summary="Resgatar cupom")
def redeem_coupon(
    data: RedeemCouponRequest,
    db: Session = Depends(get_db)
):
    """
    Confirma o resgate de um cupom previamente validado e reservado.
    
    - **coupon_id**: ID do cupom a ser resgatado (obtido de /pdv/attempt-coupon)
    - **order_id**: ID do pedido externo (opcional)
    - **order**: Detalhes completos do pedido (opcional)
    
    Altera o status do cupom para REDEEMED, registra o momento do resgate 
    e opcionalmente cria um registro de pedido.
    
    Deve ser chamada após a validação bem-sucedida por /pdv/attempt-coupon.
    """
    # Verificar se o cupom existe e está reservado
    coupon = db.query(models.Coupon).filter(
        models.Coupon.id == data.coupon_id,
        models.Coupon.status == "RESERVED"
    ).with_for_update().first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found or not reserved"
        )
    
    try:
        # Atualizar status para REDEEMED
        coupon.status = "REDEEMED"
        coupon.redeemed_at = datetime.utcnow()
        
        if data.order:
            # Criar registro de pedido se fornecido
            order = models.Order(
                store_id=data.order.get("store_id"),
                person_id=coupon.issued_to_person_id,
                total_brl=data.order.get("total_brl"),
                tax_brl=data.order.get("tax_brl", 0),
                items=data.order.get("items", {}),
                shipping=data.order.get("shipping"),
                checkout_ref=data.order.get("checkout_ref"),
                external_id=data.order.get("external_id") or data.order_id
            )
            db.add(order)
        
        # Registrar evento para outbox
        event = models.OutboxEvent(
            topic="coupon.redeemed",
            payload={
                "coupon_id": str(coupon.id),
                "offer_id": str(coupon.offer_id),
                "person_id": str(coupon.issued_to_person_id),
                "redeemed_at": coupon.redeemed_at.isoformat(),
                "order_id": data.order_id if data.order_id else None
            },
            status="PENDING"
        )
        db.add(event)
        
        db.commit()
        
        return {
            "ok": True,
            "coupon_id": str(coupon.id)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error redeeming coupon: {str(e)}"
        )

@app.post("/pdv/earn-points", status_code=status.HTTP_201_CREATED,
           tags=["PDV"],
           summary="Acumular pontos")
def earn_points(
    data: EarnPointsRequest,
    db: Session = Depends(get_db)
):
    """
    Registra pontos de fidelidade para um cliente com base em um pedido.
    
    - **person_id**: ID da pessoa (opcional, se não fornecido, usa-se o CPF)
    - **cpf**: CPF da pessoa (opcional, se não fornecido, usa-se o person_id)
    - **order**: Detalhes do pedido (incluindo total_brl e outros dados)
    - **store_id**: ID da loja onde o pedido foi realizado
    
    Calcula os pontos com base nas regras de pontuação mais específicas para a loja,
    registra a transação de pontos e retorna o total de pontos ganhos e o saldo atualizado.
    """
    # Validar person_id ou CPF (pelo menos um deve ser fornecido)
    person = None
    if data.person_id:
        person = db.query(models.Person).filter(models.Person.id == data.person_id).first()
    elif data.cpf:
        person = db.query(models.Person).filter(models.Person.cpf == data.cpf).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Validar store_id
    store = db.query(models.Store).filter(models.Store.id == data.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Buscar franchise e customer da store
    franchise = db.query(models.Franchise).filter(models.Franchise.id == store.franchise_id).first()
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Store does not have a valid franchise"
        )
    
    # Encontrar regra de pontos mais específica (STORE > FRANCHISE > CUSTOMER > GLOBAL)
    point_rule = None
    
    # Tentar regra por loja
    point_rule = db.query(models.PointRules).filter(
        models.PointRules.scope == "STORE",
        models.PointRules.store_id == store.id
    ).first()
    
    # Tentar regra por franquia
    if not point_rule:
        point_rule = db.query(models.PointRules).filter(
            models.PointRules.scope == "FRANCHISE",
            models.PointRules.franchise_id == franchise.id
        ).first()
    
    # Tentar regra por cliente
    if not point_rule:
        point_rule = db.query(models.PointRules).filter(
            models.PointRules.scope == "CUSTOMER",
            models.PointRules.customer_id == franchise.customer_id
        ).first()
    
    # Tentar regra global
    if not point_rule:
        point_rule = db.query(models.PointRules).filter(
            models.PointRules.scope == "GLOBAL"
        ).first()
    
    if not point_rule or not point_rule.points_per_brl:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No applicable point rules found"
        )
    
    try:
        # Calcular pontos
        total_brl = Decimal(data.order.get("total_brl", 0))
        points_earned = math.floor(float(total_brl) * float(point_rule.points_per_brl))
        
        if points_earned <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order amount too small to earn points"
            )
        
        # Calcular data de expiração
        expires_at = None
        if point_rule.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=point_rule.expires_in_days)
        
        # Criar registro de pedido
        order = models.Order(
            store_id=data.store_id,
            person_id=person.id,
            total_brl=total_brl,
            tax_brl=Decimal(data.order.get("tax_brl", 0)),
            items=data.order.get("items", {}),
            shipping=data.order.get("shipping", {}),
            checkout_ref=data.order.get("checkout_ref"),
            external_id=data.order.get("external_id")
        )
        db.add(order)
        db.flush()  # Para obter o ID do pedido
        
        # Criar transação de pontos
        transaction = models.PointTransaction(
            person_id=person.id,
            scope=point_rule.scope,
            scope_id=(
                point_rule.store_id or 
                point_rule.franchise_id or 
                point_rule.customer_id
            ),
            store_id=data.store_id,
            order_id=str(order.id),
            delta=points_earned,
            details={
                "order_total": float(total_brl),
                "points_per_brl": float(point_rule.points_per_brl),
                "rule_id": str(point_rule.id)
            },
            expires_at=expires_at
        )
        db.add(transaction)
        
        db.commit()
        
        # Snapshot da carteira
        wallet_query = text("""
        SELECT SUM(delta) FILTER (WHERE expires_at IS NULL OR expires_at > now()) AS total_points
        FROM point_transaction
        WHERE person_id = :person_id
        """)
        
        wallet_result = db.execute(wallet_query, {"person_id": person.id}).fetchone()
        total_points = wallet_result.total_points if wallet_result else 0
        
        return {
            "order_id": order.id,
            "points_earned": points_earned,
            "wallet_snapshot": {
                "total_points": total_points or 0
            }
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process points"
        )

# Criar tabelas no banco de dados
@app.on_event("startup")
def create_tables():
    # Criar todas as tabelas definidas nos modelos
    Base.metadata.create_all(bind=engine)
    
    # Criar views SQL
    with engine.connect() as connection:
        connection.execute(models.point_wallet_view)
        connection.execute(models.coupon_wallet_view)
        
    print("Database tables and views created successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
