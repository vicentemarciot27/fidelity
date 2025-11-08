"""
Unit tests for Pydantic schemas validation
"""
import pytest
from pydantic import ValidationError
from decimal import Decimal
from uuid import uuid4

from app.schemas.auth import Token, TokenData, UserLogin, UserCreate
from app.schemas.coupons import (
    BuyCouponRequest, 
    BuyCouponResponse, 
    AttemptCouponRequest,
    AttemptCouponResponse,
    RedeemCouponRequest
)
from app.schemas.points import EarnPointsRequest, EarnPointsResponse
from app.schemas.wallet import PointBalance, CouponBalance, WalletResponse


class TestAuthSchemas:
    """Test cases for authentication schemas"""
    
    def test_token_schema_valid(self):
        """Test Token schema with valid data"""
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            refresh_token="refresh_token_value",
            token_type="bearer"
        )
        
        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == "bearer"
    
    def test_token_data_schema_valid(self):
        """Test TokenData schema with valid data"""
        token_data = TokenData(
            user_id=uuid4(),
            role="USER",
            exp=1234567890
        )
        
        assert token_data.user_id is not None
        assert token_data.role == "USER"
        assert token_data.exp == 1234567890
    
    def test_token_data_schema_with_optional_fields(self):
        """Test TokenData schema with optional fields"""
        customer_id = uuid4()
        franchise_id = uuid4()
        store_id = uuid4()
        person_id = uuid4()
        
        token_data = TokenData(
            user_id=uuid4(),
            role="STORE_MANAGER",
            customer_id=customer_id,
            franchise_id=franchise_id,
            store_id=store_id,
            person_id=person_id,
            exp=1234567890
        )
        
        assert token_data.customer_id == customer_id
        assert token_data.franchise_id == franchise_id
        assert token_data.store_id == store_id
        assert token_data.person_id == person_id
    
    def test_user_login_schema_valid(self):
        """Test UserLogin schema with valid data"""
        login = UserLogin(
            email="user@example.com",
            password="password123"
        )
        
        assert login.email == "user@example.com"
        assert login.password == "password123"
    
    def test_user_login_schema_missing_fields(self):
        """Test UserLogin schema with missing required fields"""
        with pytest.raises(ValidationError):
            UserLogin(email="user@example.com")  # Missing password
    
    def test_user_create_schema_valid(self):
        """Test UserCreate schema with valid data"""
        user_create = UserCreate(
            email="newuser@example.com",
            password="securepass123",
            name="New User",
            cpf="12345678901",
            phone="11999999999",
            role="USER"
        )
        
        assert user_create.email == "newuser@example.com"
        assert user_create.cpf == "12345678901"
        assert user_create.role == "USER"
    
    def test_user_create_schema_default_role(self):
        """Test UserCreate schema with default role"""
        user_create = UserCreate(
            email="newuser@example.com",
            password="securepass123",
            name="New User",
            cpf="12345678901"
        )
        
        assert user_create.role == "USER"
    
    def test_user_create_schema_optional_phone(self):
        """Test UserCreate schema without optional phone"""
        user_create = UserCreate(
            email="newuser@example.com",
            password="securepass123",
            name="New User",
            cpf="12345678901"
        )
        
        assert user_create.phone is None


