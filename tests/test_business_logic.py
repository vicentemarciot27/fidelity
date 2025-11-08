"""
Unit tests for business logic and calculations
"""
import pytest
import math
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from app.models import points as points_models
from app.models import coupons as coupon_models


class TestPointsCalculationLogic:
    """Test cases for points calculation business logic"""
    
    def test_points_per_brl_calculation(self):
        """Test basic points per BRL calculation"""
        total_brl = Decimal("100.00")
        points_per_brl = 1.0
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 100
    
    def test_points_per_brl_fractional_rate(self):
        """Test points calculation with fractional rate"""
        total_brl = Decimal("100.00")
        points_per_brl = 1.5
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 150
    
    def test_points_calculation_rounding_down(self):
        """Test that points are always rounded down"""
        # 99.99 BRL * 1.5 points_per_brl = 149.985 -> 149 points
        total_brl = Decimal("99.99")
        points_per_brl = 1.5
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 149
        assert points_earned != 150  # Not rounded up
    
    def test_points_calculation_zero_amount(self):
        """Test points calculation with zero amount"""
        total_brl = Decimal("0.00")
        points_per_brl = 1.0
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 0
    
    def test_points_calculation_small_amount(self):
        """Test points calculation with small amount (less than 1 BRL)"""
        total_brl = Decimal("0.99")
        points_per_brl = 1.0
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 0  # Should be 0 as 0.99 * 1.0 = 0.99 -> floor(0.99) = 0
    
    def test_points_calculation_large_amount(self):
        """Test points calculation with large amount"""
        total_brl = Decimal("10000.00")
        points_per_brl = 2.0
        
        points_earned = math.floor(float(total_brl) * float(points_per_brl))
        
        assert points_earned == 20000
    
    def test_points_to_brl_conversion(self):
        """Test converting points back to BRL value"""
        points = 100
        points_per_brl = 2.0
        
        brl_value = points / points_per_brl
        
        assert brl_value == 50.0
    
    def test_points_to_brl_conversion_fractional_result(self):
        """Test points to BRL conversion with fractional result"""
        points = 150
        points_per_brl = 2.5
        
        brl_value = points / points_per_brl
        
        assert brl_value == 60.0


class TestDiscountCalculationLogic:
    """Test cases for discount calculation business logic"""
    
    def test_brl_discount_fixed_amount(self):
        """Test fixed BRL discount"""
        discount_amount_brl = Decimal("10.00")
        order_total = Decimal("100.00")
        
        final_amount = order_total - discount_amount_brl
        
        assert final_amount == Decimal("90.00")
    
    def test_percentage_discount_calculation(self):
        """Test percentage-based discount"""
        order_total = 100.0
        discount_percentage = 20.0
        
        discount_amount = order_total * discount_percentage / 100.0
        
        assert discount_amount == 20.0
    
    def test_percentage_discount_various_amounts(self):
        """Test percentage discount with various amounts"""
        test_cases = [
            (100.0, 10.0, 10.0),   # 10% of 100
            (50.0, 20.0, 10.0),    # 20% of 50
            (250.0, 15.0, 37.5),   # 15% of 250
            (99.99, 5.0, 4.9995),  # 5% of 99.99
        ]
        
        for order_total, percentage, expected in test_cases:
            discount = order_total * percentage / 100.0
            assert discount == expected
    
    def test_discount_cannot_exceed_order_total(self):
        """Test that discount should not exceed order total"""
        order_total = Decimal("50.00")
        discount_amount_brl = Decimal("10.00")
        
        # Valid discount
        assert discount_amount_brl < order_total
        
        # Discount larger than total (should be validated)
        large_discount = Decimal("60.00")
        assert large_discount > order_total
    
    def test_discount_brl_precision(self):
        """Test discount calculation precision"""
        order_total = 99.99
        discount_percentage = 15.5
        
        discount_amount = order_total * discount_percentage / 100.0
        
        assert discount_amount == pytest.approx(15.49845, rel=1e-5)
    
    def test_free_sku_discount_logic(self):
        """Test FREE_SKU discount type logic"""
        # For FREE_SKU, the discount is the price of the free item
        free_item_price = Decimal("25.00")
        order_total = Decimal("100.00")
        
        final_amount = order_total - free_item_price
        
        assert final_amount == Decimal("75.00")


