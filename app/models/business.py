"""
Business structure models: Customer, Franchise, Store, Device
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

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