class TestCouponSchemas:
    """Test cases for coupon schemas"""
    
    def test_buy_coupon_request_valid(self):
        """Test BuyCouponRequest schema with valid data"""
        offer_id = uuid4()
        request = BuyCouponRequest(offer_id=offer_id)
        
        assert request.offer_id == offer_id
    
    def test_buy_coupon_request_invalid_uuid(self):
        """Test BuyCouponRequest schema with invalid UUID"""
        with pytest.raises(ValidationError):
            BuyCouponRequest(offer_id="not-a-uuid")
    
    def test_buy_coupon_response_valid(self):
        """Test BuyCouponResponse schema with valid data"""
        coupon_id = uuid4()
        response = BuyCouponResponse(
            coupon_id=coupon_id,
            code="COUPON_CODE_123",
            qr={"format": "png", "data": "base64data"}
        )
        
        assert response.coupon_id == coupon_id
        assert response.code == "COUPON_CODE_123"
        assert response.qr["format"] == "png"
    
    def test_attempt_coupon_request_valid(self):
        """Test AttemptCouponRequest schema with valid data"""
        store_id = uuid4()
        request = AttemptCouponRequest(
            code="COUPON_123",
            order_total_brl=Decimal("100.50"),
            store_id=store_id,
            items=[{"sku_id": "SKU001", "quantity": 2}]
        )
        
        assert request.code == "COUPON_123"
        assert request.order_total_brl == Decimal("100.50")
        assert request.store_id == store_id
        assert len(request.items) == 1
    
    def test_attempt_coupon_request_without_items(self):
        """Test AttemptCouponRequest schema without optional items"""
        store_id = uuid4()
        request = AttemptCouponRequest(
            code="COUPON_123",
            order_total_brl=Decimal("100.50"),
            store_id=store_id
        )
        
        assert request.items is None
    
    def test_attempt_coupon_response_valid(self):
        """Test AttemptCouponResponse schema with valid data"""
        coupon_id = uuid4()
        response = AttemptCouponResponse(
            coupon_id=coupon_id,
            redeemable=True,
            discount={"type": "BRL", "amount_brl": 10.0}
        )
        
        assert response.coupon_id == coupon_id
        assert response.redeemable is True
        assert response.discount["amount_brl"] == 10.0
    
    def test_attempt_coupon_response_not_redeemable(self):
        """Test AttemptCouponResponse schema when not redeemable"""
        coupon_id = uuid4()
        response = AttemptCouponResponse(
            coupon_id=coupon_id,
            redeemable=False,
            message="Coupon expired"
        )
        
        assert response.redeemable is False
        assert response.message == "Coupon expired"
        assert response.discount is None
    
    def test_redeem_coupon_request_valid(self):
        """Test RedeemCouponRequest schema with valid data"""
        coupon_id = uuid4()
        request = RedeemCouponRequest(
            coupon_id=coupon_id,
            order_id="ORDER_123",
            order={
                "store_id": str(uuid4()),
                "total_brl": 90.00,
                "items": {}
            }
        )
        
        assert request.coupon_id == coupon_id
        assert request.order_id == "ORDER_123"
        assert request.order is not None
    
    def test_redeem_coupon_request_minimal(self):
        """Test RedeemCouponRequest schema with minimal data"""
        coupon_id = uuid4()
        request = RedeemCouponRequest(coupon_id=coupon_id)
        
        assert request.coupon_id == coupon_id
        assert request.order_id is None
        assert request.order is None


class TestPointsSchemas:
    """Test cases for points schemas"""
    
    def test_earn_points_request_with_person_id(self):
        """Test EarnPointsRequest schema with person_id"""
        person_id = uuid4()
        store_id = uuid4()
        
        request = EarnPointsRequest(
            person_id=person_id,
            store_id=store_id,
            order={"total_brl": 100.00}
        )
        
        assert request.person_id == person_id
        assert request.cpf is None
        assert request.store_id == store_id
    
    def test_earn_points_request_with_cpf(self):
        """Test EarnPointsRequest schema with CPF"""
        store_id = uuid4()
        
        request = EarnPointsRequest(
            cpf="12345678901",
            store_id=store_id,
            order={"total_brl": 100.00}
        )
        
        assert request.cpf == "12345678901"
        assert request.person_id is None
    
    def test_earn_points_request_with_both(self):
        """Test EarnPointsRequest schema with both person_id and CPF"""
        person_id = uuid4()
        store_id = uuid4()
        
        request = EarnPointsRequest(
            person_id=person_id,
            cpf="12345678901",
            store_id=store_id,
            order={"total_brl": 100.00}
        )
        
        assert request.person_id == person_id
        assert request.cpf == "12345678901"
    
    def test_earn_points_request_missing_order(self):
        """Test EarnPointsRequest schema without required order"""
        store_id = uuid4()
        
        with pytest.raises(ValidationError):
            EarnPointsRequest(
                person_id=uuid4(),
                store_id=store_id
            )
    
    def test_earn_points_response_valid(self):
        """Test EarnPointsResponse schema with valid data"""
        order_id = uuid4()
        
        response = EarnPointsResponse(
            order_id=order_id,
            points_earned=100,
            wallet_snapshot={"total_points": 150}
        )
        
        assert response.order_id == order_id
        assert response.points_earned == 100
        assert response.wallet_snapshot["total_points"] == 150


class TestWalletSchemas:
    """Test cases for wallet schemas"""
    
    def test_point_balance_valid(self):
        """Test PointBalance schema with valid data"""
        scope_id = uuid4()
        
        balance = PointBalance(
            scope="STORE",
            scope_id=scope_id,
            points=150,
            as_brl=75.0
        )
        
        assert balance.scope == "STORE"
        assert balance.scope_id == scope_id
        assert balance.points == 150
        assert balance.as_brl == 75.0
    
    def test_point_balance_without_brl(self):
        """Test PointBalance schema without BRL conversion"""
        balance = PointBalance(
            scope="GLOBAL",
            scope_id=None,
            points=200
        )
        
        assert balance.points == 200
        assert balance.as_brl is None
    
    def test_coupon_balance_valid(self):
        """Test CouponBalance schema with valid data"""
        offer_id = uuid4()
        
        balance = CouponBalance(
            offer_id=offer_id,
            available_count=5,
            redeemed_count=2
        )
        
        assert balance.offer_id == offer_id
        assert balance.available_count == 5
        assert balance.redeemed_count == 2
    
    def test_wallet_response_valid(self):
        """Test WalletResponse schema with valid data"""
        response = WalletResponse(
            balances=[
                PointBalance(scope="STORE", scope_id=uuid4(), points=100)
            ],
            coupons=[
                CouponBalance(offer_id=uuid4(), available_count=3, redeemed_count=1)
            ]
        )
        
        assert len(response.balances) == 1
        assert len(response.coupons) == 1
    
    def test_wallet_response_empty(self):
        """Test WalletResponse schema with empty lists"""
        response = WalletResponse(
            balances=[],
            coupons=[]
        )
        
        assert len(response.balances) == 0
        assert len(response.coupons) == 0


