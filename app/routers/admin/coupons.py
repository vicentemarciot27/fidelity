"""
Coupon and offer management routes for Admin API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text
from pydantic import UUID4
from typing import Optional
from datetime import datetime
import math
import uuid
import secrets

from database import get_db
from ...models import coupons as coupon_models
from ...models import user as user_models
from ...models import business as business_models
from ...models import system as system_models
from ...schemas.admin import coupons as coupon_schemas
from ...core.security import get_current_active_user
from ..offers import hash_coupon_code

router = APIRouter(prefix="/admin", tags=["admin-coupons"])


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


# ========= Coupon Type endpoints =========
@router.post("/coupon-types", response_model=coupon_schemas.CouponTypeResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar tipo de cupom")
def create_coupon_type(
    data: coupon_schemas.CouponTypeCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo tipo de cupom com configurações de desconto.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Validar dados de acordo com redeem_type
    if data.redeem_type == "BRL" and not data.discount_amount_brl:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_amount_brl required for BRL redeem type"
        )
    elif data.redeem_type == "PERCENTAGE" and not data.discount_amount_percentage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_amount_percentage required for PERCENTAGE redeem type"
        )
    elif data.redeem_type == "FREE_SKU" and not data.valid_skus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_skus required for FREE_SKU redeem type"
        )
    
    try:
        coupon_type = coupon_models.CouponType(**data.model_dump())
        db.add(coupon_type)
        db.commit()
        db.refresh(coupon_type)
        return coupon_type
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating coupon type"
        )


@router.get("/coupon-types", summary="Listar tipos de cupons")
def list_coupon_types(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista tipos de cupons com paginação.
    """
    query = db.query(coupon_models.CouponType).order_by(coupon_models.CouponType.id)
    return paginate_query(query, page, page_size)


@router.get("/coupon-types/{type_id}", response_model=coupon_schemas.CouponTypeResponse,
            summary="Obter detalhes do tipo de cupom")