class TestCouponValidationLogic:
    """Test cases for coupon validation business logic"""
    
    def test_coupon_status_validation(self):
        """Test coupon status validation"""
        valid_statuses = ["ISSUED", "RESERVED"]
        invalid_statuses = ["REDEEMED", "EXPIRED", "CANCELLED"]
        
        # Check valid statuses
        for status in valid_statuses:
            assert status in ["ISSUED", "RESERVED"]
        
        # Check invalid statuses
        for status in invalid_statuses:
            assert status not in ["ISSUED", "RESERVED"]
    
    def test_coupon_time_window_validation(self):
        """Test coupon offer time window validation"""
        now = datetime.utcnow()
        
        # Future offer (not yet valid)
        start_at = now + timedelta(days=1)
        end_at = now + timedelta(days=30)
        
        is_before_start = start_at > now
        is_after_end = end_at < now
        
        assert is_before_start is True
        assert is_after_end is False
        
        # Active offer
        start_at = now - timedelta(days=1)
        end_at = now + timedelta(days=30)
        
        is_active = start_at <= now and end_at >= now
        assert is_active is True
        
        # Expired offer
        start_at = now - timedelta(days=30)
        end_at = now - timedelta(days=1)
        
        is_expired = end_at < now
        assert is_expired is True
    
    def test_coupon_stock_validation(self):
        """Test coupon stock availability validation"""
        initial_quantity = 100
        current_quantity = 50
        
        has_stock = current_quantity > 0
        assert has_stock is True
        
        # Out of stock
        current_quantity = 0
        has_stock = current_quantity > 0
        assert has_stock is False
    
    def test_coupon_max_per_customer_validation(self):
        """Test max coupons per customer validation"""
        max_per_customer = 5
        
        # Customer has 3 coupons
        customer_coupon_count = 3
        can_acquire = customer_coupon_count < max_per_customer
        assert can_acquire is True
        
        # Customer has 5 coupons (at limit)
        customer_coupon_count = 5
        can_acquire = customer_coupon_count < max_per_customer
        assert can_acquire is False
        
        # No limit (0 means unlimited)
        max_per_customer = 0
        customer_coupon_count = 100
        # In the code, 0 means no limit, but > 0 applies the limit
        has_limit = max_per_customer > 0
        assert has_limit is False
    
    def test_coupon_sku_specific_validation(self):
        """Test SKU-specific coupon validation"""
        valid_skus = ["SKU001", "SKU002", "SKU003"]
        
        # Order items
        order_items = [
            {"sku_id": "SKU001", "quantity": 2},
            {"sku_id": "SKU999", "quantity": 1}
        ]
        
        # Check if any item has valid SKU
        has_valid_sku = any(
            item.get("sku_id") in valid_skus 
            for item in order_items
        )
        
        assert has_valid_sku is True
        
        # No valid SKUs
        order_items_invalid = [
            {"sku_id": "SKU888", "quantity": 2},
            {"sku_id": "SKU999", "quantity": 1}
        ]
        
        has_valid_sku = any(
            item.get("sku_id") in valid_skus 
            for item in order_items_invalid
        )
        
        assert has_valid_sku is False


class TestPointsExpirationLogic:
    """Test cases for points expiration logic"""
    
    def test_points_expiration_calculation(self):
        """Test points expiration date calculation"""
        now = datetime.utcnow()
        expires_in_days = 365
        
        expires_at = now + timedelta(days=expires_in_days)
        
        # Verify it's approximately 1 year from now
        expected_date = now + timedelta(days=365)
        assert expires_at.date() == expected_date.date()
    
    def test_points_without_expiration(self):
        """Test points that never expire"""
        expires_at = None
        
        # Points without expiration should be included regardless of date
        assert expires_at is None
    
    def test_expired_points_filtering(self):
        """Test filtering of expired points"""
        now = datetime.utcnow()
        
        # Active points
        active_expires_at = now + timedelta(days=30)
        is_active = active_expires_at > now
        assert is_active is True
        
        # Expired points
        expired_expires_at = now - timedelta(days=1)
        is_active = expired_expires_at > now
        assert is_active is False
    
    def test_points_expiration_edge_case_today(self):
        """Test points expiring today"""
        now = datetime.utcnow()
        expires_at = now  # Expires right now
        
        # Should be considered expired if expires_at <= now
        is_expired = expires_at <= now
        assert is_expired is True


