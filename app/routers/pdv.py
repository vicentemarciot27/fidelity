"""
PDV (Point of Sale) routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime, timedelta
import math

from database import get_db
from ..models import user as user_models
from ..models import business as business_models
from ..models import coupons as coupon_models
from ..models import orders as order_models
from ..models import points as points_models
from ..models import system as system_models
from ..schemas.coupons import AttemptCouponRequest, AttemptCouponResponse, RedeemCouponRequest
from ..schemas.points import EarnPointsRequest, EarnPointsResponse
from .offers import hash_coupon_code, verify_coupon_code

router = APIRouter(prefix="/pdv", tags=["pdv"])

@router.post("/attempt-coupon", response_model=AttemptCouponResponse,
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
    coupons = db.query(coupon_models.Coupon).filter(
        coupon_models.Coupon.status.in_(["ISSUED", "RESERVED"])
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
    offer = db.query(coupon_models.CouponOffer).filter(coupon_models.CouponOffer.id == coupon.offer_id).first()
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
    coupon_type = db.query(coupon_models.CouponType).filter(coupon_models.CouponType.id == offer.coupon_type_id).first()
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
        coupon_for_update = db.query(coupon_models.Coupon).filter(
            coupon_models.Coupon.id == coupon.id
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

@router.post("/redeem", summary="Resgatar cupom")
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
    coupon = db.query(coupon_models.Coupon).filter(
        coupon_models.Coupon.id == data.coupon_id,
        coupon_models.Coupon.status == "RESERVED"
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
            order = order_models.Order(
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
        event = system_models.OutboxEvent(
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

@router.post("/earn-points", response_model=EarnPointsResponse, status_code=status.HTTP_201_CREATED,
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
        person = db.query(user_models.Person).filter(user_models.Person.id == data.person_id).first()
    elif data.cpf:
        person = db.query(user_models.Person).filter(user_models.Person.cpf == data.cpf).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Validar store_id
    store = db.query(business_models.Store).filter(business_models.Store.id == data.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Buscar franchise e customer da store
    franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == store.franchise_id).first()
    if not franchise:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Store does not have a valid franchise"
        )
    
    # Encontrar regra de pontos mais específica (STORE > FRANCHISE > CUSTOMER > GLOBAL)
    point_rule = None
    
    # Tentar regra por loja
    point_rule = db.query(points_models.PointRules).filter(
        points_models.PointRules.scope == "STORE",
        points_models.PointRules.store_id == store.id
    ).first()
    
    # Tentar regra por franquia
    if not point_rule:
        point_rule = db.query(points_models.PointRules).filter(
            points_models.PointRules.scope == "FRANCHISE",
            points_models.PointRules.franchise_id == franchise.id
        ).first()
    
    # Tentar regra por cliente
    if not point_rule:
        point_rule = db.query(points_models.PointRules).filter(
            points_models.PointRules.scope == "CUSTOMER",
            points_models.PointRules.customer_id == franchise.customer_id
        ).first()
    
    # Tentar regra global
    if not point_rule:
        point_rule = db.query(points_models.PointRules).filter(
            points_models.PointRules.scope == "GLOBAL"
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
        order = order_models.Order(
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
        transaction = points_models.PointTransaction(
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