def get_coupon_type(
    type_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um tipo de cupom específico.
    """
    coupon_type = db.query(coupon_models.CouponType).filter(
        coupon_models.CouponType.id == type_id
    ).first()
    
    if not coupon_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon type not found"
        )
    
    return coupon_type


# ========= Coupon Offer endpoints =========
@router.post("/coupon-offers", response_model=coupon_schemas.CouponOfferResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Criar oferta de cupom")
def create_coupon_offer(
    data: coupon_schemas.CouponOfferCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova oferta de cupom.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se coupon_type existe
    coupon_type = db.query(coupon_models.CouponType).filter(
        coupon_models.CouponType.id == data.coupon_type_id
    ).first()
    if not coupon_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon type not found"
        )
    
    try:
        # Criar oferta com current_quantity igual a initial_quantity
        offer_data = data.model_dump()
        offer_data['current_quantity'] = offer_data['initial_quantity']
        
        offer = coupon_models.CouponOffer(**offer_data)
        db.add(offer)
        db.commit()
        db.refresh(offer)
        return offer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating coupon offer"
        )


@router.get("/coupon-offers", summary="Listar ofertas de cupons")
def list_coupon_offers(
    entity_scope: Optional[str] = Query(None, description="Filtrar por escopo (CUSTOMER, FRANCHISE, STORE)"),
    entity_id: Optional[UUID4] = Query(None, description="Filtrar por ID da entidade"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista ofertas de cupons com paginação.
    """
    query = db.query(coupon_models.CouponOffer)
    
    if entity_scope:
        query = query.filter(coupon_models.CouponOffer.entity_scope == entity_scope)
    
    if entity_id:
        query = query.filter(coupon_models.CouponOffer.entity_id == entity_id)
    
    if is_active is not None:
        query = query.filter(coupon_models.CouponOffer.is_active == is_active)
    
    query = query.order_by(coupon_models.CouponOffer.created_at.desc())
    return paginate_query(query, page, page_size)


@router.get("/coupon-offers/{offer_id}", response_model=coupon_schemas.CouponOfferResponse,
            summary="Obter detalhes da oferta")
def get_coupon_offer(
    offer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma oferta de cupom específica.
    """
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    return offer


@router.patch("/coupon-offers/{offer_id}", response_model=coupon_schemas.CouponOfferResponse,
              summary="Atualizar oferta de cupom")
def update_coupon_offer(
    offer_id: UUID4,
    data: coupon_schemas.CouponOfferUpdate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza uma oferta de cupom.
    Para inventory (current_quantity), apenas incrementos são permitidos.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).with_for_update().first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    try:
        update_data = data.model_dump(exclude_unset=True)
        
        # Validar current_quantity (apenas incrementos)
        if "current_quantity" in update_data:
            new_quantity = update_data["current_quantity"]
            
            # Contar cupons emitidos
            issued_count = db.query(func.count(coupon_models.Coupon.id)).filter(
                coupon_models.Coupon.offer_id == offer_id
            ).scalar()
            
            if new_quantity < issued_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reduce current_quantity below issued count ({issued_count})"
                )
        
        # Validar initial_quantity
        if "initial_quantity" in update_data:
            new_initial = update_data["initial_quantity"]
            if new_initial < offer.current_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="initial_quantity cannot be less than current_quantity"
                )
        
        for key, value in update_data.items():
            setattr(offer, key, value)
        
        db.commit()
        db.refresh(offer)
        return offer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating coupon offer"
        )


@router.delete("/coupon-offers/{offer_id}", summary="Deletar oferta de cupom")
def delete_coupon_offer(
    offer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma oferta de cupom (com cascata para cupons emitidos).
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    try:
        db.delete(offer)
        db.commit()
        return {"message": "Coupon offer deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting coupon offer"
        )


# ========= Offer Asset endpoints =========
@router.post("/coupon-offers/{offer_id}/assets", response_model=coupon_schemas.OfferAssetResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Adicionar asset à oferta")
def create_offer_asset(
    offer_id: UUID4,
    data: coupon_schemas.OfferAssetCreate,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Adiciona um asset (imagem) a uma oferta de cupom.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN", "FRANCHISE_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se offer existe
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    # Validar kind
    if data.kind not in ["BANNER", "THUMB", "DETAIL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset kind. Must be BANNER, THUMB, or DETAIL"
        )
    
    try:
        # Garantir que offer_id no data corresponde ao da rota
        asset_data = data.model_dump()
        asset_data["offer_id"] = offer_id
        
        asset = coupon_models.OfferAsset(**asset_data)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating offer asset"
        )


# ========= Statistics endpoint =========
@router.get("/coupon-offers/{offer_id}/stats", response_model=coupon_schemas.CouponOfferStatsResponse,
            summary="Obter estatísticas da oferta")
def get_offer_stats(
    offer_id: UUID4,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas detalhadas de uma oferta de cupom.
    """
    # Verificar se offer existe
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).first()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    # Contar por status
    total_issued = db.query(func.count(coupon_models.Coupon.id)).filter(
        coupon_models.Coupon.offer_id == offer_id,
        coupon_models.Coupon.status == "ISSUED"
    ).scalar() or 0
    
    total_reserved = db.query(func.count(coupon_models.Coupon.id)).filter(
        coupon_models.Coupon.offer_id == offer_id,
        coupon_models.Coupon.status == "RESERVED"
    ).scalar() or 0
    
    total_redeemed = db.query(func.count(coupon_models.Coupon.id)).filter(
        coupon_models.Coupon.offer_id == offer_id,
        coupon_models.Coupon.status == "REDEEMED"
    ).scalar() or 0
    
    total_cancelled = db.query(func.count(coupon_models.Coupon.id)).filter(
        coupon_models.Coupon.offer_id == offer_id,
        coupon_models.Coupon.status == "CANCELLED"
    ).scalar() or 0
    
    total_expired = db.query(func.count(coupon_models.Coupon.id)).filter(
        coupon_models.Coupon.offer_id == offer_id,
        coupon_models.Coupon.status == "EXPIRED"
    ).scalar() or 0
    
    # Resgates por loja
    redemption_by_store_query = text("""
    SELECT s.id AS store_id, s.name AS store_name, COUNT(c.id) AS count
    FROM coupon c
    JOIN store s ON c.redeemed_store_id = s.id
    WHERE c.offer_id = :offer_id AND c.status = 'REDEEMED'
    GROUP BY s.id, s.name
    ORDER BY count DESC
    """)
    
    redemption_by_store_result = db.execute(
        redemption_by_store_query,
        {"offer_id": str(offer_id)}
    ).fetchall()
    
    redemption_by_store = [
        {
            "store_id": str(row.store_id),
            "store_name": row.store_name,
            "count": row.count
        }
        for row in redemption_by_store_result
    ]
    
    # Timeline de resgates (por dia)
    redemption_timeline_query = text("""
    SELECT DATE(redeemed_at) AS date, COUNT(*) AS count
    FROM coupon
    WHERE offer_id = :offer_id AND status = 'REDEEMED' AND redeemed_at IS NOT NULL
    GROUP BY DATE(redeemed_at)
    ORDER BY date DESC
    LIMIT 30
    """)
    
    redemption_timeline_result = db.execute(
        redemption_timeline_query,
        {"offer_id": str(offer_id)}
    ).fetchall()
    
    redemption_timeline = [
        {
            "date": row.date.isoformat() if row.date else None,
            "count": row.count
        }
        for row in redemption_timeline_result
    ]
    
    return {
        "total_issued": total_issued,
        "total_reserved": total_reserved,
        "total_redeemed": total_redeemed,
        "total_cancelled": total_cancelled,
        "total_expired": total_expired,
        "redemption_by_store": redemption_by_store,
        "redemption_timeline": redemption_timeline
    }


# ========= Cancel Coupon endpoint =========
@router.post("/coupons/{coupon_id}/cancel", summary="Cancelar cupom")
def cancel_coupon(
    coupon_id: UUID4,
    data: coupon_schemas.CancelCouponRequest,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancela um cupom emitido (apenas se não foi resgatado).
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    coupon = db.query(coupon_models.Coupon).filter(
        coupon_models.Coupon.id == coupon_id
    ).first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    if coupon.status == "REDEEMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a redeemed coupon"
        )
    
    if coupon.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is already cancelled"
        )
    
    try:
        coupon.status = "CANCELLED"
        
        # Registrar auditoria
        audit = system_models.AuditLog(
            actor_user_id=current_user.id,
            action="COUPON_CANCEL",
            target_table="coupon",
            target_id=str(coupon.id),
            before={"status": coupon.status},
            after={"status": "CANCELLED", "reason": data.reason}
        )
        db.add(audit)
        
        db.commit()
        return {"message": "Coupon cancelled successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error cancelling coupon"
        )


