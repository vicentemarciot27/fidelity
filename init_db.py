"""
Script para inicializar banco com dados de exemplo
"""
import os
import subprocess
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Carregar variáveis de ambiente
load_dotenv()

# Imports dos modelos
from database import Base, engine, SessionLocal
from models import *

def run_migrations():
    """Roda migrations do Alembic"""
    print("🔄 Executando migrations do Alembic...")
    try:
        result = subprocess.run(["alembic", "current"], capture_output=True, text=True)
        print(f"Status atual: {result.stdout.strip()}")
        
        # Aplicar migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Migrations aplicadas com sucesso!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar migrations: {e}")
        raise

def create_views():
    """Cria views customizadas"""
    print("🔄 Criando views customizadas...")
    with engine.connect() as connection:
        # View de carteira de pontos
        connection.execute(text("""
            CREATE OR REPLACE VIEW v_point_wallet AS
            SELECT
              person_id,
              scope,
              scope_id,
              SUM(delta) FILTER (WHERE expires_at IS NULL OR expires_at > now()) AS points
            FROM point_transaction
            GROUP BY person_id, scope, scope_id;
        """))
        
        # View de carteira de cupons
        connection.execute(text("""
            CREATE OR REPLACE VIEW v_coupon_wallet AS
            SELECT
              issued_to_person_id AS person_id,
              offer_id AS coupon_offer_id,
              COUNT(*) FILTER (WHERE status IN ('ISSUED','RESERVED')) AS available_count,
              COUNT(*) FILTER (WHERE status = 'REDEEMED') AS redeemed_count
            FROM coupon
            GROUP BY issued_to_person_id, offer_id;
        """))
        
        connection.commit()
    print("✅ Views criadas!")

def create_sample_data():
    """Cria dados de exemplo"""
    db = SessionLocal()
    try:
        # Verificar se já existem dados
        if db.query(Customer).first():
            print("⚠️ Dados de exemplo já existem")
            return
        
        print("🔄 Criando dados de exemplo...")
        
        # Cliente
        customer = Customer(
            cnpj="12.345.678/0001-90",
            name="Rede Exemplo Ltda",
            contact_email="contato@exemplorede.com",
            phone="(11) 99999-9999"
        )
        db.add(customer)
        db.flush()
        
        # Franquia
        franchise = Franchise(
            customer_id=customer.id,
            cnpj="12.345.678/0002-71",
            name="Franquia Centro"
        )
        db.add(franchise)
        db.flush()
        
        # Loja
        store = Store(
            franchise_id=franchise.id,
            cnpj="12.345.678/0003-52",
            name="Loja Shopping Center",
            location={"endereco": "Rua das Flores, 123", "cidade": "São Paulo"}
        )
        db.add(store)
        db.flush()
        
        # Pessoa
        person = Person(
            cpf="123.456.789-00",
            name="João da Silva",
            phone="(11) 98888-8888"
        )
        db.add(person)
        db.flush()
        
        # Usuário (password: 123456)
        user = AppUser(
            person_id=person.id,
            email="joao@teste.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.RK6E4S1D6",
            role="USER"
        )
        db.add(user)
        
        # Regra de pontos global
        point_rule = PointRules(
            scope=ScopeEnum.GLOBAL,
            points_per_brl=1.0,
            expires_in_days=365
        )
        db.add(point_rule)
        
        # Tipo de cupom
        coupon_type = CouponType(
            sku_specific=False,
            redeem_type=RedeemTypeEnum.BRL,
            discount_amount_brl=10.00
        )
        db.add(coupon_type)
        db.flush()
        
        # Oferta de cupom
        coupon_offer = CouponOffer(
            entity_scope=ScopeEnum.STORE,
            entity_id=store.id,
            coupon_type_id=coupon_type.id,
            initial_quantity=100,
            current_quantity=100,
            max_per_customer=5,
            is_active=True
        )
        db.add(coupon_offer)
        
        db.commit()
        print("✅ Dados de exemplo criados!")
        print("📧 Login: joao@teste.com")
        print("🔐 Senha: 123456")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar dados: {e}")
        print(f"Detalhes: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados...")
    try:
        run_migrations()
        create_views()
        create_sample_data()
        print("✨ Pronto! Banco inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro geral: {e}")