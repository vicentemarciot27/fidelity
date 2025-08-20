\[Your analysis of the Figma images and overall design, including any suggestions for improvements]

**What the screenshots describe (high-level domain)**
A loyalty & coupon system for a marketplace with **tenants** (Customer → Franchise → Store), **people/users**, **points**, and **coupon offers / coupons**.

* **Endpoints shown**

  * `/get_wallet` → return a person’s wallet; display points in *brl* or *points*.
  * `/pointsByOrder` → compute points from an order payload using **CustomerGenRules** + **PointsCalculator**.
  * `/coupons/offer` (CRUD) → manage **CouponOffer**.
  * `/buy_coupon` → acquire/issue a coupon from an offer (no frontend yet).
  * `/get_coupon_offers` → list available offers (no frontend yet).
  * `/attempt_coupon` → validate a coupon by hash for redemption.

* **Entities & relationships surfaced**

  * **Customer** (tenant) has many **Franchise**; Franchise has many **Store**.
  * **Person** (individual) linked to **Users** (auth).
  * **PointTransactions** (delta, store, expires\_at) roll up into a **PointWallet (View)** keyed by person + scope (**GLOBAL | CUSTOMER | FRANCHISE | STORE**) + entity id.
  * **CustomerMarketplaceRules** / **CustomerGenRules** (per-tenant configs) drive point accrual and eligibility.
  * **CouponType** defines how a discount works.
  * **CouponOffer** belongs to an entity scope (Store/Franchise/Customer), has inventory & per-customer limits.
  * **Coupon** holds a protected **hash** code.
  * **CouponWallet** associates Person ↔ CouponOffer (and effectively the issued coupons).

**Design evaluation & suggestions**

* The core modeling is sound. Treating points as **immutable deltas** is best-practice; the wallet should be a **(materialized) view** over transactions.
* Make **scope** explicit instead of separate wallet tables: `(scope, scope_id) ∈ {GLOBAL, CUSTOMER, FRANCHISE, STORE}`; this matches the diagrams.
* Collapse *Coupon* + *CouponWallet* into a single **issued coupon** record (`coupon`) with `offer_id`, `issued_to_person_id`, `code_hash`, `status`. Keep a small **view** to present the “wallet”.
* Add **validity windows** (`start_at`, `end_at`) on offers, plus **redemption window**/`expires_at` on coupons/points.
* Use **JSONB** for segmentation/rules (as the diagrams suggest future flexibility) with **GIN** indexes on frequently queried paths.
* Enforce **inventory atomically** during `/buy_coupon` (transaction + `SELECT … FOR UPDATE` on the offer row).
* Introduce **enums** for `scope`, `redeem_type`, `coupon_status` to avoid magic strings.
* Multi-tenant security: add **Row Level Security** scoped by `customer_id` (directly or via store→franchise→customer).
* Normalize **CNPJ/CPF** as `TEXT` with business rules in the app; keep unique indexes.
* Consider a **materialized wallet view** refreshed on schedule or after large batch inserts if read frequency is high.

---

\[List of identified classes]

* Customer
* Franchise
* Store
* Person
* User (auth)
* CustomerMarketplaceRules (config)
* CustomerGenRules / PointRules (config for accrual & conversions)
* PointTransaction
* PointWallet (SQL view)
* CouponType
* CouponOffer
* Coupon (issued, hashed code; represents “CouponWallet”)
* CouponWallet (SQL view grouping issued coupons by person & offer)

*(Potential supportive but optional)*: Product/SKU catalog (the diagrams keep SKUs as arrays/ids inside rules/types; a real catalog could live elsewhere).

---

\[PostgreSQL schemas for each class]

