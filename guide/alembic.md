# Como funcionam as **Alembic migrations**

**TL;DR:** Alembic é a ferramenta oficial do SQLAlchemy para versionar o esquema do banco. Você descreve mudanças do schema em scripts Python chamados *revisions*; cada revision tem funções `upgrade()` e `downgrade()`. O Alembic mantém um histórico linear (ou ramificado) e grava, numa tabela interna, qual versão o banco está. Comandos como `alembic upgrade head` aplicam as mudanças pendentes.

---

## Conceitos essenciais

* **alembic.ini** – configurações (URL do banco, diretórios, etc.).
* **env.py** – “ambiente” de migração; conecta no DB e define o *metadata* alvo (para *autogenerate*).
* **versions/** – pasta com os scripts de migração (*revisions*).
* **Revision** – arquivo com `revision = "xxxx"`, `down_revision = "yyyy"`, `def upgrade()`, `def downgrade()`.
* **Tabela alembic\_version** – guarda a revision atual aplicada naquele banco.

---

## Instalação e bootstrap

```bash
pip install alembic
alembic init alembic
```

Estrutura típica:

```
alembic.ini
alembic/
  env.py
  script.py.mako
  versions/
```

No `alembic.ini`, você pode **omitir** a URL e usar variável de ambiente no `env.py`.

---

## Integração com SQLAlchemy (autogenerate)

No `alembic/env.py`, exponha o `MetaData` dos seus modelos para o Alembic comparar o estado atual do DB com os modelos:

```python
# env.py (trecho comum)
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# importe seu Base
from app.db import Base  # Base = declarative_base()
target_metadata = Base.metadata

def run_migrations_online():
    config = context.config
    url = os.getenv("DATABASE_URL")
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,                      # usa env var
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # detecta mudanças de tipo
            compare_server_default=True,
            render_as_batch=True,    # útil para SQLite; inofensivo no PG
        )
        with context.begin_transaction():
            context.run_migrations()
```

---

## Criar migrações

### Manual

```bash
alembic revision -m "cria tabela orders"
```

Edite `versions/<timestamp>_cria_tabela_orders.py` e use a API `op`:

```python
from alembic import op
import sqlalchemy as sa

revision = "abcd1234"
down_revision = "wxyz9876"

def upgrade():
    op.create_table(
        "order",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("total_brl", sa.Numeric(12,2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_order_created", "order", ["created_at"])

def downgrade():
    op.drop_index("ix_order_created", table_name="order")
    op.drop_table("order")
```

### Autogerada (com base nos modelos)

```bash
alembic revision --autogenerate -m "add coluna phone em person"
```

O Alembic compara `target_metadata` com o banco e preenche `upgrade()/downgrade()`. **Revise o diff** antes de aplicar.

---

## Aplicar, voltar, inspecionar

```bash
alembic upgrade head          # aplica tudo até a última revisão
alembic upgrade +1            # avança 1 migração
alembic downgrade -1          # volta 1 migração
alembic downgrade base        # zera o schema
alembic current               # mostra a versão aplicada
alembic history --verbose     # lista o histórico
alembic heads                 # mostra "pontas" (branches)
alembic show <revision_id>    # detalhes da revisão
alembic stamp head            # marca o DB como na head, sem executar (use com cuidado)
```

**Offline (gera SQL sem conectar):**

```bash
alembic upgrade head --sql > migrations.sql
```

---

## Branches e merges

Em times, duas revisões diferentes podem ter o mesmo `down_revision` → **branch**. O Alembic permite *merge*:

```bash
alembic merge -m "merge branches" <revA> <revB>
```

Cria uma revisão “conectora” com `down_revision = ('revA','revB')` para voltar a uma linha única.

---

## Migrações de dados (não só schema)

Você pode alterar dados dentro de `upgrade()`/`downgrade()`:

```python
from sqlalchemy.orm import Session

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("UPDATE person SET phone = regexp_replace(phone, '[^0-9]', '', 'g')"))
    session.commit()
```

Boas práticas:

* Seja **idempotente** quando possível.
* Faça em **lotes** (chunked) se a tabela for grande.
* Registre em *audit\_log* se for crítico.

---

## Dicas específicas para PostgreSQL

* **Enums**: se precisar criar **ENUM** nativo:

  ```python
  op.execute("CREATE TYPE redeem_type AS ENUM ('BRL','PERCENTAGE','FREE_SKU')")
  op.add_column("coupon_type", sa.Column("redeem_type", sa.Enum(name="redeem_type"), nullable=False))
  ```

  Para **adicionar** um novo valor:

  ```python
  op.execute("ALTER TYPE redeem_type ADD VALUE IF NOT EXISTS 'FREE_SKU'")
  ```

* **ALTER TYPE com conversão**:

  ```python
  op.alter_column(
      "point_transaction", "delta",
      type_=sa.Integer(),
      postgresql_using="delta::integer"
  )
  ```

* **Views / Materialized Views**:

  ```python
  op.execute("""
  CREATE OR REPLACE VIEW v_point_wallet AS
  SELECT person_id, scope, scope_id,
         SUM(delta) FILTER (WHERE expires_at IS NULL OR expires_at > now()) AS points
  FROM point_transaction GROUP BY 1,2,3
  """)
  ```

* **Índices GIN/BTREE**:

  ```python
  op.create_index("ix_offer_segment_gin", "coupon_offer", ["customer_segment"], postgresql_using="gin")
  ```

* **Batch alter** (seguro para mudanças complexas em tabelas usadas):

  ```python
  with op.batch_alter_table("order") as batch:
      batch.add_column(sa.Column("source", sa.Text(), server_default="PDV", nullable=False))
  ```

---

## Convenções e qualidade

* **Naming conventions** no `Base.metadata` para autogenerate consistente:

  ```python
  from sqlalchemy import MetaData
  NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
  }
  Base = declarative_base(metadata=MetaData(naming_convention=NAMING))
  ```

* **Granularidade**: uma mudança por revisão. Evite “mega” migrações.

* **Destrutivas** (drop de tabela/coluna) – faça em duas fases: 1) parar de usar; 2) dropar numa versão posterior.

* **Revisar autogenerate**: principalmente *server\_default*, *nullable*, tipos e índices.

* **Rollback**: mantenha `downgrade()` funcional pelo menos até a última release.

---

## Rodando no CI/CD e no app

* CI: `alembic upgrade head` em um banco de teste; gere *SQL offline* para auditoria se precisar.
* Produção: execute migrações pelo pipeline antes do deploy do app (ou em *prestart job*).
* Rodar migração **automaticamente** no startup do servidor é prático, mas só faça se a disciplina de *feature flags* e *backward compatibility* estiver sólida.

---

## Erros comuns e como evitar

* **Autogenerate não detecta tudo**: mudanças em *constraints* nomeadas manualmente, triggers e *views* precisam de `op.execute`.
* **Branch esquecido**: sempre verifique `alembic heads`; se >1, faça `merge`.
* **Alterar enum removendo valor**: no PG é complicado; geralmente crie um novo tipo, converta dados, troque a coluna e apague o antigo.
* **Migração pesada em hora de pico**: adie, use *LOCK* mínimo, crie índices **CONCURRENTLY** quando possível (não suportado diretamente no `op.create_index`; use `op.execute('CREATE INDEX CONCURRENTLY ...')` em transação separada).

---

## Mini “cola” de comandos

```bash
# gerar
alembic revision -m "..."                      # manual
alembic revision --autogenerate -m "..."       # a partir dos modelos

# aplicar / voltar
alembic upgrade head
alembic upgrade +1
alembic downgrade -1
alembic downgrade base

# inspeção
alembic current
alembic history
alembic heads
alembic show <rev>

# branches
alembic merge -m "merge" <revA> <revB>

# marcar sem executar (cuidado)
alembic stamp head
```

Com isso, você consegue **versionar, auditar e automatizar** a evolução do schema do seu Postgres de forma segura em qualquer ambiente (dev, staging, produção).

# Quando você altera um *model*, o que acontece com o Alembic? Como arquitetar o fluxo

## Ideia central

* **Os *models* (SQLAlchemy) descrevem a intenção atual do seu schema.**
* **As *migrations* do Alembic são o histórico publicado dessa evolução.**
  O DB **não muda** só porque você alterou o *model*. Você precisa **gerar, revisar e aplicar** uma *migration* que leve o banco da versão anterior para a nova.

Se você alterar um *model* e **não** criar a migration correspondente, você cria **drift** (deriva) entre código e banco. A aplicação pode quebrar em runtime (coluna não existe, tipo diferente etc.).

---

## Arquitetura recomendada do fluxo

### 1) Organização do projeto

```
app/
  db.py                # engine, session, Base (com naming conventions)
  models/              # models SQLAlchemy (organizados por domínio)
    __init__.py        # importa todos os modelos p/ expor Base.metadata
    *.py
alembic/
  env.py               # aponta para Base.metadata
  versions/            # histórico de migrations (uma por mudança)
alembic.ini
```

**db.py (exemplo com naming conventions para diffs consistentes)**

```python
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

NAMING = {
  "ix": "ix_%(column_0_label)s",
  "uq": "uq_%(table_name)s_%(column_0_name)s",
  "ck": "ck_%(table_name)s_%(constraint_name)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s",
}
Base = declarative_base(metadata=MetaData(naming_convention=NAMING))
```

**alembic/env.py (trecho relevante)**

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.db import Base
import os

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=os.getenv("DATABASE_URL"),
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

> **Importante:** nunca use `Base.metadata.create_all()` em produção; **somente Alembic** deve criar/alterar schema.

---

### 2) Ciclo de mudança (passo a passo)

1. **Alterar o model**

   * Adicionar/alterar/remover coluna, índice, FK, tabela, enum etc.
2. **Gerar a migration**

   * **Autogenerate** (bom para a maioria dos casos):

     ```bash
     alembic revision --autogenerate -m "add phone em person"
     ```
   * **Manual** (útil para renomear coluna, views, enums, data-fix):

     ```bash
     alembic revision -m "rename col foo->bar e backfill"
     ```
3. **Revisar a migration**

   * Checar `upgrade()`/`downgrade()`.
   * Ajustar operações especiais (rename, view, enum, índices CONCURRENTLY).
4. **Aplicar local**

   ```bash
   alembic upgrade head
   ```

   Rodar testes.
5. **Commitar e abrir PR**

   * *Model + migration no mesmo PR*.
6. **CI/CD**

   * Rodar `alembic upgrade head` em DB de teste.
   * Gate de **detecção de drift** (abaixo).
7. **Produção**

   * Pipeline aplica migrations antes (ou junto) do deploy.
   * Aplicações devem ser **compatíveis para frente e para trás** durante a janela de deploy (ver “zero downtime”).

---

## Boas práticas para evitar *drift* e *downtime*

### Drift guard (checagem automática)

No CI, gere um *dry-run* e falhe se houver diffs não comitados:

```bash
# exemplo simples: tenta autogerar e procura por "No changes"
OUT=$(alembic revision --autogenerate -m "drift-check" --sql 2>&1 || true)
echo "$OUT" | grep -q "No changes detected" || \
  (echo "Há mudanças de schema não migradas!"; exit 1)
```

> Alternativamente, rode um *script* que compare `Base.metadata` com o schema atual e alerte.

### Compatibilidade progressiva (zero-downtime)

* **Adicionar coluna** como *nullable* → subir app → popular dados → tornar *NOT NULL* em uma migração futura.
* **Renomear coluna**:

  1. adicionar a nova, escrever em ambas, ler preferindo nova;
  2. *backfill*;
  3. remover a antiga em release posterior.
* **Enums**: adicionar valores com `ALTER TYPE ... ADD VALUE`; para remover/trocar, crie **novo tipo**, converta dados, troque a coluna e apague o antigo.
* **Índices grandes**: criar **CONCURRENTLY** (em transação separada; use `op.execute`).
* **Mutações pesadas**: fazer em *chunks*; usar *maintenance window* se necessário.

### Política de *branches* de migration

* Cada PR deve apontar para a `down_revision` mais recente.
* Se surgirem **duas heads**, faça:

  ```bash
  alembic merge -m "merge heads" <revA> <revB>
  ```

---

## O que o autogenerate detecta (e o que não detecta tão bem)

**Detecta bem**

* Tabelas/colunas novas/removidas.
* Tipos alterados (`compare_type=True`).
* *Server defaults* (`compare_server_default=True`).
* FKs/UKs/IXs normais (com naming conventions).

**Requer atenção manual**

* **Renomear coluna/tabela** (autogenerate interpreta como drop + add).
* **Views, materialized views, triggers, policies RLS** (use `op.execute`).
* **Índices CONCURRENTLY** (criar manualmente).
* **Enums** (manter com `op.execute` ao alterar valores).
* **Check constraints complexos**.

---

## Exemplos de mudanças comuns

### 1) Adicionar coluna com default e NOT NULL (2 etapas)

```python
# models.py
phone = sa.Column(sa.Text, nullable=False, server_default="")
```

Migration (etapa 1):

```python
with op.batch_alter_table("person") as b:
    b.add_column(sa.Column("phone", sa.Text(), server_default="", nullable=False))
# opcional: b.alter_column("phone", server_default=None)
```

Etapa 2 (release seguinte):

```python
with op.batch_alter_table("person") as b:
    b.alter_column("phone", server_default=None)
```

### 2) Renomear coluna (manual)

```python
op.alter_column("person", "cpf_old", new_column_name="cpf")
```

### 3) Adicionar valor a ENUM

```python
op.execute("ALTER TYPE redeem_type ADD VALUE IF NOT EXISTS 'FREE_SKU'")
```

### 4) Índice grande sem bloquear

```python
op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_order_created ON "order" (created_at DESC)')
```

---

## Estratégia de execução no *app*

* **Não** crie/alter e schema no *startup* do app (evite `create_all`).
* Opcional: no *startup*, apenas **verifique** se o DB está na `head` e logue/alerte:

  ```python
  from alembic.config import Config
  from alembic.script import ScriptDirectory
  from sqlalchemy import text

  def assert_db_on_head(engine):
      cfg = Config("alembic.ini")
      script = ScriptDirectory.from_config(cfg)
      with engine.connect() as conn:
          current = conn.execute(text("select version_num from alembic_version")).scalar()
      head = script.get_current_head()
      if current != head:
          logger.error("DB não está na head (%s != %s)", current, head)
  ```

---

## Resumo prático

* **Mudou model?** Gere uma **migration**, revise e aplique.
* **Fonte da verdade do schema** em produção = **migrations** (não os models).
* **Commit** sempre *model + migration* juntos.
* **CI** protege contra *drift*.
* **Mutações destrutivas** em **duas fases**.
* **Merges** resolvem *branches* de migrations quando PRs paralelos acontecem.

Seguindo esse desenho, o Alembic vira um **histórico confiável** da evolução do banco e seu time evita surpresas no deploy.
