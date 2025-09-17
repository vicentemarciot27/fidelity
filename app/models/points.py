"""
Points and loyalty program models: PointRules, PointTransaction
"""
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, CheckConstraint, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base
from .enums import ScopeEnum

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

class PointTransaction(Base):
    __tablename__ = "point_transaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    scope = Column(SQLEnum(ScopeEnum), nullable=False)
    scope_id = Column(UUID(as_uuid=True))
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"))
    order_id = Column(String(50))
    delta = Column(Integer, nullable=False)
    details = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("delta <> 0"),
    )
    
    person = relationship("Person", back_populates="point_transactions")
    store = relationship("Store")
