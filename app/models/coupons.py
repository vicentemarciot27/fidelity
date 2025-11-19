"""
Coupon system models: CouponType, CouponOffer, Coupon, OfferAsset
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, CheckConstraint, Enum as SQLEnum, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base
from .enums import ScopeEnum, RedeemTypeEnum, CouponStatusEnum

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
    points_cost = Column(Integer, nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True)
    start_at = Column(TIMESTAMP(timezone=True))
    end_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("entity_scope IN ('CUSTOMER', 'FRANCHISE', 'STORE')"),
        CheckConstraint("current_quantity <= initial_quantity"),
        CheckConstraint("initial_quantity >= 0"),
        CheckConstraint("current_quantity >= 0"),
        CheckConstraint("points_cost >= 0"),
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
