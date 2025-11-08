"""
Pytest configuration and fixtures for testing
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
import os
import random
from dotenv import load_dotenv

# Import base and models
from database import Base, get_db
from main import app
from app.models import user as user_models
from app.models import business as business_models
from app.models import coupons as coupon_models
from app.models import points as points_models
from app.models import views as views_models
from app.core.security import get_password_hash

# Helper functions to generate unique test data
def generate_unique_cpf():
    """Generate a unique CPF for testing"""
    return f"{random.randint(10000000000, 99999999999)}"

def generate_unique_cnpj():
    """Generate a unique CNPJ for testing"""
    return f"{random.randint(10000000000000, 99999999999999)}"

def generate_unique_email():
    """Generate a unique email for testing"""
    return f"test_{uuid4().hex[:8]}@example.com"

# Load environment variables
load_dotenv()

# Use PostgreSQL test database
# You can set TEST_DATABASE_URL in your .env file, otherwise it will use the test database on port 5433
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/fidelity_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database views once before all tests
@pytest.fixture(scope="module", autouse=True)
def setup_views():
    """Create database views before running tests"""
    views_models.create_views(engine)
    yield
    # Views persist, no cleanup needed


@pytest.fixture(scope="function")
def db():
    """
    Create a database session for each test.
    Uses the existing database without creating or dropping tables.
    """
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with overridden database dependency
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_person(db):
    """
    Create a sample person for testing
    """
    person = user_models.Person(
        id=uuid4(),
        cpf=generate_unique_cpf(),
        name="Test User",
        phone="11999999999"
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def sample_user(db, sample_person):
    """
    Create a sample app user for testing
    """
    user = user_models.AppUser(
        id=uuid4(),
        person_id=sample_person.id,
        email=generate_unique_email(),
        password_hash=get_password_hash("testpassword123"),
        role="USER",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_admin_user(db):
    """
    Create a sample admin user for testing
    """
    person = user_models.Person(
        id=uuid4(),
        cpf=generate_unique_cpf(),
        name="Admin User",
        phone="11988888888"
    )
    db.add(person)
    db.flush()
    
    user = user_models.AppUser(
        id=uuid4(),
        person_id=person.id,
        email=generate_unique_email(),
        password_hash=get_password_hash("adminpass123"),
        role="ADMIN",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_customer(db):
    """
    Create a sample customer for testing
    """
    customer = business_models.Customer(
        id=uuid4(),
        name="Test Customer",
        cnpj=generate_unique_cnpj(),
        contact_email=generate_unique_email(),
        phone="1133334444"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def sample_franchise(db, sample_customer):
    """
    Create a sample franchise for testing
    """
    franchise = business_models.Franchise(
        id=uuid4(),
        customer_id=sample_customer.id,
        name="Test Franchise",
        cnpj=generate_unique_cnpj()
    )
    db.add(franchise)
    db.commit()
    db.refresh(franchise)
    return franchise


@pytest.fixture
def sample_store(db, sample_franchise):
    """
    Create a sample store for testing
    """
    store = business_models.Store(
        id=uuid4(),
        franchise_id=sample_franchise.id,
        name="Test Store",
        cnpj=generate_unique_cnpj(),
        location={"address": "123 Test St"}
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@pytest.fixture
def sample_point_rule(db, sample_store):
    """
    Create a sample point rule for testing
    """
    rule = points_models.PointRules(
        id=uuid4(),
        scope="STORE",
        store_id=sample_store.id,
        points_per_brl=1.0,
        expires_in_days=365
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@pytest.fixture
def sample_coupon_type(db):
    """
    Create a sample coupon type for testing
    """
    coupon_type = coupon_models.CouponType(
        id=uuid4(),
        redeem_type="BRL",
        discount_amount_brl=10.0,
        sku_specific=False
    )
    db.add(coupon_type)
    db.commit()
    db.refresh(coupon_type)
    return coupon_type


@pytest.fixture
def sample_coupon_offer(db, sample_customer, sample_coupon_type):
    """
    Create a sample coupon offer for testing
    """
    offer = coupon_models.CouponOffer(
        id=uuid4(),
        entity_scope="CUSTOMER",
        entity_id=sample_customer.id,
        coupon_type_id=sample_coupon_type.id,
        initial_quantity=100,
        current_quantity=50,
        max_per_customer=5,
        is_active=True,
        start_at=datetime.utcnow() - timedelta(days=1),
        end_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@pytest.fixture
def sample_coupon(db, sample_coupon_offer, sample_person):
    """
    Create a sample coupon for testing
    """
    import hashlib
    code = "test_coupon_code_123"
    code_hash = hashlib.sha256(code.encode()).digest()
    
    coupon = coupon_models.Coupon(
        id=uuid4(),
        offer_id=sample_coupon_offer.id,
        issued_to_person_id=sample_person.id,
        code_hash=code_hash,
        status="ISSUED"
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon, code


@pytest.fixture
def auth_headers(client, sample_user, db):
    """
    Get authentication headers for a user
    """
    # Create a fresh user with known credentials for login
    person = user_models.Person(
        id=uuid4(),
        cpf=generate_unique_cpf(),
        name="Auth Test User",
        phone="11999999999"
    )
    db.add(person)
    db.flush()
    
    email = generate_unique_email()
    user = user_models.AppUser(
        id=uuid4(),
        person_id=person.id,
        email=email,
        password_hash=get_password_hash("testpassword123"),
        role="USER",
        is_active=True
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_get_current_user(sample_user):
    """
    Mock the get_current_active_user dependency
    """
    def _mock():
        return sample_user
    return _mock

