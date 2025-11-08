from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
        conn.commit()
    print('✓ Tabela alembic_version removida com sucesso')
except Exception as e:
    print(f'Aviso: {e}')

