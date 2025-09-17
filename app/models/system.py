"""
System and auxiliary models: ApiKey, IdempotencyKey, RateLimitCounter, AuditLog, OutboxEvent
"""
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

class ApiKey(Base):
    __tablename__ = "api_key"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    key_hash = Column(BYTEA, nullable=False)
    scopes = Column(ARRAY(String), nullable=False, default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    revoked_at = Column(TIMESTAMP(timezone=True))

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
