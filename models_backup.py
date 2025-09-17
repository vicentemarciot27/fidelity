from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, ARRAY, Enum as SQLEnum, LargeBinary, CheckConstraint, TIMESTAMP, Numeric, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
import uuid
import enum
from database import Base

# Definição de enums
class ScopeEnum(str, enum.Enum):
    GLOBAL = "GLOBAL"
    CUSTOMER = "CUSTOMER"
    FRANCHISE = "FRANCHISE"
    STORE = "STORE"

class RedeemTypeEnum(str, enum.Enum):
    BRL = "BRL"
    PERCENTAGE = "PERCENTAGE"
    FREE_SKU = "FREE_SKU"

class CouponStatusEnum(str, enum.Enum):
    CREATED = "CREATED"
    ISSUED = "ISSUED"
    RESERVED = "RESERVED"
    REDEEMED = "REDEEMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

# Entidades principais
class Customer(Base):
    __tablename__ = "customer"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cnpj = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    contact_email = Column(String)
    phone = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    franchises = relationship("Franchise", back_populates="customer")
    marketplace_rules = relationship("CustomerMarketplaceRules", back_populates="customer", uselist=False)
    point_rules = relationship("PointRules", back_populates="customer")

class Franchise(Base):
    __tablename__ = "franchise"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    cnpj = Column(String, unique=True)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    customer = relationship("Customer", back_populates="franchises")
    stores = relationship("Store", back_populates="franchise")
    point_rules = relationship("PointRules", back_populates="franchise")

class Store(Base):
    __tablename__ = "store"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchise.id", ondelete="CASCADE"), nullable=False)
    cnpj = Column(String, unique=True)
    name = Column(String, nullable=False)
    location = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    franchise = relationship("Franchise", back_populates="stores")
    orders = relationship("Order", back_populates="store")
    devices = relationship("Device", back_populates="store")
    point_rules = relationship("PointRules", back_populates="store")
    staff = relationship("StoreStaff", back_populates="store")

class Person(Base):
    __tablename__ = "person"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpf = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    location = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("AppUser", back_populates="person", uselist=False)
    point_transactions = relationship("PointTransaction", back_populates="person")
    coupons = relationship("Coupon", back_populates="issued_to_person")
    orders = relationship("Order", back_populates="person")

class AppUser(Base):
    __tablename__ = "app_user"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    person = relationship("Person", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    store_staff = relationship("StoreStaff", back_populates="user")

# Configurações e regras
class CustomerMarketplaceRules(Base):
    __tablename__ = "customer_marketplace_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), unique=True, nullable=False)
    rules = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="marketplace_rules")

class PointRules(Base):
    __tablename__ = "point_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(SQLEnum(ScopeEnum), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"))
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchise.id", ondelete="CASCADE"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id", ondelete="CASCADE"))
    points_per_brl = Column(Numeric(12, 4))
    expires_in_days = Column(Integer)
    extra = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint(
            "(scope = 'CUSTOMER' AND customer_id IS NOT NULL AND franchise_id IS NULL AND store_id IS NULL) OR "
            "(scope = 'FRANCHISE' AND franchise_id IS NOT NULL AND store_id IS NULL) OR "
            "(scope = 'STORE' AND store_id IS NOT NULL) OR "
            "(scope = 'GLOBAL' AND customer_id IS NULL AND franchise_id IS NULL AND store_id IS NULL)"
        ),
    )
    
    customer = relationship("Customer", back_populates="point_rules")
    franchise = relationship("Franchise", back_populates="point_rules")
    store = relationship("Store", back_populates="point_rules")

# Transações de pontos e wallet view
class PointTransaction(Base):
    __tablename__ = "point_transaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    scope = Column(SQLEnum(ScopeEnum), nullable=False)
    scope_id = Column(UUID(as_uuid=True))
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"))
    order_id = Column(String)
    delta = Column(Integer, nullable=False)
    details = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("delta <> 0"),
    )
    
    person = relationship("Person", back_populates="point_transactions")
    store = relationship("Store")

# Modelos para cupons
class CouponType(Base):
    __tablename__ = "coupon_type"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_specific = Column(Boolean, nullable=False, default=False)
    redeem_type = Column(SQLEnum(RedeemTypeEnum), nullable=False)
    discount_amount_brl = Column(Numeric(12, 2))
    discount_amount_percentage = Column(Numeric(5, 2))
    valid_skus = Column(ARRAY(String))
    
    __table_args__ = (
        CheckConstraint(
            "(redeem_type = 'BRL' AND discount_amount_brl IS NOT NULL) OR "
            "(redeem_type = 'PERCENTAGE' AND discount_amount_percentage IS NOT NULL) OR "
            "(redeem_type = 'FREE_SKU' AND valid_skus IS NOT NULL)"
        ),
    )
    
    offers = relationship("CouponOffer", back_populates="coupon_type")

