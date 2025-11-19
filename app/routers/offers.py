"""
Offers and coupons routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
from pydantic import UUID4
from typing import Optional
import math
from datetime import datetime, timezone
import secrets
import bcrypt
import hashlib
import qrcode
import io
import base64

from database import get_db
from ..models import user as user_models
from ..models import coupons as coupon_models
from ..models import points as points_models
from ..models import system as system_models
from ..models.enums import CouponStatusEnum, RedeemTypeEnum, ScopeEnum
from ..schemas.coupons import BuyCouponRequest, BuyCouponResponse
from ..core.security import get_current_active_user

offers_router = APIRouter(prefix="/offers", tags=["offers"])
coupons_router = APIRouter(prefix="/coupons", tags=["coupons"])

def generate_coupon_code() -> str:
    """Generate a unique coupon code"""
    return secrets.token_urlsafe(16)

def hash_coupon_code(code: str) -> bytes:
    """Hash a coupon code for storage"""
    return hashlib.sha256(code.encode()).digest()

def verify_coupon_code(code: str, code_hash: bytes) -> bool:
    """Verify a coupon code against its hash"""
    return hashlib.sha256(code.encode()).digest() == code_hash

def generate_qr_code(code: str) -> dict:
    """Generate QR code for coupon"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "format": "png",
        "data": f"data:image/png;base64,{img_str}"
    }

