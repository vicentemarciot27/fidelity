from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib

# Import all models
from app.models import user, business, coupons, points, orders, config, system
from app.models.views import create_views
from app.core.security import get_password_hash

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/fidelity_test"
engine = create_engine(TEST_DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create extension
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
    conn.commit()

# Drop all views first (they depend on tables)
print("🗑️  Removendo todas as views existentes...")
with engine.connect() as conn:
    conn.execute(text("DROP VIEW IF EXISTS v_coupon_wallet CASCADE;"))
    conn.execute(text("DROP VIEW IF EXISTS v_point_wallet CASCADE;"))
    conn.commit()

# Drop all existing tables (destructive)
print("🗑️  Removendo todas as tabelas existentes...")
Base.metadata.drop_all(bind=engine)

# Create tables
print("🔨 Criando todas as tabelas...")
Base.metadata.create_all(bind=engine)

# Create views
print("👁️  Criando views...")
create_views(engine)