class CouponOffer(Base):
    __tablename__ = "coupon_offer"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_scope = Column(SQLEnum(ScopeEnum), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    coupon_type_id = Column(UUID(as_uuid=True), ForeignKey("coupon_type.id"), nullable=False)
    customer_segment = Column(JSONB)
    initial_quantity = Column(Integer, nullable=False, default=0)
    current_quantity = Column(Integer, nullable=False, default=0)
    max_per_customer = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    start_at = Column(TIMESTAMP(timezone=True))
    end_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("entity_scope IN ('CUSTOMER', 'FRANCHISE', 'STORE')"),
        CheckConstraint("current_quantity <= initial_quantity"),
        CheckConstraint("initial_quantity >= 0"),
        CheckConstraint("current_quantity >= 0"),
    )
    
    coupon_type = relationship("CouponType", back_populates="offers")
    coupons = relationship("Coupon", back_populates="offer")
    assets = relationship("OfferAsset", back_populates="offer")

class Coupon(Base):
    __tablename__ = "coupon"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("coupon_offer.id", ondelete="CASCADE"), nullable=False)
    issued_to_person_id = Column(UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    code_hash = Column(BYTEA, nullable=False)
    status = Column(SQLEnum(CouponStatusEnum), nullable=False, default=CouponStatusEnum.ISSUED)
    issued_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    redeemed_at = Column(TIMESTAMP(timezone=True))
    redeemed_store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"))
    
    __table_args__ = (
        CheckConstraint("status IN ('ISSUED', 'RESERVED', 'REDEEMED', 'CANCELLED', 'EXPIRED')"),
    )
    
    offer = relationship("CouponOffer", back_populates="coupons")
    issued_to_person = relationship("Person", back_populates="coupons")
    redeemed_store = relationship("Store")

# Tabelas auxiliares
class Order(Base):
    __tablename__ = "order"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"))
    total_brl = Column(Numeric(12, 2), nullable=False)
    tax_brl = Column(Numeric(12, 2), nullable=False, default=0)
    items = Column(JSONB, nullable=False)
    shipping = Column(JSONB)
    checkout_ref = Column(String)
    external_id = Column(String)
    source = Column(String, nullable=False, default="PDV")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    store = relationship("Store", back_populates="orders")
    person = relationship("Person", back_populates="orders")

class RefreshToken(Base):
    __tablename__ = "refresh_token"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(BYTEA, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True))
    
    user = relationship("AppUser", back_populates="refresh_tokens")

class ApiKey(Base):
    __tablename__ = "api_key"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    key_hash = Column(BYTEA, nullable=False)
    scopes = Column(ARRAY(String), nullable=False, default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    revoked_at = Column(TIMESTAMP(timezone=True))

class StoreStaff(Base):
    __tablename__ = "store_staff"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    
    __table_args__ = (
        CheckConstraint("role IN ('STORE_MANAGER', 'CASHIER')"),
    )
    
    user = relationship("AppUser", back_populates="store_staff")
    store = relationship("Store", back_populates="staff")

class Device(Base):
    __tablename__ = "device"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    registration_code = Column(String, nullable=False)
    public_key = Column(BYTEA)
    last_seen_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    store = relationship("Store", back_populates="devices")

class Category(Base):
    __tablename__ = "category"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    
    skus = relationship("SKU", back_populates="category")

class SKU(Base):
    __tablename__ = "sku"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String)
    category_id = Column(UUID(as_uuid=True), ForeignKey("category.id"))
    custom_metadata = Column(JSONB, nullable=False, server_default='{}')
    
    category = relationship("Category", back_populates="skus")

class OfferAsset(Base):
    __tablename__ = "offer_asset"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("coupon_offer.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String, nullable=False)
    url = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("kind IN ('BANNER', 'THUMB', 'DETAIL')"),
    )
    
    offer = relationship("CouponOffer", back_populates="assets")

class IdempotencyKey(Base):
    __tablename__ = "idempotency_key"
    
    key = Column(String, primary_key=True)
    owner_scope = Column(String, nullable=False)
    request_hash = Column(BYTEA, nullable=False)
    response_body = Column(BYTEA)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counter"
    
    key = Column(String, primary_key=True)
    count = Column(Integer, nullable=False)
    window_start = Column(TIMESTAMP(timezone=True), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id"))
    actor_device_id = Column(UUID(as_uuid=True), ForeignKey("device.id"))
    action = Column(String, nullable=False)
    target_table = Column(String)
    target_id = Column(String)
    before = Column(JSONB)
    after = Column(JSONB)
    ip = Column(INET)
    user_agent = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class OutboxEvent(Base):
    __tablename__ = "outbox_event"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    sent_at = Column(TIMESTAMP(timezone=True))

# Views SQL declarativas
# Views para carteiras de pontos e cupons
# Essas views são definidas usando o SQLAlchemy Core
from sqlalchemy import select, func, case, and_, text

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