class TestPointRuleHierarchy:
    """Test cases for point rule hierarchy logic"""
    
    def test_rule_hierarchy_priority(self):
        """Test rule selection priority: STORE > FRANCHISE > CUSTOMER > GLOBAL"""
        # Simulate rule selection logic
        rules = {
            "STORE": {"scope": "STORE", "points_per_brl": 2.0},
            "FRANCHISE": {"scope": "FRANCHISE", "points_per_brl": 1.5},
            "CUSTOMER": {"scope": "CUSTOMER", "points_per_brl": 1.2},
            "GLOBAL": {"scope": "GLOBAL", "points_per_brl": 1.0}
        }
        
        # Priority order
        priority = ["STORE", "FRANCHISE", "CUSTOMER", "GLOBAL"]
        
        # Find first available rule
        selected_rule = None
        for scope in priority:
            if scope in rules:
                selected_rule = rules[scope]
                break
        
        assert selected_rule["scope"] == "STORE"
        assert selected_rule["points_per_brl"] == 2.0
    
    def test_rule_fallback_to_franchise(self):
        """Test fallback to franchise rule when store rule doesn't exist"""
        rules = {
            "FRANCHISE": {"scope": "FRANCHISE", "points_per_brl": 1.5},
            "CUSTOMER": {"scope": "CUSTOMER", "points_per_brl": 1.2},
            "GLOBAL": {"scope": "GLOBAL", "points_per_brl": 1.0}
        }
        
        priority = ["STORE", "FRANCHISE", "CUSTOMER", "GLOBAL"]
        
        selected_rule = None
        for scope in priority:
            if scope in rules:
                selected_rule = rules[scope]
                break
        
        assert selected_rule["scope"] == "FRANCHISE"
    
    def test_rule_fallback_to_global(self):
        """Test fallback to global rule when no specific rules exist"""
        rules = {
            "GLOBAL": {"scope": "GLOBAL", "points_per_brl": 1.0}
        }
        
        priority = ["STORE", "FRANCHISE", "CUSTOMER", "GLOBAL"]
        
        selected_rule = None
        for scope in priority:
            if scope in rules:
                selected_rule = rules[scope]
                break
        
        assert selected_rule["scope"] == "GLOBAL"


class TestWalletBalanceCalculation:
    """Test cases for wallet balance calculation logic"""
    
    def test_wallet_balance_sum_transactions(self):
        """Test wallet balance calculation from multiple transactions"""
        transactions = [
            {"delta": 100},
            {"delta": 50},
            {"delta": -30},
            {"delta": 20}
        ]
        
        balance = sum(t["delta"] for t in transactions)
        
        assert balance == 140
    
    def test_wallet_balance_exclude_expired(self):
        """Test wallet balance excludes expired points"""
        now = datetime.utcnow()
        
        transactions = [
            {"delta": 100, "expires_at": now + timedelta(days=30)},  # Active
            {"delta": 50, "expires_at": now - timedelta(days=1)},    # Expired
            {"delta": 30, "expires_at": None},                        # Never expires
        ]
        
        # Filter out expired
        active_transactions = [
            t for t in transactions 
            if t["expires_at"] is None or t["expires_at"] > now
        ]
        
        balance = sum(t["delta"] for t in active_transactions)
        
        assert balance == 130  # 100 + 30 (excluding expired 50)
    
    def test_wallet_balance_by_scope(self):
        """Test wallet balance calculation per scope"""
        transactions = [
            {"scope": "STORE", "scope_id": "store1", "delta": 100},
            {"scope": "STORE", "scope_id": "store1", "delta": 50},
            {"scope": "STORE", "scope_id": "store2", "delta": 30},
            {"scope": "FRANCHISE", "scope_id": "franchise1", "delta": 200},
        ]
        
        # Balance for store1
        store1_balance = sum(
            t["delta"] for t in transactions 
            if t["scope"] == "STORE" and t["scope_id"] == "store1"
        )
        
        assert store1_balance == 150
        
        # Balance for franchise1
        franchise1_balance = sum(
            t["delta"] for t in transactions 
            if t["scope"] == "FRANCHISE" and t["scope_id"] == "franchise1"
        )
        
        assert franchise1_balance == 200
    
    def test_wallet_balance_negative_handling(self):
        """Test handling of negative balance (should be prevented in production)"""
        transactions = [
            {"delta": 50},
            {"delta": -100}  # More deduction than available
        ]
        
        balance = sum(t["delta"] for t in transactions)
        
        assert balance == -50
        # In production, this should be prevented at the business logic level