```sql
-- Extensions (safe to include in migrations)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

-- =========================
-- Enums
-- =========================
DO $$ BEGIN
  CREATE TYPE scope AS ENUM ('GLOBAL','CUSTOMER','FRANCHISE','STORE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE redeem_type AS ENUM ('BRL','PERCENTAGE','FREE_SKU');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE coupon_status AS ENUM ('CREATED','ISSUED','RESERVED','REDEEMED','CANCELLED','EXPIRED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =========================
-- Core parties / tenancy
-- =========================
CREATE TABLE IF NOT EXISTS customer (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cnpj          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  contact_email CITEXT,
  phone         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS franchise (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id   UUID NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
  cnpj          TEXT UNIQUE,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_franchise_customer ON franchise(customer_id);

CREATE TABLE IF NOT EXISTS store (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  franchise_id  UUID NOT NULL REFERENCES franchise(id) ON DELETE CASCADE,
  cnpj          TEXT UNIQUE,
  name          TEXT NOT NULL,
  location      JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_store_franchise ON store(franchise_id);

-- =========================
-- People / users
-- =========================
CREATE TABLE IF NOT EXISTS person (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cpf        TEXT UNIQUE NOT NULL,
  name       TEXT NOT NULL,
  phone      TEXT,
  location   JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_user (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id     UUID UNIQUE NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  email         CITEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'USER',
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================
-- Tenant configs / rules
-- =========================
-- Arbitrary marketplace config per customer
CREATE TABLE IF NOT EXISTS customer_marketplace_rules (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID UNIQUE NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
  rules       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cmr_rules_gin ON customer_marketplace_rules USING GIN (rules);

-- Point accrual/conversion rules with optional overrides at franchise/store level
CREATE TABLE IF NOT EXISTS point_rules (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scope           scope NOT NULL,                  -- where the rule applies
  customer_id     UUID REFERENCES customer(id) ON DELETE CASCADE,
  franchise_id    UUID REFERENCES franchise(id) ON DELETE CASCADE,
  store_id        UUID REFERENCES store(id) ON DELETE CASCADE,
  points_per_brl  NUMERIC(12,4),                  -- e.g., 1 point per BRL
  expires_in_days INTEGER,                        -- default points validity
  extra           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    (scope = 'CUSTOMER'  AND customer_id IS NOT NULL AND franchise_id IS NULL AND store_id IS NULL) OR
    (scope = 'FRANCHISE' AND franchise_id IS NOT NULL AND store_id IS NULL) OR
    (scope = 'STORE'     AND store_id IS NOT NULL) OR
    (scope = 'GLOBAL'    AND customer_id IS NULL AND franchise_id IS NULL AND store_id IS NULL)
  )
);
CREATE INDEX IF NOT EXISTS idx_point_rules_scope ON point_rules(scope);
CREATE INDEX IF NOT EXISTS idx_point_rules_extra_gin ON point_rules USING GIN (extra);

-- =========================
-- Points ledger & wallet view
-- =========================
CREATE TABLE IF NOT EXISTS point_transaction (
  id          BIGSERIAL PRIMARY KEY,
  person_id   UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  scope       scope NOT NULL,
  scope_id    UUID,                                -- null when scope=GLOBAL
  store_id    UUID REFERENCES store(id),           -- where it happened (earn/redeem)
  order_id    TEXT,                                -- from /pointsByOrder
  delta       INTEGER NOT NULL,                    -- positive earn / negative burn
  details     JSONB NOT NULL DEFAULT '{}'::jsonb,  -- raw calc, items, etc.
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at  TIMESTAMPTZ,                         -- when points become invalid
  CHECK (delta <> 0)
);
CREATE INDEX IF NOT EXISTS idx_pt_person_scope ON point_transaction(person_id, scope, scope_id);
CREATE INDEX IF NOT EXISTS idx_pt_expires ON point_transaction(expires_at);
CREATE INDEX IF NOT EXISTS idx_pt_store ON point_transaction(store_id);

-- Live wallet (non-expired)
CREATE OR REPLACE VIEW v_point_wallet AS
SELECT
  person_id,
  scope,
  scope_id,
  SUM(delta) FILTER (WHERE expires_at IS NULL OR expires_at > now()) AS points
FROM point_transaction
GROUP BY person_id, scope, scope_id;

-- =========================
-- Coupons
-- =========================
CREATE TABLE IF NOT EXISTS coupon_type (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sku_specific                BOOLEAN NOT NULL DEFAULT FALSE,
  redeem_type                 redeem_type NOT NULL,
  discount_amount_brl         NUMERIC(12,2),
  discount_amount_percentage  NUMERIC(5,2),
  valid_skus                  TEXT[],                 -- SKU ids if applicable
  CHECK (
    (redeem_type = 'BRL'        AND discount_amount_brl IS NOT NULL) OR
    (redeem_type = 'PERCENTAGE' AND discount_amount_percentage IS NOT NULL) OR
    (redeem_type = 'FREE_SKU'   AND valid_skus IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS coupon_offer (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_scope     scope NOT NULL CHECK (entity_scope IN ('CUSTOMER','FRANCHISE','STORE')),
  entity_id        UUID NOT NULL,                    -- FK by scope (not enforced by FK)
  coupon_type_id   UUID NOT NULL REFERENCES coupon_type(id),
  customer_segment JSONB,                            -- future targeting
  initial_quantity INTEGER NOT NULL DEFAULT 0 CHECK (initial_quantity >= 0),
  current_quantity INTEGER NOT NULL DEFAULT 0 CHECK (current_quantity >= 0),
  max_per_customer INTEGER NOT NULL DEFAULT 0,       -- 0 = unlimited
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  start_at         TIMESTAMPTZ,
  end_at           TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (current_quantity <= initial_quantity)
);
CREATE INDEX IF NOT EXISTS idx_offer_entity ON coupon_offer(entity_scope, entity_id);
CREATE INDEX IF NOT EXISTS idx_offer_active ON coupon_offer(is_active, start_at, end_at);
CREATE INDEX IF NOT EXISTS idx_offer_segment_gin ON coupon_offer USING GIN (customer_segment);

-- Every issued coupon (wallet item) – includes protected code hash
CREATE TABLE IF NOT EXISTS coupon (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_id             UUID NOT NULL REFERENCES coupon_offer(id) ON DELETE CASCADE,
  issued_to_person_id  UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  code_hash            BYTEA NOT NULL,     -- hash of plaintext; compare with constant-time function in app
  status               coupon_status NOT NULL DEFAULT 'ISSUED',
  issued_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  redeemed_at          TIMESTAMPTZ,
  redeemed_store_id    UUID REFERENCES store(id),
  UNIQUE (offer_id, code_hash)
);
CREATE INDEX IF NOT EXISTS idx_coupon_issued_to ON coupon(issued_to_person_id, status);
CREATE INDEX IF NOT EXISTS idx_coupon_code_hash ON coupon(code_hash);
CREATE INDEX IF NOT EXISTS idx_coupon_status ON coupon(status);

-- Friendly wallet grouping view (person + offer)
CREATE OR REPLACE VIEW v_coupon_wallet AS
SELECT
  issued_to_person_id AS person_id,
  offer_id            AS coupon_offer_id,
  COUNT(*) FILTER (WHERE status IN ('ISSUED','RESERVED')) AS available_count,
  COUNT(*) FILTER (WHERE status = 'REDEEMED')            AS redeemed_count
FROM coupon
GROUP BY issued_to_person_id, offer_id;
```