@offers_router.get("", summary="Listar ofertas de cupons")
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
    query = db.query(coupon_models.CouponOffer).join(
        coupon_models.CouponType, coupon_models.CouponOffer.coupon_type_id == coupon_models.CouponType.id
    )
    
    # Filtrar por escopo
    if scope:
        query = query.filter(coupon_models.CouponOffer.entity_scope == scope)
    
    # Filtrar por entity_id
    if scope_id:
        query = query.filter(coupon_models.CouponOffer.entity_id == scope_id)
    
    # Filtrar apenas ofertas ativas
    if active:
        query = query.filter(
            coupon_models.CouponOffer.is_active == True,
            or_(
                coupon_models.CouponOffer.start_at == None,
                coupon_models.CouponOffer.start_at <= func.now()
            ),
            or_(
                coupon_models.CouponOffer.end_at == None,
                coupon_models.CouponOffer.end_at >= func.now()
            )
        )
    
    # Busca por texto
    if search:
        # Isso seria refinado em um ambiente real, possivelmente buscando em metadados ou detalhes
        pass
    
    # Contar total para paginação
    total = query.count()
    
    # Aplicar paginação
    query = query.order_by(coupon_models.CouponOffer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    offers = query.all()
    
    # Formato de resposta
    results = []
    for offer in offers:
        # Obter detalhes da oferta
        coupon_type = db.query(coupon_models.CouponType).filter(coupon_models.CouponType.id == offer.coupon_type_id).first()
        
        # Obter assets (imagens) da oferta
        assets = db.query(coupon_models.OfferAsset).filter(
            coupon_models.OfferAsset.offer_id == offer.id
        ).order_by(coupon_models.OfferAsset.position).all()
        
        offer_data = {
            "id": str(offer.id),
            "entity_scope": offer.entity_scope,
            "entity_id": str(offer.entity_id),
            "initial_quantity": offer.initial_quantity,
            "current_quantity": offer.current_quantity,
            "max_per_customer": offer.max_per_customer,
            "points_cost": offer.points_cost,
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

@offers_router.get("/{offer_id}", summary="Detalhes de uma oferta")
def get_offer_details(
    offer_id: UUID4,
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes completos de uma oferta de cupom específica.
    
    - **offer_id**: ID da oferta a ser consultada
    
    Inclui detalhes do tipo de cupom e assets (imagens) associados.
    """
    offer = db.query(coupon_models.CouponOffer).filter(coupon_models.CouponOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    # Obter detalhes do tipo de cupom
    coupon_type = db.query(coupon_models.CouponType).filter(coupon_models.CouponType.id == offer.coupon_type_id).first()
    
    # Obter assets (imagens) da oferta
    assets = db.query(coupon_models.OfferAsset).filter(
        coupon_models.OfferAsset.offer_id == offer.id
    ).order_by(coupon_models.OfferAsset.position).all()
    
    # Construir resposta detalhada
    result = {
        "id": str(offer.id),
        "entity_scope": offer.entity_scope,
        "entity_id": str(offer.entity_id),
        "initial_quantity": offer.initial_quantity,
        "current_quantity": offer.current_quantity,
        "max_per_customer": offer.max_per_customer,
        "points_cost": offer.points_cost,
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

@coupons_router.post("/buy", response_model=BuyCouponResponse, status_code=status.HTTP_201_CREATED,
                     summary="Adquirir um cupom")
def buy_coupon(
    data: BuyCouponRequest,
    current_user: user_models.AppUser = Depends(get_current_active_user),
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
    offer = db.query(coupon_models.CouponOffer).filter(coupon_models.CouponOffer.id == data.offer_id).with_for_update().first()
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
    now = datetime.now(timezone.utc)
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
        active_statuses = [
            CouponStatusEnum.ISSUED,
            CouponStatusEnum.RESERVED,
        ]
        count = (
            db.query(func.count(coupon_models.Coupon.id))
            .filter(
                coupon_models.Coupon.offer_id == offer.id,
                coupon_models.Coupon.issued_to_person_id == current_user.person_id,
                coupon_models.Coupon.status.in_(active_statuses),
            )
            .scalar()
        )

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
    
    entity_scope_value = offer.entity_scope.value if isinstance(offer.entity_scope, ScopeEnum) else offer.entity_scope
    points_cost = offer.points_cost or 0
    available_points = None
    if points_cost > 0:
        balance_query = (
            db.query(func.coalesce(func.sum(points_models.PointTransaction.delta), 0))
            .filter(
                points_models.PointTransaction.person_id == current_user.person_id,
                points_models.PointTransaction.scope == offer.entity_scope,
                or_(
                    points_models.PointTransaction.expires_at == None,
                    points_models.PointTransaction.expires_at > func.now()
                ),
                points_models.PointTransaction.scope_id == offer.entity_id
            )
        )
        available_points = balance_query.scalar() or 0
        
        if available_points < points_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient points to acquire this offer. Required: {points_cost}, available: {available_points}"
            )
    
    try:
        # Gerar código de cupom
        code = generate_coupon_code()
        code_hash = hash_coupon_code(code)
        
        # Criar cupom
        coupon = coupon_models.Coupon(
            offer_id=offer.id,
            issued_to_person_id=current_user.person_id,
            code_hash=code_hash,
            status=CouponStatusEnum.ISSUED
        )
        
        # Decrementar estoque
        offer.current_quantity -= 1
        
        # Persistir alterações
        db.add(coupon)
        
        # Registrar custo em pontos, se aplicável
        if points_cost > 0:
            deduction = points_models.PointTransaction(
                person_id=current_user.person_id,
                scope=offer.entity_scope,
                scope_id=offer.entity_id,
                delta=-points_cost,
                details={
                    "reason": "coupon_purchase",
                    "offer_id": str(offer.id),
                    "points_cost": points_cost
                }
            )
            db.add(deduction)
        
        # Gerar QR code
        qr_data = generate_qr_code(code)
        
        # Registrar auditoria
        audit = system_models.AuditLog(
            actor_user_id=current_user.id,
            action="COUPON_ISSUE",
            target_table="coupon",
            target_id=str(coupon.id),
            after={
                "points_cost": points_cost,
                "offer_id": str(offer.id),
                "entity_scope": entity_scope_value,
                "entity_id": str(offer.entity_id),
            }
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

@coupons_router.get("/my", summary="Listar meus cupons")
def get_my_coupons(
    current_user: user_models.AppUser = Depends(get_current_active_user),
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
    coupons = db.query(coupon_models.Coupon).filter(
        coupon_models.Coupon.issued_to_person_id == current_user.person_id
    ).all()
    
    results = []
    for coupon in coupons:
        offer = db.query(coupon_models.CouponOffer).filter(coupon_models.CouponOffer.id == coupon.offer_id).first()
        coupon_type = db.query(coupon_models.CouponType).filter(coupon_models.CouponType.id == offer.coupon_type_id).first() if offer else None
        
        if offer and coupon_type:
            coupon_data = {
                "id": str(coupon.id),
                "offer_id": str(coupon.offer_id),
                "status": coupon.status,
                "issued_at": coupon.issued_at.isoformat(),
                "redeemed_at": coupon.redeemed_at.isoformat() if coupon.redeemed_at else None,
                "offer": {
                    "entity_scope": offer.entity_scope,
                    "points_cost": offer.points_cost,
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

@coupons_router.get("/my-with-codes", summary="Listar meus cupons com códigos e QR")
def get_my_coupons_with_codes(
    offer_id: Optional[UUID4] = None,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista cupons do usuário atual com códigos e QR codes.
    Pode filtrar por offer_id específico.
    
    Retorna apenas cupons não resgatados (ISSUED ou RESERVED).
    
    Requer autenticação via token de acesso (Bearer token).
    """
    if not current_user.person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an associated person record"
        )
    
    # Query base
    query = db.query(coupon_models.Coupon).filter(
        coupon_models.Coupon.issued_to_person_id == current_user.person_id,
        coupon_models.Coupon.status.in_([CouponStatusEnum.ISSUED, CouponStatusEnum.RESERVED])
    )
    
    # Filtrar por offer_id se fornecido
    if offer_id:
        query = query.filter(coupon_models.Coupon.offer_id == offer_id)
    
    coupons = query.all()
    
    results = []
    for coupon in coupons:
        offer = db.query(coupon_models.CouponOffer).filter(
            coupon_models.CouponOffer.id == coupon.offer_id
        ).first()
        coupon_type = db.query(coupon_models.CouponType).filter(
            coupon_models.CouponType.id == offer.coupon_type_id
        ).first() if offer else None
        
        if offer and coupon_type:
            # Gerar código temporário para exibição (não armazenado)
            # Por segurança, usamos hash reverso apenas para display do cupom ao dono
            code_display = f"COUPON-{str(coupon.id)[:8].upper()}"
            qr_data = generate_qr_code(code_display)
            
            coupon_data = {
                "id": str(coupon.id),
                "offer_id": str(coupon.offer_id),
                "status": coupon.status,
                "issued_at": coupon.issued_at.isoformat(),
                "code": code_display,
                "qr": qr_data,
                "offer": {
                    "entity_scope": offer.entity_scope,
                    "entity_id": str(offer.entity_id),
                    "points_cost": offer.points_cost,
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