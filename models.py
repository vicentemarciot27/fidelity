"""
Legacy models.py file for backward compatibility
This imports all models from the new organized structure
"""

# Import all models to maintain backward compatibility
from app.models.enums import *
from app.models.user import *
from app.models.business import *
from app.models.points import *
from app.models.coupons import *
from app.models.orders import *
from app.models.config import *
from app.models.system import *
from app.models.views import *

# Re-export Base for compatibility
from app.models import Base

# Keep the existing views definitions for compatibility
from sqlalchemy import text

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