**Notes on FK by scope**
`coupon_offer.entity_id` references different tables depending on `entity_scope`. Enforcing this polymorphic FK at DB level is possible with triggers; most teams validate it in the application layer and index `(entity_scope, entity_id)` for performance (as above).

---

\[Your thoughts on how the design and schemas align with the given tech stack, and any relevant optimizations or considerations]

**PostgreSQL**

* The schema uses **enums, views, JSONB, and indexes** that Postgres handles very well.
* If wallet reads are heavy, consider a **materialized wallet view** with `REFRESH MATERIALIZED VIEW CONCURRENTLY v_point_wallet_mat` after batch inserts (or periodically via a job).
* Use **RLS** to enforce tenant boundaries (e.g., `customer_id` context set by JWT claim); derive `customer_id` from `store → franchise → customer` in views.
* For `code_hash`, store **Argon2id**/bcrypt hashes; validate with constant-time compare in the app.

**FastAPI (Python)**

* Model with **SQLAlchemy 2.x** + **Alembic** migrations. Map Postgres enums with `sqlalchemy.Enum`.
* Pydantic schemas mirror the DB tables; keep `rules`/`customer_segment` as `dict` (`JSONB`) for flexibility.
* Implement `/buy_coupon` transaction:

  1. `SELECT ... FOR UPDATE` the `coupon_offer`.
  2. Check inventory, user quota, validity window.
  3. Decrement `current_quantity`.
  4. Insert `coupon` with `issued_to_person_id` + `code_hash`.
* Implement `/attempt_coupon` by hashing input and querying `coupon` with `status IN ('ISSUED','RESERVED')`. Update to `REDEEMED` + append a **negative** `point_transaction` if paying with points.
* Implement `/get_wallet` by querying `v_point_wallet` + converting to BRL using `point_rules` (prefer cached config by tenant); format per `display_as`.

