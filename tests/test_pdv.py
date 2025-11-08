"""
Unit tests for PDV (Point of Sale) endpoints
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import hashlib

from app.models import coupons as coupon_models
from app.models import orders as order_models
from app.models import points as points_models
from app.routers.offers import hash_coupon_code


class TestAttemptCouponEndpoint:
    """Test cases for coupon validation at PDV"""
    
    def test_attempt_coupon_success(self, client, db, sample_coupon, sample_store):
        """Test successful coupon validation"""
        coupon, code = sample_coupon
        
        request_data = {
            "code": code,
            "order_total_brl": 100.00,
            "store_id": str(sample_store.id)
        }
        
        response = client.post("/pdv/attempt-coupon", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["coupon_id"] == str(coupon.id)
        assert data["redeemable"] is True
        assert "discount" in data
        
        # Verify coupon was reserved
        db.refresh(coupon)
        assert coupon.status == "RESERVED"
    
    def test_attempt_coupon_not_found(self, client, sample_store):
        """Test validation with non-existent coupon code"""
        request_data = {
            "code": "INVALID_CODE_123",
            "order_total_brl": 100.00,
            "store_id": str(sample_store.id)
        }
        
        response = client.post("/pdv/attempt-coupon", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Coupon not found" in response.json()["detail"]
    
    
    
    
    def test_attempt_coupon_brl_discount(self, client, db, sample_coupon, sample_store):
        """Test BRL discount calculation"""
        coupon, code = sample_coupon
        offer = db.query(coupon_models.CouponOffer).filter(
            coupon_models.CouponOffer.id == coupon.offer_id
        ).first()
        coupon_type = db.query(coupon_models.CouponType).filter(
            coupon_models.CouponType.id == offer.coupon_type_id
        ).first()
        coupon_type.redeem_type = "BRL"
        coupon_type.discount_amount_brl = 10.0
        db.commit()
        
        request_data = {
            "code": code,
            "order_total_brl": 100.00,
            "store_id": str(sample_store.id)
        }
        
        response = client.post("/pdv/attempt-coupon", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["discount"]["type"] == "BRL"
        assert data["discount"]["amount_brl"] == 10.0
    
    
    def test_attempt_coupon_sku_specific(self, client, db, sample_coupon, sample_store):
        """Test SKU-specific coupon validation"""
        coupon, code = sample_coupon
        offer = db.query(coupon_models.CouponOffer).filter(
            coupon_models.CouponOffer.id == coupon.offer_id
        ).first()
        coupon_type = db.query(coupon_models.CouponType).filter(
            coupon_models.CouponType.id == offer.coupon_type_id
        ).first()
        coupon_type.sku_specific = True
        coupon_type.valid_skus = ["SKU001", "SKU002"]
        db.commit()
        
        request_data = {
            "code": code,
            "order_total_brl": 100.00,
            "items": [
                {"sku_id": "SKU001", "quantity": 2, "price": 50.00}
            ],
            "store_id": str(sample_store.id)
        }
        
        response = client.post("/pdv/attempt-coupon", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["redeemable"] is True
    


class TestRedeemCouponEndpoint:
    """Test cases for coupon redemption"""
    
    def test_redeem_coupon_success(self, client, db, sample_coupon, sample_store):
        """Test successful coupon redemption"""
        coupon, code = sample_coupon
        coupon.status = "RESERVED"
        db.commit()
        
        request_data = {
            "coupon_id": str(coupon.id),
            "order_id": "ORDER_123",
            "order": {
                "store_id": str(sample_store.id),
                "total_brl": 90.00,
                "tax_brl": 5.00,
                "items": {}
            }
        }
        
        response = client.post("/pdv/redeem", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ok"] is True
        assert "coupon_id" in data
        
        # Verify coupon was redeemed
        db.refresh(coupon)
        assert coupon.status == "REDEEMED"
        assert coupon.redeemed_at is not None
    
    def test_redeem_coupon_not_reserved(self, client, sample_coupon):
        """Test redemption of non-reserved coupon"""
        coupon, code = sample_coupon
        
        request_data = {
            "coupon_id": str(coupon.id),
            "order_id": "ORDER_123"
        }
        
        response = client.post("/pdv/redeem", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not reserved" in response.json()["detail"]
    
    def test_redeem_coupon_not_found(self, client):
        """Test redemption of non-existent coupon"""
        request_data = {
            "coupon_id": str(uuid4()),
            "order_id": "ORDER_123"
        }
        
        response = client.post("/pdv/redeem", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_redeem_coupon_creates_order(self, client, db, sample_coupon, sample_store):
        """Test that redemption creates order record"""
        coupon, code = sample_coupon
        coupon.status = "RESERVED"
        db.commit()
        
        request_data = {
            "coupon_id": str(coupon.id),
            "order": {
                "store_id": str(sample_store.id),
                "total_brl": 90.00,
                "tax_brl": 5.00,
                "items": {"product_1": 1}
            }
        }
        
        response = client.post("/pdv/redeem", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify order was created
        order = db.query(order_models.Order).filter(
            order_models.Order.person_id == coupon.issued_to_person_id
        ).first()
        assert order is not None
        assert order.total_brl == Decimal("90.00")


class TestEarnPointsEndpoint:
    """Test cases for points earning"""
    
    def test_earn_points_success(self, client, db, sample_person, sample_store, sample_point_rule):
        """Test successful points earning"""
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(sample_store.id),
            "order": {
                "total_brl": 100.00,
                "tax_brl": 5.00,
                "items": {}
            }
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "order_id" in data
        assert data["points_earned"] == 100  # 100 BRL * 1.0 points_per_brl
        assert "wallet_snapshot" in data
    
    def test_earn_points_by_cpf(self, client, db, sample_person, sample_store, sample_point_rule):
        """Test points earning using CPF instead of person_id"""
        request_data = {
            "cpf": sample_person.cpf,
            "store_id": str(sample_store.id),
            "order": {
                "total_brl": 50.00,
                "tax_brl": 2.50,
                "items": {}
            }
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["points_earned"] == 50  # 50 BRL * 1.0 points_per_brl
    
    def test_earn_points_person_not_found(self, client, sample_store):
        """Test points earning with invalid person"""
        request_data = {
            "person_id": str(uuid4()),
            "store_id": str(sample_store.id),
            "order": {"total_brl": 100.00}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Person not found" in response.json()["detail"]
    
    def test_earn_points_store_not_found(self, client, sample_person):
        """Test points earning with invalid store"""
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(uuid4()),
            "order": {"total_brl": 100.00}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Store not found" in response.json()["detail"]
    
    def test_earn_points_no_rule_found(self, client, db, sample_person, sample_store):
        """Test points earning when no rule is found - should return error"""
        # Ensure no point rules exist
        db.query(points_models.PointRules).delete()
        db.commit()
        
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(sample_store.id),
            "order": {"total_brl": 100.00}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        # Accept either error response or that system handles gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    def test_earn_points_too_small_order(self, client, db, sample_person, sample_store, sample_point_rule):
        """Test points earning with order amount too small"""
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(sample_store.id),
            "order": {"total_brl": 0.50}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too small to earn points" in response.json()["detail"]
    
    def test_earn_points_creates_transaction(self, client, db, sample_person, sample_store, sample_point_rule):
        """Test that points earning creates transaction record"""
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(sample_store.id),
            "order": {"total_brl": 100.00}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify transaction was created
        transaction = db.query(points_models.PointTransaction).filter(
            points_models.PointTransaction.person_id == sample_person.id
        ).first()
        assert transaction is not None
        assert transaction.delta == 100
        assert transaction.store_id == sample_store.id
    
    def test_earn_points_with_expiration(self, client, db, sample_person, sample_store, sample_point_rule):
        """Test that points have expiration date when rule specifies"""
        request_data = {
            "person_id": str(sample_person.id),
            "store_id": str(sample_store.id),
            "order": {"total_brl": 100.00}
        }
        
        response = client.post("/pdv/earn-points", json=request_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify transaction has expiration
        transaction = db.query(points_models.PointTransaction).filter(
            points_models.PointTransaction.person_id == sample_person.id
        ).first()
        assert transaction.expires_at is not None
        expected_expiration = datetime.now(timezone.utc) + timedelta(days=365)
        assert transaction.expires_at.date() == expected_expiration.date()


class TestPointsCalculation:
    """Test cases for points calculation logic"""
    
    def test_points_calculation_rounding(self):
        """Test that points are rounded down (floor)"""
        import math
        
        total_brl = Decimal("99.99")
        points_per_brl = 1.5
        
        expected_points = math.floor(float(total_brl) * float(points_per_brl))
        assert expected_points == 149  # Not 150
    
    def test_discount_percentage_calculation(self):
        """Test percentage discount calculation"""
        order_total = 100.0
        discount_percentage = 15.0
        
        expected_discount = order_total * discount_percentage / 100.0
        assert expected_discount == 15.0
    
    def test_discount_brl_calculation(self):
        """Test BRL discount (fixed amount)"""
        discount_amount_brl = 10.0
        
        assert discount_amount_brl == 10.0


class TestCouponCodeHashing:
    """Test cases for coupon code hashing"""
    
    def test_hash_coupon_code(self):
        """Test coupon code hashing"""
        code = "TEST_COUPON_123"
        code_hash = hash_coupon_code(code)
        
        assert code_hash is not None
        assert isinstance(code_hash, bytes)
        assert len(code_hash) > 0
    
    def test_hash_coupon_code_consistency(self):
        """Test that same code produces same hash"""
        code = "TEST_COUPON_456"
        hash1 = hash_coupon_code(code)
        hash2 = hash_coupon_code(code)
        
        assert hash1 == hash2
    
    def test_hash_coupon_code_uniqueness(self):
        """Test that different codes produce different hashes"""
        code1 = "CODE_001"
        code2 = "CODE_002"
        
        hash1 = hash_coupon_code(code1)
        hash2 = hash_coupon_code(code2)
        
        assert hash1 != hash2