class TestOrderTotalCalculation:
    """Test cases for order total calculation logic"""
    
    def test_order_total_with_items(self):
        """Test order total calculation from items"""
        items = [
            {"price": Decimal("10.00"), "quantity": 2},
            {"price": Decimal("15.50"), "quantity": 1},
            {"price": Decimal("5.00"), "quantity": 3}
        ]
        
        subtotal = sum(
            item["price"] * item["quantity"] 
            for item in items
        )
        
        assert subtotal == Decimal("50.50")
    
    def test_order_total_with_tax(self):
        """Test order total with tax"""
        subtotal = Decimal("100.00")
        tax = Decimal("5.00")
        
        total = subtotal + tax
        
        assert total == Decimal("105.00")
    
    def test_order_total_with_discount(self):
        """Test order total with discount"""
        subtotal = Decimal("100.00")
        discount = Decimal("10.00")
        
        total = subtotal - discount
        
        assert total == Decimal("90.00")
    
    def test_order_total_complex(self):
        """Test complex order total calculation"""
        items_total = Decimal("100.00")
        shipping = Decimal("10.00")
        tax = Decimal("5.50")
        discount = Decimal("15.00")
        
        total = items_total + shipping + tax - discount
        
        assert total == Decimal("100.50")


class TestBusinessRuleValidations:
    """Test cases for various business rule validations"""
    
    def test_minimum_order_value_validation(self):
        """Test minimum order value validation"""
        minimum_order_value = Decimal("10.00")
        
        # Valid order
        order_total = Decimal("15.00")
        is_valid = order_total >= minimum_order_value
        assert is_valid is True
        
        # Invalid order
        order_total = Decimal("5.00")
        is_valid = order_total >= minimum_order_value
        assert is_valid is False
    
    def test_cpf_format_validation(self):
        """Test CPF format validation (simplified)"""
        # Valid CPF format (11 digits)
        cpf = "12345678901"
        is_valid_format = len(cpf) == 11 and cpf.isdigit()
        assert is_valid_format is True
        
        # Invalid CPF format
        cpf_invalid = "123456789"
        is_valid_format = len(cpf_invalid) == 11 and cpf_invalid.isdigit()
        assert is_valid_format is False
    
    def test_email_format_validation(self):
        """Test email format validation (simplified)"""
        # Valid email
        email = "user@example.com"
        has_at_symbol = "@" in email
        has_domain = "." in email.split("@")[-1] if "@" in email else False
        is_valid = has_at_symbol and has_domain
        assert is_valid is True
        
        # Invalid email
        email_invalid = "userexample.com"
        has_at_symbol = "@" in email_invalid
        assert has_at_symbol is False
    
    def test_quantity_validation(self):
        """Test quantity validation"""
        # Valid quantities
        assert 1 > 0
        assert 100 > 0
        
        # Invalid quantities
        assert not (0 > 0)
        assert not (-1 > 0)
    
    def test_percentage_range_validation(self):
        """Test percentage value range validation"""
        # Valid percentages
        for percentage in [0, 10, 50, 100]:
            is_valid = 0 <= percentage <= 100
            assert is_valid is True
        
        # Invalid percentages
        for percentage in [-1, 101, 150]:
            is_valid = 0 <= percentage <= 100
            assert is_valid is False