**Frontend (JavaScript)**

* Keep wallet and offers in separate screens. Use pagination over `/get_coupon_offers` with filters `(entity_scope, entity_id, active window)`.
* During redemption, avoid leaking codes—send plaintext to backend only, never store in client.
* For “SKU-specific” coupons, validate the cart on the server and let the UI display error codes from the API.

**Operational**

* Add **partial indexes** for active offers: `(is_active) WHERE is_active AND (start_at IS NULL OR start_at <= now()) AND (end_at IS NULL OR end_at >= now())`.
* Schedule **cleanup** for expired coupons & points (set `status='EXPIRED'`, or ignore via queries).
* If traffic is high, insert points in **bulk** and keep read-optimized paths via views/materialized views.

This design maps directly to the figures, stays flexible for future segmentation, and fits naturally with PostgreSQL + FastAPI + a JS frontend.

# Especificação de Produto e Implementação — **Marketplace**, **PDV** e **Admin** (com tabelas auxiliares)

> Esta proposta parte dos esquemas já definidos (Customer, Franchise, Store, Person/User, PointTransaction & *views*, CouponType, CouponOffer, Coupon/Wallet). Abaixo estão as camadas de **produto**, **fluxos**, **APIs FastAPI**, **UI**, **segurança** e **tabelas auxiliares** necessárias para entregar os três front-ends sem lacunas.

---

## 1) Perfis e permissões

**Papéis padrão**

* **Admin Global** (equipe da plataforma): tudo.
* **Customer Admin** (locatário): gerencia seu *tenant* (Customer, suas Franchises/Stores, ofertas, regras, staff).
* **Franchise Manager**: gerencia suas lojas e ofertas de franquia.
* **Store Manager** / **Caixa (POS)**: opera PDV, emite/usa cupons, lança pontos; sem acesso a regras.
* **Usuário Final (Marketplace)**: vê carteira, compra/pega cupons, usa cupons.

**Escopo de acesso**

* JWT inclui `role`, `customer_id`, `franchise_id?`, `store_id?`, `person_id?`.
* *Row Level Security* no Postgres garante isolamento por `customer_id` (derivado de `store → franchise → customer` quando aplicável).

---

## 2) Tabelas auxiliares (PostgreSQL)

> Complementam o modelo anterior para suportar UI, segurança, inventário, auditoria e integrações.

