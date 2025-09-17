"""
Database views for wallet calculations
"""
from sqlalchemy import text

def create_views(engine):
    """Create or update database views"""
    
    # Definição da view de carteira de pontos
    point_wallet_view = text("""
    CREATE OR REPLACE VIEW v_point_wallet AS
    SELECT
      person_id,
      scope,
      scope_id,
      SUM(delta) FILTER (WHERE expires_at IS NULL OR expires_at > now()) AS points
    FROM point_transaction
    GROUP BY person_id, scope, scope_id;
    """)

    # Definição da view de carteira de cupons
    coupon_wallet_view = text("""
    CREATE OR REPLACE VIEW v_coupon_wallet AS
    SELECT
      issued_to_person_id AS person_id,
      offer_id AS coupon_offer_id,
      COUNT(*) FILTER (WHERE status IN ('ISSUED','RESERVED')) AS available_count,
      COUNT(*) FILTER (WHERE status = 'REDEEMED') AS redeemed_count
    FROM coupon
    GROUP BY issued_to_person_id, offer_id;
    """)
    
    with engine.connect() as conn:
        conn.execute(point_wallet_view)
        conn.execute(coupon_wallet_view)
        conn.commit()
