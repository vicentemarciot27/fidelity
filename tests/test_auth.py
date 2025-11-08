"""
Unit tests for authentication endpoints
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import random

from app.models import user as user_models
from app.core.security import verify_password, get_password_hash
import bcrypt


class TestRegisterEndpoint:
    """Test cases for user registration"""
    
    def test_register_new_user_success(self, client, db):
        """Test successful user registration"""
        # Use unique values to avoid conflicts with other tests
        unique_id = uuid4().hex[:8]
        user_data = {
            "email": f"newuser_{unique_id}@example.com",
            "password": "securepassword123",
            "name": "New User",
            "cpf": f"{random.randint(10000000000, 99999999999)}",
            "phone": "11999887766",
            "role": "USER"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user was created in database
        user = db.query(user_models.AppUser).filter(
            user_models.AppUser.email == user_data["email"]
        ).first()
        assert user is not None
        assert user.email == user_data["email"]
        assert user.role == "USER"
        assert user.is_active is True
        
        # Verify person was created
        person = db.query(user_models.Person).filter(
            user_models.Person.cpf == user_data["cpf"]
        ).first()
        assert person is not None
        assert person.name == user_data["name"]
        assert person.phone == user_data["phone"]
    
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": sample_user.email,
            "password": "password123",
            "name": "Duplicate User",
            "cpf": "99988877766",
            "role": "USER"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email já registrado" in response.json()["detail"]
    
    def test_register_duplicate_cpf(self, client, sample_person):
        """Test registration with duplicate CPF"""
        user_data = {
            "email": "unique@example.com",
            "password": "password123",
            "name": "Duplicate CPF User",
            "cpf": sample_person.cpf,
            "role": "USER"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "CPF já registrado" in response.json()["detail"]
    
    def test_register_password_hashing(self, client, db):
        """Test that passwords are properly hashed"""
        password = "mysecretpassword123"
        # Use unique values to avoid conflicts
        unique_id = uuid4().hex[:8]
        user_data = {
            "email": f"hashtest_{unique_id}@example.com",
            "password": password,
            "name": "Hash Test User",
            "cpf": f"{random.randint(10000000000, 99999999999)}",
            "role": "USER"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify password is hashed
        user = db.query(user_models.AppUser).filter(
            user_models.AppUser.email == user_data["email"]
        ).first()
        assert user.password_hash != password
        assert verify_password(password, user.password_hash)


class TestLoginEndpoint:
    """Test cases for user login"""
    
    def test_login_success(self, client, sample_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, sample_user):
        """Test login with incorrect password"""
        response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "wrongpassword"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_creates_refresh_token(self, client, db, sample_user):
        """Test that login creates a refresh token in database"""
        response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify refresh token was created
        refresh_token = db.query(user_models.RefreshToken).filter(
            user_models.RefreshToken.user_id == sample_user.id
        ).first()
        assert refresh_token is not None
        assert refresh_token.revoked_at is None
        assert refresh_token.expires_at > datetime.now(timezone.utc)


class TestOAuth2LoginEndpoint:
    """Test cases for OAuth2 login (Swagger UI compatibility)"""
    
    def test_oauth2_login_success(self, client, sample_user):
        """Test successful OAuth2 login"""
        response = client.post(
            "/auth/token",
            data={"username": sample_user.email, "password": "testpassword123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_oauth2_login_invalid_credentials(self, client):
        """Test OAuth2 login with invalid credentials"""
        response = client.post(
            "/auth/token",
            data={"username": "invalid@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshTokenEndpoint:
    """Test cases for token refresh"""
    
    def test_refresh_token_success(self, client, db, sample_user):
        """Test successful token refresh"""
        # First login to get refresh token
        login_response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify old token was revoked
        old_tokens = db.query(user_models.RefreshToken).filter(
            user_models.RefreshToken.user_id == sample_user.id,
            user_models.RefreshToken.revoked_at != None
        ).all()
        assert len(old_tokens) > 0
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/auth/refresh",
            params={"refresh_token": "invalid_token_123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_refresh_token_expired(self, client, db, sample_user):
        """Test refresh with expired token"""
        # Create expired refresh token
        import secrets
        refresh_token_value = secrets.token_urlsafe(32)
        refresh_token_hash = bcrypt.hashpw(refresh_token_value.encode(), bcrypt.gensalt())
        
        expired_token = user_models.RefreshToken(
            user_id=sample_user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.add(expired_token)
        db.commit()
        
        response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token_value}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpoint:
    """Test cases for user logout"""
    
    def test_logout_success(self, client, db, sample_user):
        """Test successful logout"""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        access_token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "Logout successful" in response.json()["message"]
        
        # Verify all refresh tokens were revoked
        active_tokens = db.query(user_models.RefreshToken).filter(
            user_models.RefreshToken.user_id == sample_user.id,
            user_models.RefreshToken.revoked_at == None
        ).all()
        assert len(active_tokens) == 0
    
    def test_logout_without_auth(self, client):
        """Test logout without authentication"""
        response = client.post("/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRegisterDeviceEndpoint:
    """Test cases for PDV device registration"""
    
    def test_register_device_success(self, client, db, sample_store):
        """Test successful device registration"""
        # Create a device with registration code
        from app.models import business as business_models
        device = business_models.Device(
            id=uuid4(),
            store_id=sample_store.id,
            name="Test Device",
            registration_code="TEST123CODE",
            is_active=True
        )
        db.add(device)
        db.commit()
        
        response = client.post(
            "/auth/pdv/register-device",
            params={
                "store_id": str(sample_store.id),
                "registration_code": "TEST123CODE"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["device_id"] == str(device.id)
        assert data["store_id"] == str(sample_store.id)
        
        # Verify device was updated
        db.refresh(device)
        assert device.last_seen_at is not None
    
    def test_register_device_invalid_code(self, client, sample_store):
        """Test device registration with invalid code"""
        response = client.post(
            "/auth/pdv/register-device",
            params={
                "store_id": str(sample_store.id),
                "registration_code": "INVALID_CODE"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Invalid registration code" in response.json()["detail"]


class TestPasswordSecurity:
    """Test cases for password security"""
    
    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes"""
        password = "samepassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_password_verification(self):
        """Test password verification"""
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        password_hash = get_password_hash(password)
        
        assert verify_password(password, password_hash)
        assert not verify_password(wrong_password, password_hash)