```sql
-- ========= Identidade / Sessões =========
CREATE TABLE IF NOT EXISTS refresh_token (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  token_hash   BYTEA NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at   TIMESTAMPTZ NOT NULL,
  revoked_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_token(user_id);

CREATE TABLE IF NOT EXISTS api_key (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id  UUID REFERENCES customer(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  key_hash     BYTEA NOT NULL,
  scopes       TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at   TIMESTAMPTZ
);

-- ========= Staff por loja =========
CREATE TABLE IF NOT EXISTS store_staff (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  store_id   UUID NOT NULL REFERENCES store(id) ON DELETE CASCADE,
  role       TEXT NOT NULL CHECK (role IN ('STORE_MANAGER','CASHIER')),
  UNIQUE (user_id, store_id)
);

-- ========= Dispositivos PDV =========
CREATE TABLE IF NOT EXISTS device (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id         UUID NOT NULL REFERENCES store(id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  registration_code TEXT NOT NULL,        -- exibe no PDV para *pairing*; curta duração
  public_key       BYTEA,                  -- para assinatura opcional
  last_seen_at     TIMESTAMPTZ,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_device_store ON device(store_id);

-- ========= Catálogo opcional (para SKU-specific) =========
CREATE TABLE IF NOT EXISTS category (
  id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sku (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  brand       TEXT,
  category_id UUID REFERENCES category(id),
  metadata    JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_sku_customer ON sku(customer_id);

-- ========= Pedidos (base para pointsByOrder) =========
CREATE TABLE IF NOT EXISTS "order" (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id       UUID NOT NULL REFERENCES store(id) ON DELETE CASCADE,
  person_id      UUID REFERENCES person(id),
  total_brl      NUMERIC(12,2) NOT NULL,
  tax_brl        NUMERIC(12,2) NOT NULL DEFAULT 0,
  items          JSONB NOT NULL,            -- [{sku_id?, name, categoryId?, qty, price, tax, brand, ...}]
  shipping       JSONB,                     -- conforme payload
  checkout_ref   TEXT,                      -- p.ex. "c73-h268"
  external_id    TEXT,                      -- id no ERP/PDV
  source         TEXT NOT NULL DEFAULT 'PDV',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_store_created ON "order"(store_id, created_at DESC);

-- ========= Assets de oferta (imagens para marketplace) =========
CREATE TABLE IF NOT EXISTS offer_asset (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_id   UUID NOT NULL REFERENCES coupon_offer(id) ON DELETE CASCADE,
  kind       TEXT NOT NULL CHECK (kind IN ('BANNER','THUMB','DETAIL')),
  url        TEXT NOT NULL,
  position   SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ========= Idempotência & Rate Limit =========
CREATE TABLE IF NOT EXISTS idempotency_key (
  key            TEXT PRIMARY KEY,
  owner_scope    TEXT NOT NULL,                 -- ex: person:<id> ou device:<id>
  request_hash   BYTEA NOT NULL,
  response_body  BYTEA,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at     TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_limit_counter (
  key          TEXT PRIMARY KEY,                -- ex: "redeem:<coupon_id>"
  count        INTEGER NOT NULL,
  window_start TIMESTAMPTZ NOT NULL
);

-- ========= Auditoria & Eventos =========
CREATE TABLE IF NOT EXISTS audit_log (
  id            BIGSERIAL PRIMARY KEY,
  actor_user_id UUID REFERENCES app_user(id),
  actor_device_id UUID REFERENCES device(id),
  action        TEXT NOT NULL,                  -- ex: OFFER_CREATE, COUPON_REDEEM
  target_table  TEXT,
  target_id     TEXT,
  before        JSONB,
  after         JSONB,
  ip            INET,
  user_agent    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS outbox_event (
  id          BIGSERIAL PRIMARY KEY,
  topic       TEXT NOT NULL,                    -- ex: "coupon.redeemed"
  payload     JSONB NOT NULL,
  status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING|SENT|ERROR
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at     TIMESTAMPTZ
);
```

---

## 3) APIs (FastAPI) — Contratos essenciais

> Nomes/rotas estáveis; todos com **Idempotency-Key** opcional via header quando indicado. Todas as respostas usam `application/json; charset=utf-8`.

### Autenticação

* `POST /auth/login` → troca `email + senha` por `{access_token, refresh_token}`.
* `POST /auth/refresh` → `{refresh_token}` → novo par de tokens.
* `POST /auth/logout` → revoga *refresh tokens*.
* `POST /auth/pdv/register-device` (sem auth) → `{store_id, registration_code}` → `{device_token}`.

  * O registration code é emitido no Admin para pareamento.

### Marketplace (Usuário Final)

* `GET /wallet?display_as=points|brl`
  **200** `{balances: [{scope, scope_id, points, as_brl}], coupons: [{offer_id, available_count, redeemed_count}]}`.
* `GET /offers?scope=CUSTOMER|FRANCHISE|STORE&scope_id=<uuid>&active=true&search=&page=&page_size=`
  Retorna lista paginada com assets.
* `GET /offers/{id}` → detalhe + `coupon_type`.
* `POST /coupons/buy` *(idempotente por pessoa)*
  Body: `{offer_id}`
  Regras: janela válida, `is_active`, estoque `current_quantity > 0`, `max_per_customer`, segmento, *throttling*.
  Efeitos: `current_quantity--`, cria `coupon` com `ISSUED` e **gera code plaintext** (retornado **só nesta chamada**), armazena `code_hash`.
  **201** `{coupon_id, code, qr:{format:'svg', data:'...'}}`.
* `GET /coupons/my` → listar emitidos (sem `code`), status.

### PDV (Caixa/Dispositivo)

* Header `Authorization: Bearer <device JWT>`.
* `POST /pdv/attempt-coupon` *(idempotente por device)*
  Body: `{code, order_total_brl, items?, store_id}`
  Passos (transação):

  1. localiza `coupon` por `code_hash`, estado `ISSUED|RESERVED`, janela de oferta válida; valida *tenant*.
  2. **Reserva** (`status=RESERVED`) com `SELECT ... FOR UPDATE SKIP LOCKED` para evitar duplo uso.
  3. Recalcula aplicabilidade (SKU-specific, min cart etc).
     Resposta: `{coupon_id, redeemable: true|false, discount:{type, amount_brl|percentage}, message}`.
