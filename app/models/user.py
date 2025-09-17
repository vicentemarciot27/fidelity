"""
User-related models: Person, AppUser, RefreshToken, StoreStaff
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

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

class RefreshToken(Base):
    __tablename__ = "refresh_token"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(BYTEA, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True))
    
    user = relationship("AppUser", back_populates="refresh_tokens")

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
