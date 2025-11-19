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

print("✅ Banco de teste inicializado com sucesso!")


def seed_complete_test_data():
    """Create comprehensive test data for all tables"""
    session = Session()
    try:
        # Check if data already exists
        existing_user = session.query(user.AppUser).filter(user.AppUser.email == "test@email.com").first()
        if existing_user:
            print("ℹ️  Dados de teste já existem, nenhum dado novo criado.")
            return

        print("\n🌱 Iniciando seed de dados de teste completos...\n")

        # ============================================
        # 1. PERSON & APP USER (Admin and regular user)
        # ============================================
        print("👤 Criando Person e AppUser...")
        person = user.Person(
            cpf="00000000000",
            name="Test Admin User",
            phone="11999999999",
            location={"city": "São Paulo", "state": "SP"}
        )
        session.add(person)
        session.flush()

        test_user = user.AppUser(
            person_id=person.id,
            email="test@email.com",
            password_hash=get_password_hash("test123"),
            role="ADMIN",  # Admin role for full access
            is_active=True
        )
        session.add(test_user)
        session.flush()
        print(f"  ✓ User criado: test@email.com / test123 (Role: ADMIN)")

        # Regular user (non-admin)
        person_regular = user.Person(
            cpf="11111111111",
            name="Test Regular User",
            phone="11988888888",
            location={"city": "São Paulo", "state": "SP"}
        )
        session.add(person_regular)
        session.flush()

        test_regular_user = user.AppUser(
            person_id=person_regular.id,
            email="test-user@email.com",
            password_hash=get_password_hash("test123"),
            role="USER",  # Regular user role
            is_active=True
        )
        session.add(test_regular_user)
        session.flush()
        print(f"  ✓ User criado: test-user@email.com / test123 (Role: USER)")

        # ============================================
        # 2. BUSINESS STRUCTURE (Customer -> Franchise -> Store)
        # ============================================
        print("\n🏢 Criando estrutura de negócio...")
        
        # Customer
        customer = business.Customer(
            cnpj="12345678000100",
            name="Acme Corporation",
            contact_email="contact@acme.com",
            phone="1133334444"
        )
        session.add(customer)
        session.flush()
        print(f"  ✓ Customer criado: {customer.name}")

        # Franchise
        franchise = business.Franchise(
            customer_id=customer.id,
            cnpj="12345678000101",
            name="Acme São Paulo"
        )
        session.add(franchise)
        session.flush()
        print(f"  ✓ Franchise criada: {franchise.name}")

        # Store
        store = business.Store(
            franchise_id=franchise.id,
            cnpj="12345678000102",
            name="Acme Loja Paulista",
            location={"address": "Av. Paulista, 1000", "city": "São Paulo", "state": "SP"}
        )
        session.add(store)
        session.flush()
        print(f"  ✓ Store criada: {store.name}")

        # Device (PDV)
        device = business.Device(
            store_id=store.id,
            name="PDV-001",
            registration_code="PDV001CODE",
            is_active=True
        )
        session.add(device)
        print(f"  ✓ Device criado: {device.name}")

        # StoreStaff - Link user to store as manager
        store_staff = user.StoreStaff(
            user_id=test_user.id,
            store_id=store.id,
            role="STORE_MANAGER"
        )
        session.add(store_staff)
        print(f"  ✓ StoreStaff criado: User vinculado à loja como STORE_MANAGER")

        # ============================================
        # 3. CUSTOMER MARKETPLACE RULES
        # ============================================
        print("\n⚙️  Criando regras de marketplace...")
        marketplace_rules = config.CustomerMarketplaceRules(
            customer_id=customer.id,
            rules={
                "allow_external_offers": True,
                "max_discount_percentage": 50,
                "features": ["points", "coupons", "marketplace"]
            }
        )
        session.add(marketplace_rules)
        print(f"  ✓ Marketplace rules criadas para {customer.name}")

        # ============================================
        # 4. POINT RULES (All scopes)
        # ============================================
        print("\n🎯 Criando regras de pontos...")
        
        # Global rule
        global_rule = points.PointRules(
            scope="GLOBAL",
            points_per_brl=1.0,
            expires_in_days=365
        )
        session.add(global_rule)
        print("  ✓ Regra GLOBAL: 1.0 pontos/BRL, expira em 365 dias")

        # Customer rule
        customer_rule = points.PointRules(
            scope="CUSTOMER",
            customer_id=customer.id,
            points_per_brl=1.5,
            expires_in_days=365
        )
        session.add(customer_rule)
        print("  ✓ Regra CUSTOMER: 1.5 pontos/BRL, expira em 365 dias")

        # Franchise rule
        franchise_rule = points.PointRules(
            scope="FRANCHISE",
            franchise_id=franchise.id,
            points_per_brl=2.0,
            expires_in_days=180
        )
        session.add(franchise_rule)
        print("  ✓ Regra FRANCHISE: 2.0 pontos/BRL, expira em 180 dias")

        # Store rule (highest priority)
        store_rule = points.PointRules(
            scope="STORE",
            store_id=store.id,
            points_per_brl=2.5,
            expires_in_days=180
        )
        session.add(store_rule)
        print("  ✓ Regra STORE: 2.5 pontos/BRL, expira em 180 dias")

        # ============================================
        # 5. CATEGORIES & SKUs
        # ============================================
        print("\n📦 Criando categorias e SKUs...")
        
        category_food = orders.Category(name="Alimentos")
        category_drinks = orders.Category(name="Bebidas")
        session.add_all([category_food, category_drinks])
        session.flush()

        sku1 = orders.SKU(
            customer_id=customer.id,
            name="Pizza Margherita",
            brand="Acme Pizza",
            category_id=category_food.id,
            custom_metadata={"price": 45.90, "size": "Grande"}
        )
        sku2 = orders.SKU(
            customer_id=customer.id,
            name="Coca-Cola 2L",
            brand="Coca-Cola",
            category_id=category_drinks.id,
            custom_metadata={"price": 8.50, "volume": "2L"}
        )
        sku3 = orders.SKU(
            customer_id=customer.id,
            name="Hamburguer Especial",
            brand="Acme Burger",
            category_id=category_food.id,
            custom_metadata={"price": 32.00}
        )
        session.add_all([sku1, sku2, sku3])
        session.flush()
        print(f"  ✓ {session.query(orders.Category).count()} categorias criadas")
        print(f"  ✓ {session.query(orders.SKU).count()} SKUs criados")

        # ============================================
        # 6. COUPON TYPES
        # ============================================
        print("\n🎫 Criando tipos de cupom...")
        
        # BRL discount type
        coupon_type_brl = coupons.CouponType(
            sku_specific=False,
            redeem_type="BRL",
            discount_amount_brl=Decimal("10.00")
        )
        session.add(coupon_type_brl)
        print("  ✓ Tipo BRL: R$ 10,00 de desconto")

        # Percentage discount type
        coupon_type_percentage = coupons.CouponType(
            sku_specific=False,
            redeem_type="PERCENTAGE",
            discount_amount_percentage=Decimal("15.00")
        )
        session.add(coupon_type_percentage)
        print("  ✓ Tipo PERCENTAGE: 15% de desconto")

        # Free SKU type
        coupon_type_free_sku = coupons.CouponType(
            sku_specific=True,
            redeem_type="FREE_SKU",
            valid_skus=[str(sku2.id)]  # Free Coca-Cola
        )
        session.add(coupon_type_free_sku)
        print("  ✓ Tipo FREE_SKU: Coca-Cola grátis")

        session.flush()

        # ============================================
        # 7. COUPON OFFERS
        # ============================================
        print("\n🎁 Criando ofertas de cupom...")
        
        now = datetime.now(timezone.utc)
        
        # Customer-level offer (BRL discount)
        offer_customer = coupons.CouponOffer(
            entity_scope="CUSTOMER",
            entity_id=customer.id,
            coupon_type_id=coupon_type_brl.id,
            initial_quantity=100,
            current_quantity=95,
            max_per_customer=5,
            points_cost=40,
            is_active=True,
            start_at=now - timedelta(days=7),
            end_at=now + timedelta(days=30)
        )
        session.add(offer_customer)
        print("  ✓ Oferta CUSTOMER: Desconto R$ 10,00")

        # Franchise-level offer (Percentage discount)
        offer_franchise = coupons.CouponOffer(
            entity_scope="FRANCHISE",
            entity_id=franchise.id,
            coupon_type_id=coupon_type_percentage.id,
            initial_quantity=50,
            current_quantity=45,
            max_per_customer=3,
            points_cost=50,
            is_active=True,
            start_at=now - timedelta(days=3),
            end_at=now + timedelta(days=60)
        )
        session.add(offer_franchise)
        print("  ✓ Oferta FRANCHISE: Desconto 15%")

        # Store-level offer (Free SKU)
        offer_store = coupons.CouponOffer(
            entity_scope="STORE",
            entity_id=store.id,
            coupon_type_id=coupon_type_free_sku.id,
            initial_quantity=30,
            current_quantity=28,
            max_per_customer=2,
            points_cost=30,
            is_active=True,
            start_at=now,
            end_at=now + timedelta(days=15)
        )
        session.add(offer_store)
        print("  ✓ Oferta STORE: Coca-Cola grátis")

        session.flush()

        # ============================================
        # 8. OFFER ASSETS
        # ============================================
        print("\n🖼️  Criando assets para ofertas...")
        
        asset1 = coupons.OfferAsset(
            offer_id=offer_customer.id,
            kind="BANNER",
            url="https://example.com/banners/discount-10-brl.jpg",
            position=1
        )
        asset2 = coupons.OfferAsset(
            offer_id=offer_customer.id,
            kind="THUMB",
            url="https://example.com/thumbs/discount-10-brl.jpg",
            position=2
        )
        asset3 = coupons.OfferAsset(
            offer_id=offer_franchise.id,
            kind="BANNER",
            url="https://example.com/banners/discount-15-percent.jpg",
            position=1
        )
        session.add_all([asset1, asset2, asset3])
        print(f"  ✓ {3} assets criados")

        # ============================================
        # 9. COUPONS (Issued to user)
        # ============================================
        print("\n🎟️  Criando cupons emitidos...")
        
        # Issued coupon (available)
        code1 = "TESTCOUPON001"
        code1_hash = hashlib.sha256(code1.encode()).digest()
        coupon1 = coupons.Coupon(
            offer_id=offer_customer.id,
            issued_to_person_id=person.id,
            code_hash=code1_hash,
            status="ISSUED"
        )
        session.add(coupon1)
        print(f"  ✓ Cupom ISSUED criado: {code1}")

        # Reserved coupon
        code2 = "TESTCOUPON002"
        code2_hash = hashlib.sha256(code2.encode()).digest()
        coupon2 = coupons.Coupon(
            offer_id=offer_franchise.id,
            issued_to_person_id=person.id,
            code_hash=code2_hash,
            status="RESERVED"
        )
        session.add(coupon2)
        print(f"  ✓ Cupom RESERVED criado: {code2}")

        # Redeemed coupon (already used)
        code3 = "TESTCOUPON003"
        code3_hash = hashlib.sha256(code3.encode()).digest()
        coupon3 = coupons.Coupon(
            offer_id=offer_store.id,
            issued_to_person_id=person.id,
            code_hash=code3_hash,
            status="REDEEMED",
            redeemed_at=now - timedelta(days=2),
            redeemed_store_id=store.id
        )
        session.add(coupon3)
        print(f"  ✓ Cupom REDEEMED criado: {code3}")

        session.flush()

        # ============================================
        # 10. ORDERS
        # ============================================
        print("\n🛒 Criando pedidos...")
        
        # Order 1 - With coupon redemption
        order1 = orders.Order(
            store_id=store.id,
            person_id=person.id,
            total_brl=Decimal("85.00"),
            tax_brl=Decimal("5.00"),
            items={
                "items": [
                    {"sku_id": str(sku1.id), "name": "Pizza Margherita", "quantity": 1, "price": 45.90},
                    {"sku_id": str(sku2.id), "name": "Coca-Cola 2L", "quantity": 2, "price": 8.50}
                ]
            },
            source="PDV",
            external_id="ORDER001"
        )
        session.add(order1)
        print("  ✓ Pedido 1: R$ 85,00 (PDV)")

        # Order 2 - Regular order
        order2 = orders.Order(
            store_id=store.id,
            person_id=person.id,
            total_brl=Decimal("150.00"),
            tax_brl=Decimal("10.00"),
            items={
                "items": [
                    {"sku_id": str(sku1.id), "name": "Pizza Margherita", "quantity": 2, "price": 45.90},
                    {"sku_id": str(sku3.id), "name": "Hamburguer Especial", "quantity": 2, "price": 32.00}
                ]
            },
            source="PDV",
            external_id="ORDER002"
        )
        session.add(order2)
        print("  ✓ Pedido 2: R$ 150,00 (PDV)")

        # Order 3 - Marketplace order
        order3 = orders.Order(
            store_id=store.id,
            person_id=person.id,
            total_brl=Decimal("54.40"),
            tax_brl=Decimal("4.40"),
            items={
                "items": [
                    {"sku_id": str(sku1.id), "name": "Pizza Margherita", "quantity": 1, "price": 45.90},
                    {"sku_id": str(sku2.id), "name": "Coca-Cola 2L", "quantity": 1, "price": 8.50}
                ]
            },
            source="MARKETPLACE",
            checkout_ref="CHECKOUT123"
        )
        session.add(order3)
        print("  ✓ Pedido 3: R$ 54,40 (MARKETPLACE)")

        session.flush()

        # ============================================
        # 11. POINT TRANSACTIONS
        # ============================================
        print("\n⭐ Criando transações de pontos...")
        
        # Transaction 1 - Earned from order 1
        transaction1 = points.PointTransaction(
            person_id=person.id,
            scope="STORE",
            scope_id=store.id,
            store_id=store.id,
            order_id=str(order1.id),
            delta=212,  # 85 * 2.5 (store rule)
            details={"order_total": 85.00, "points_per_brl": 2.5},
            expires_at=now + timedelta(days=180)
        )
        session.add(transaction1)
        print("  ✓ Transação +212 pontos (Order 1)")

        # Transaction 2 - Earned from order 2
        transaction2 = points.PointTransaction(
            person_id=person.id,
            scope="STORE",
            scope_id=store.id,
            store_id=store.id,
            order_id=str(order2.id),
            delta=375,  # 150 * 2.5
            details={"order_total": 150.00, "points_per_brl": 2.5},
            expires_at=now + timedelta(days=180)
        )
        session.add(transaction2)
        print("  ✓ Transação +375 pontos (Order 2)")

        # Transaction 3 - Bonus points
        transaction3 = points.PointTransaction(
            person_id=person.id,
            scope="CUSTOMER",
            scope_id=customer.id,
            delta=10000,
            details={"reason": "welcome_bonus", "campaign": "new_user_2024"},
            expires_at=now + timedelta(days=365)
        )
        session.add(transaction3)
        print("  ✓ Transação +10000 pontos (Bônus de boas-vindas)")

        # Transaction 4 - Points redemption (negative)
        transaction4 = points.PointTransaction(
            person_id=person.id,
            scope="STORE",
            scope_id=store.id,
            store_id=store.id,
            delta=-50,
            details={"reason": "redemption", "redeemed_for": "discount"},
            expires_at=now + timedelta(days=180)
        )
        session.add(transaction4)
        print("  ✓ Transação -50 pontos (Resgate)")

        # Transaction 5 - Franchise-level points
        transaction5 = points.PointTransaction(
            person_id=person.id,
            scope="FRANCHISE",
            scope_id=franchise.id,
            delta=200,
            details={"reason": "franchise_campaign", "campaign": "summer_2024"},
            expires_at=now + timedelta(days=180)
        )
        session.add(transaction5)
        print("  ✓ Transação +200 pontos (Campanha franquia)")

        # ============================================
        # 12. DATA FOR REGULAR USER (test-user@email.com)
        # ============================================
        print("\n👤 Criando dados para usuário regular...")
        
        # Order for regular user
        order_regular = orders.Order(
            store_id=store.id,
            person_id=person_regular.id,
            total_brl=Decimal("100.00"),
            tax_brl=Decimal("8.00"),
            items={
                "items": [
                    {"sku_id": str(sku1.id), "name": "Pizza Margherita", "quantity": 2, "price": 45.90}
                ]
            },
            source="PDV",
            external_id="ORDER_REGULAR_001"
        )
        session.add(order_regular)
        print("  ✓ Pedido: R$ 100,00 (PDV)")

        # Points for regular user - from order
        transaction_regular1 = points.PointTransaction(
            person_id=person_regular.id,
            scope="STORE",
            scope_id=store.id,
            store_id=store.id,
            order_id=str(order_regular.id),
            delta=250,  # 100 * 2.5 (store rule)
            details={"order_total": 100.00, "points_per_brl": 2.5},
            expires_at=now + timedelta(days=180)
        )
        session.add(transaction_regular1)
        print("  ✓ Transação +250 pontos (Pedido)")

        # Welcome bonus for regular user
        transaction_regular2 = points.PointTransaction(
            person_id=person_regular.id,
            scope="CUSTOMER",
            scope_id=customer.id,
            delta=5000,
            details={"reason": "welcome_bonus", "campaign": "new_user_2024"},
            expires_at=now + timedelta(days=365)
        )
        session.add(transaction_regular2)
        print("  ✓ Transação +5000 pontos (Bônus de boas-vindas)")

        # Coupons for regular user
        code_regular1 = "REGULARUSER001"
        code_regular1_hash = hashlib.sha256(code_regular1.encode()).digest()
        coupon_regular1 = coupons.Coupon(
            offer_id=offer_customer.id,
            issued_to_person_id=person_regular.id,
            code_hash=code_regular1_hash,
            status="ISSUED"
        )
        session.add(coupon_regular1)
        print(f"  ✓ Cupom ISSUED: {code_regular1}")

        code_regular2 = "REGULARUSER002"
        code_regular2_hash = hashlib.sha256(code_regular2.encode()).digest()
        coupon_regular2 = coupons.Coupon(
            offer_id=offer_franchise.id,
            issued_to_person_id=person_regular.id,
            code_hash=code_regular2_hash,
            status="ISSUED"
        )
        session.add(coupon_regular2)
        print(f"  ✓ Cupom ISSUED: {code_regular2}")

        session.flush()

        # Commit all changes
        session.commit()
        
        # ============================================
        # SUMMARY
        # ============================================
        print("\n" + "="*60)
        print("✅ SEED COMPLETO - RESUMO DOS DADOS CRIADOS:")
        print("="*60)
        print(f"👤 Person Admin: {person.name} (CPF: {person.cpf})")
        print(f"👤 Person Regular: {person_regular.name} (CPF: {person_regular.cpf})")
        print(f"🔐 AppUser Admin: {test_user.email} / test123 (Role: {test_user.role})")
        print(f"🔐 AppUser Regular: {test_regular_user.email} / test123 (Role: {test_regular_user.role})")
        print(f"🏢 Customer: {customer.name}")
        print(f"🏪 Franchise: {franchise.name}")
        print(f"🏬 Store: {store.name}")
        print(f"💻 Device: {device.name}")
        print(f"👔 StoreStaff: User vinculado como STORE_MANAGER")
        print(f"🎯 Point Rules: 4 regras (GLOBAL, CUSTOMER, FRANCHISE, STORE)")
        print(f"📦 Categories: 2 categorias")
        print(f"🛍️  SKUs: 3 produtos")
        print(f"🎫 Coupon Types: 3 tipos (BRL, PERCENTAGE, FREE_SKU)")
        print(f"🎁 Coupon Offers: 3 ofertas ativas")
        print(f"🖼️  Offer Assets: 3 imagens")
        print(f"🎟️  Coupons Admin: 3 cupons (1 ISSUED, 1 RESERVED, 1 REDEEMED)")
        print(f"   - {code1} (ISSUED)")
        print(f"   - {code2} (RESERVED)")
        print(f"   - {code3} (REDEEMED)")
        print(f"🎟️  Coupons Regular: 2 cupons (ISSUED)")
        print(f"   - {code_regular1} (ISSUED)")
        print(f"   - {code_regular2} (ISSUED)")
        print(f"🛒 Orders Admin: 3 pedidos (R$ 289,40 total)")
        print(f"🛒 Orders Regular: 1 pedido (R$ 100,00 total)")
        print(f"⭐ Point Transactions Admin: 5 transações")
        print(f"   - Saldo atual: {212 + 375 + 10000 - 50 + 200} pontos")
        print(f"⭐ Point Transactions Regular: 2 transações")
        print(f"   - Saldo atual: {250 + 5000} pontos")
        print("="*60)
        print("\n🎉 Dados de teste criados com sucesso!\n")
        
    except Exception as exc:
        session.rollback()
        print(f"\n❌ Erro ao criar dados de teste: {exc}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


seed_complete_test_data()