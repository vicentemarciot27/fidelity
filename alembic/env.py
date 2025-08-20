import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Adicionar projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Alembic
config = context.config

# Setup de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔑 IMPORTAR MODELOS - ESSENCIAL!
from database import Base
from models import *

# Metadados das tabelas
target_metadata = Base.metadata

def get_database_url():
    """Pega URL do banco das variáveis de ambiente"""
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fidelity")

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Configurar URL do banco
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()