* `POST /pdv/redeem` *(idempotente via Idempotency-Key)*
  Body: `{coupon_id, order_id?, order:{...}}`
  Atualiza `coupon.status='REDEEMED'`, `redeemed_at`, `redeemed_store_id`, grava `order` se enviado, publica `outbox_event('coupon.redeemed')`.
  **200** `{ok:true}`.
* `POST /pdv/earn-points`
  Body é o payload de `/pointsByOrder` (figma) + `person_id|cpf`.
  Backend: seleciona `point_rules` por hierarquia (STORE > FRANCHISE > CUSTOMER > GLOBAL), persiste `order` e `point_transaction (+delta)`, calcula `expires_at`.
  **201** `{order_id, points_earned, wallet_snapshot}`.

### Admin

* CRUD: `/customers`, `/franchises`, `/stores`, `/users`, `/store-staff`
* Regras: `/point-rules` (CRUD), `/customer-marketplace-rules` (CRUD)
* Catálogo (opcional): `/skus`, `/categories`
* Ofertas:

  * `POST /coupon-types`
  * `POST /coupon-offers`
  * `PATCH /coupon-offers/{id}` (alterações de inventário só **incrementais**; nunca reduzir abaixo de emitidos)
  * `POST /coupon-offers/{id}/assets` (upload url-assinado)
  * `GET /coupon-offers/{id}/stats` → emitidos, disponíveis, resgatados, por período, por loja.
* Operações:

  * `POST /coupons/{id}/cancel` (se não resgatado).
  * `POST /offers/{id}/bulk-issue` (campanhas: emite `N` cupons p/ segmento; resultado em *outbox*).

---

## 4) Front-end **Marketplace** (Web/Mobile)

**Tecnologias**

* JS/TS + React/Next.js. State global com Zustand/Redux. Query com React Query.
* Autenticação via OAuth Password ou Magic Link (opcional), tokens salvos em *Secure Storage* (Web: cookie httpOnly + SameSite=Lax).

**Páginas/Componentes**

1. **Onboarding/Login**: CPF + telefone/email; cria `person`+`app_user` se necessário.
2. **Home / Descoberta de Ofertas**: filtros (categoria, escopo), paginação. Cards com `offer_asset`.
3. **Detalhe da Oferta**: regras resumidas (SKU-specific, validade), estoque disponível (aproximado, ex: “poucas unidades”).
4. **Carteira**:

   * **Pontos**: saldos por `scope`. *Toggle* `display_as: brl|points` (*/wallet*).
   * **Cupons**: listagem (`v_coupon_wallet` + detalhes). Botão “Mostrar QR/Code” ⇒ abre modal somente para cupons **emitidos** (retorna code via endpoint temporário **one-time**; ver segurança abaixo).
5. **Comprar/Obter Cupom**: chama `POST /coupons/buy`. Exibe QR + código alfanumérico. Opcional: adicionar ao Apple/Google Wallet (gera `.pkpass`/`Save to Google Wallet`).
6. **Histórico**: cupons resgatados e pontos ganhos/gastos (consulta em *ledger*).
7. **Perfil**: dados pessoais, consentimentos LGPD, preferências.

**Segurança UX**

* O **código plaintext** do cupom só é retornado no `buy` ou por **/coupons/{id}/reveal** (uma única vez; depois só QR com *nonce de sessão*).
* Bloquear *screenshots* (melhoria) e sempre validar no servidor.

**Acessibilidade e i18n**

* WCAG AA, textos alt, `aria-*`.
* i18n pronto para PT/EN.

---

## 5) Front-end **PDV** (Desktop/Tablet)

**Tecnologias**

* React (Electron opcional para *kiosk*), integração com câmera/leitor para QR/Code128.

**Fluxos**

1. **Pareamento de dispositivo**: operador insere `registration_code` fornecido no Admin ⇒ recebe `device_token`.
2. **Tela principal**:

   * Campo “Digite/escaneie código” (QR/alfanumérico).
   * **Pré-validação** (`/pdv/attempt-coupon`) mostra **valor do desconto** e status (ex.: “válido para carrinho atual”).
   * Botão **Resgatar** (`/pdv/redeem`) com `Idempotency-Key` (UUID por operação).
