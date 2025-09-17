"""
Wallet routes for checking points and coupons
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from ..models import user as user_models
from ..models import business as business_models
from ..models import points as points_models
from ..schemas.wallet import WalletResponse
from ..core.security import get_current_active_user

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("", response_model=WalletResponse, summary="Consultar carteira do usuário")
def get_wallet(
    display_as: str = "points",
    current_user: user_models.AppUser = Depends(get_current_active_user),
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
                points_rule = db.query(points_models.PointRules).filter(
                    points_models.PointRules.scope == "STORE",
                    points_models.PointRules.store_id == row.scope_id
                ).first()
            
            if not points_rule and row.scope in ["STORE", "FRANCHISE"] and row.scope_id:
                # Obter franchise_id do store se necessário
                franchise_id = None
                if row.scope == "STORE":
                    store = db.query(business_models.Store).filter(business_models.Store.id == row.scope_id).first()
                    if store:
                        franchise_id = store.franchise_id
                else:
                    franchise_id = row.scope_id
                    
                if franchise_id:
                    points_rule = db.query(points_models.PointRules).filter(
                        points_models.PointRules.scope == "FRANCHISE",
                        points_models.PointRules.franchise_id == franchise_id
                    ).first()
            
            if not points_rule and row.scope in ["STORE", "FRANCHISE", "CUSTOMER"] and row.scope_id:
                # Obter customer_id
                customer_id = None
                if row.scope == "STORE":
                    store = db.query(business_models.Store).filter(business_models.Store.id == row.scope_id).first()
                    if store:
                        franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == store.franchise_id).first()
                        if franchise:
                            customer_id = franchise.customer_id
                elif row.scope == "FRANCHISE":
                    franchise = db.query(business_models.Franchise).filter(business_models.Franchise.id == row.scope_id).first()
                    if franchise:
                        customer_id = franchise.customer_id
                else:
                    customer_id = row.scope_id
                
                if customer_id:
                    points_rule = db.query(points_models.PointRules).filter(
                        points_models.PointRules.scope == "CUSTOMER",
                        points_models.PointRules.customer_id == customer_id
                    ).first()
            
            # Regra global se nenhuma das anteriores
            if not points_rule:
                points_rule = db.query(points_models.PointRules).filter(
                    points_models.PointRules.scope == "GLOBAL"
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
