from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/fidelity")

# Cria a engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Cria uma sessão local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para declaração de modelos
Base = declarative_base()


# Dependency para obter sessão de banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