3. **Acúmulo de pontos**:

   * Tela “Identificar cliente” (CPF/telefone).
   * Form do pedido (ou integração com ERP envia `order` já pronto).
   * Chamada `/pdv/earn-points`. UI mostra pontos ganhos e saldo estimado.

**Offline**

* *Queue* local para `/pdv/earn-points` (somente **acúmulo** pode atrasar).
* **Resgate de cupom não opera offline.** UI bloqueia.

**Anti-fraude**

* Rate limit por `device_id` e por `coupon_id`.
* Reserva de cupom com *lock*; expira reserva automaticamente (p.ex. 2 min) via *job* se não houver `redeem`.

---

## 6) Front-end **Admin**

**Tecnologias**

* React + shadcn/ui. Tabelas com DataGrid (filtro/ordenar/export).

**Módulos**

1. **Tenancy**

   * Customer (CNPJ, contato), Franchises, Stores (localização), Staff (convites).
2. **Regras**

   * **Point Rules** por escopo (GLOBAL/CUSTOMER/FRANCHISE/STORE) com *preview* de cálculo. Campos: `points_per_brl`, `expires_in_days`, `extra(JSONB)`.
   * **Marketplace Rules** (JSONB): flags de participação, limites de catálogo, etc.
3. **Catálogo (opcional)**: SKUs e categorias.
4. **Ofertas**

   * **Coupon Types**: tipo, valor (BRL/%), *valid\_skus*.
   * **Coupon Offers**: escopo + segmentação (builder JSON), janela (`start_at/end_at`), inventário (inicial/atual), limite por cliente, ativos/inativos.
   * **Assets**: upload e ordenação (arrastar).
   * **Relatórios**: funil (exibição→emissões→reservas→resgates), *heatmap* por loja, *top SKUs* impactados.
5. **Operações**

   * Emissão em massa (para segmento).
   * Cancelamento administrativo de cupom (não resgatado) com motivo.
   * Geração de *registration\_code* de dispositivos PDV.
6. **Auditoria & Logs**

   * Lista de `audit_log` com filtros por ator, ação, período.
7. **Chaves de API**

   * Criar/revogar `api_key`, escopos.

---

## 7) Regras de negócio detalhadas

**Validade & Janela**

* Oferta é **elegível** se `is_active` e `(start_at IS NULL or start_at <= now())` e `(end_at IS NULL or end_at >= now())`.

**Inventário**

* `current_quantity` decrementa **apenas** na emissão (`/coupons/buy`).
* Não permite atualizar `current_quantity` abaixo de `emitidos`. Mudanças via `PATCH` só incrementais.

**Limite por pessoa**

* `max_per_customer = 0` ⇒ ilimitado; senão, contar cupons *emitidos* para `person_id` e bloquear novas emissões.

**Segmentação**

* `customer_segment(JSONB)` com caminhos comuns (`min_age`, `zip_prefix`, `tags[]`).
* Index GIN e validação em aplicação.

**Cálculo de pontos**

* Seleção de `point_rules` por precedência: `STORE > FRANCHISE > CUSTOMER > GLOBAL`.
* `points = floor((total_brl - shipping.tax_exempt?) * points_per_brl)`.
* `expires_at = created_at + expires_in_days`.

**Resgate de cupom**

* `attempt` cria **reserva** temporária (status `RESERVED`) com *lock* em `coupon.id`.
* `redeem` confirma; caso contrário, *job* reverte `RESERVED → ISSUED` após *timeout*.

---

## 8) Segurança, privacidade e conformidade

* Senhas em **Argon2id** (ou bcrypt forte); `code_hash` dos cupons via **bcrypt/argon** também (não reversível).
* Dados sensíveis (CPF, telefone) → **colunas mascaradas** na aplicação; considerar criptografia à nível de app (libsodium) se requerido.
* Cookies `httpOnly` + `SameSite=Lax` no marketplace; POS usa *device token* (JWT curto + *refresh* via *pairing*).
* **RLS** no Postgres para todas as tabelas com `customer_id` indireto: usar **views** que projetam `customer_id` e políticas `USING` / `WITH CHECK`.
* **Idempotência** em `redeem`, `buy` e `earn-points`.
* **Rate limiting** (Nginx/Envoy + Redis) por IP/usuário/dispositivo.
* LGPD: Consentimento explícito, *opt-out* de comunicações, *data export* e *erasure* por `person_id`.