# ========= Bulk Issue endpoint =========
@router.post("/offers/{offer_id}/bulk-issue", response_model=coupon_schemas.BulkIssueCouponResponse,
             summary="Emissão em massa de cupons")
def bulk_issue_coupons(
    offer_id: UUID4,
    data: coupon_schemas.BulkIssueCouponRequest,
    current_user: user_models.AppUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Emite cupons em massa para um segmento de clientes.
    Requer permissão de ADMIN ou CUSTOMER_ADMIN.
    
    NOTA: Esta é uma implementação simplificada. Em produção,
    isso deveria ser feito de forma assíncrona via job/task queue.
    """
    if current_user.role not in ["ADMIN", "GLOBAL_ADMIN", "CUSTOMER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verificar se offer existe
    offer = db.query(coupon_models.CouponOffer).filter(
        coupon_models.CouponOffer.id == offer_id
    ).with_for_update().first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon offer not found"
        )
    
    # Verificar estoque disponível
    if offer.current_quantity < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory. Available: {offer.current_quantity}, Requested: {data.quantity}"
        )
    
    # Encontrar pessoas que correspondem aos critérios de segmentação
    # Implementação simplificada - em produção, isso seria mais sofisticado
    persons_query = db.query(user_models.Person).limit(data.quantity)
    persons = persons_query.all()
    
    if len(persons) < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough persons match the criteria. Found: {len(persons)}, Requested: {data.quantity}"
        )
    
    job_id = uuid.uuid4()
    
    try:
        # Emitir cupons para cada pessoa
        for person in persons[:data.quantity]:
            code = secrets.token_urlsafe(16)
            code_hash_value = hash_coupon_code(code)
            
            coupon = coupon_models.Coupon(
                offer_id=offer_id,
                issued_to_person_id=person.id,
                code_hash=code_hash_value,
                status="ISSUED"
            )
            db.add(coupon)
            
            # Criar evento de outbox
            event = system_models.OutboxEvent(
                topic="coupon.bulk_issued",
                payload={
                    "job_id": str(job_id),
                    "coupon_id": str(coupon.id),
                    "offer_id": str(offer_id),
                    "person_id": str(person.id)
                },
                status="PENDING"
            )
            db.add(event)
        
        # Decrementar estoque
        offer.current_quantity -= data.quantity
        
        db.commit()
        
        return {
            "job_id": job_id,
            "offer_id": offer_id,
            "quantity_requested": data.quantity,
            "status": "COMPLETED",
            "message": f"Successfully issued {data.quantity} coupons"
        }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error during bulk issuance: {str(e)}"
        )