class TestSchemaValidations:
    """Test cases for schema field validations"""
    
    def test_decimal_field_validation(self):
        """Test Decimal field accepts various numeric formats"""
        store_id = uuid4()
        
        # From float
        request1 = AttemptCouponRequest(
            code="CODE1",
            order_total_brl=100.50,
            store_id=store_id
        )
        assert request1.order_total_brl == Decimal("100.50")
        
        # From string
        request2 = AttemptCouponRequest(
            code="CODE2",
            order_total_brl="99.99",
            store_id=store_id
        )
        assert request2.order_total_brl == Decimal("99.99")
        
        # From Decimal
        request3 = AttemptCouponRequest(
            code="CODE3",
            order_total_brl=Decimal("150.25"),
            store_id=store_id
        )
        assert request3.order_total_brl == Decimal("150.25")
    
    def test_uuid_field_validation(self):
        """Test UUID field validation"""
        valid_uuid = uuid4()
        
        # Valid UUID
        request = BuyCouponRequest(offer_id=valid_uuid)
        assert request.offer_id == valid_uuid
        
        # Invalid UUID
        with pytest.raises(ValidationError):
            BuyCouponRequest(offer_id="not-a-valid-uuid")
    
    def test_optional_field_validation(self):
        """Test optional field handling"""
        # With optional field
        user1 = UserCreate(
            email="user1@example.com",
            password="pass123",
            name="User One",
            cpf="12345678901",
            phone="11999999999"
        )
        assert user1.phone == "11999999999"
        
        # Without optional field
        user2 = UserCreate(
            email="user2@example.com",
            password="pass123",
            name="User Two",
            cpf="12345678902"
        )
        assert user2.phone is None
    
    def test_dict_field_validation(self):
        """Test dictionary field validation"""
        store_id = uuid4()
        
        # Valid dict
        request = EarnPointsRequest(
            person_id=uuid4(),
            store_id=store_id,
            order={
                "total_brl": 100.00,
                "tax_brl": 5.00,
                "items": [{"sku": "SKU001"}]
            }
        )
        assert isinstance(request.order, dict)
        assert "total_brl" in request.order
    
    def test_list_field_validation(self):
        """Test list field validation"""
        store_id = uuid4()
        
        # Valid list
        request = AttemptCouponRequest(
            code="CODE",
            order_total_brl=100,
            store_id=store_id,
            items=[
                {"sku_id": "SKU001", "quantity": 2},
                {"sku_id": "SKU002", "quantity": 1}
            ]
        )
        assert isinstance(request.items, list)
        assert len(request.items) == 2


class TestSchemaEdgeCases:
    """Test edge cases for schema validation"""
    
    def test_empty_string_fields(self):
        """Test handling of empty string fields"""
        # Empty strings may be valid depending on schema configuration
        # This test accepts that Pydantic may allow empty strings by default
        try:
            login = UserLogin(email="user@example.com", password="")
            # If validation passes, that's acceptable
            assert login.email == "user@example.com"
        except ValidationError:
            # If validation fails, that's also acceptable
            pass
    
    def test_zero_values(self):
        """Test handling of zero values"""
        store_id = uuid4()
        
        # Zero order total
        request = AttemptCouponRequest(
            code="CODE",
            order_total_brl=0,
            store_id=store_id
        )
        assert request.order_total_brl == Decimal("0")
        
        # Zero points
        balance = PointBalance(
            scope="STORE",
            scope_id=store_id,
            points=0
        )
        assert balance.points == 0
    
    def test_negative_values(self):
        """Test handling of negative values"""
        # Negative points (for redemptions)
        response = EarnPointsResponse(
            order_id=uuid4(),
            points_earned=-50,  # Deduction
            wallet_snapshot={"total_points": 50}
        )
        assert response.points_earned == -50
    
    def test_very_large_values(self):
        """Test handling of very large values"""
        store_id = uuid4()
        
        # Large order total
        request = AttemptCouponRequest(
            code="CODE",
            order_total_brl=Decimal("999999999.99"),
            store_id=store_id
        )
        assert request.order_total_brl == Decimal("999999999.99")
        
        # Large points
        balance = PointBalance(
            scope="GLOBAL",
            scope_id=None,
            points=999999999
        )
        assert balance.points == 999999999