---

## 9) Observabilidade & Operações

* **Logs estruturados** (JSON) com `trace_id`, `actor`, `tenant`.
* **Métricas** (Prometheus):

  * `offers_active`, `coupon_issued_total`, `coupon_redeemed_total`, `coupon_reserve_conflicts_total`,
  * `points_earned_total`, `wallet_view_latency_ms`, `redeem_latency_ms`.
* **Alertas**: taxa de erro > 1% em `/pdv/redeem`, divergência `current_quantity` vs emitidos, fila `outbox` atrasada.
* **Jobs (Celery/RQ/Arq)**:

  * Limpador de reservas expiradas.
  * Expiração de pontos (`SET status=EXPIRED` opcional ou ignorar via queries).
  * Publicação `outbox_event` (retries com *exponential backoff*).
  * *Refresh* de *materialized view* de carteira (se adotado).

---

## 10) Contratos de modelos (Pydantic) — exemplos

```python
# Marketplace
class BuyCouponReq(BaseModel):
    offer_id: UUID

class BuyCouponRes(BaseModel):
    coupon_id: UUID
    code: str               # retornado uma única vez
    qr: dict                # {format, data}

# PDV
class AttemptCouponReq(BaseModel):
    code: str
    order_total_brl: Decimal
    items: list[dict] | None = None
    store_id: UUID

class AttemptCouponRes(BaseModel):
    coupon_id: UUID
    redeemable: bool
    discount: dict | None   # {"type":"BRL","amount_brl":10.00}
    message: str | None
```

---

## 11) Experiência de usuário e casos extremos

* **Baixo estoque**: quando `current_quantity <= 10`, marketplace exibe “Poucas unidades”.
* **Condição SKU-specific**: no `attempt`, se `valid_skus` não intersecciona com `items[*].sku_id`, retornar `redeemable=false` + mensagem.
* **Devolução de pedido**: criar *reversal* em `point_transaction` com `delta` negativo e `details.reason='refund'`. Se cupom deu desconto fixo, não “des-resgatar” o cupom; política comercial decide.
* **Pessoa sem cadastro** no PDV: permitir ganho de pontos depois (vincular por CPF posteriormente) — `person_id` pode ser nulo no `order`, e o vínculo gera crédito retroativo (job que encontra pedidos abertos em janela X).

---

## 12) Deploy & Infra (resumo)

* **PostgreSQL 15+**; conexões via *pooler* (PgBouncer).
* **Redis** para cache, rate limit, filas curtas.
* **FastAPI** + Uvicorn/Gunicorn, *healthcheck*, *readiness*.
* **CDN** para assets (imagens de ofertas). Upload com URL assinado (S3/GCS).
* **CI/CD** com migrações Alembic, *blue/green* ou *rolling*.

---

## 13) Testes e critérios de aceite

* **Unitários**: cálculo de regras de pontos, validação SKU, limites por cliente.
* **Integração**: fluxo completo `buy → attempt → redeem`, concorrência (duas tentativas simultâneas).
* **Contrato** (Pact/pytest + schemathesis): validação de JSONs.
* **Carga**: 200 req/s em `/pdv/attempt-coupon` mantendo p95 < 120ms com índice `(code_hash)`.

---

## 14) Roadmap funcional (ordem sugerida)

1. **MVP PDV**: pareamento, `attempt`/`redeem` com tipos BRL/%.
2. **Marketplace básico**: login, carteira, listar ofertas, `buy`.
3. **Admin**: CRUD tenant + ofertas; inventário; relatórios simples.
4. **Pontos por pedido** e regras hierárquicas.
5. **Segmentação, assets, catálogo SKU**, emissão em massa.
6. **Observabilidade avançada** e automações.

---

### Fechamento

Com os módulos, APIs, fluxos, políticas de segurança, observabilidade e tabelas auxiliares acima, os três front-ends (**Marketplace**, **PDV** e **Admin**) podem ser implementados integralmente sobre **PostgreSQL + FastAPI + JS/React**, mantendo isolamento multi-tenant, integridade de inventário, idempotência nas operações críticas e ótima experiência de uso.
