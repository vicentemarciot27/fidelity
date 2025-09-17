"""
Order and product models: Order, SKU, Category
"""
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

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
