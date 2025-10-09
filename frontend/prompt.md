# Prompt detalhado para frontend em Next.js + TypeScript para Sistema de Fidelidade

> **Objetivo:** você é um(a) engenheiro(a) front-end sênior. Gere um app em **Next.js (>=14, App Router)** com **TypeScript estrito**, **TailwindCSS** e **shadcn/ui**, implementando as telas e fluxos abaixo. Siga os padrões de código, acessibilidade e testes descritos.
> **Contexto do produto**: Sistema de fidelidade e cupons com gerenciamento de pontos, ofertas e descontos. O sistema suporta múltiplos tenants (Customer → Franchise → Store), controle de acesso baseado em perfis e diferentes pontos de acesso: Marketplace (usuários finais), PDV (Ponto de Venda) e Admin. As APIs principais incluem gestão de carteira de pontos, emissão/resgate de cupons, cálculo de pontos por pedido e validação de cupons no PDV.
> **Escopos**: `marketplace`, `pdv` (POS) e `admin`.

---

## Regras não-negociáveis

1. **Next.js (App Router)**, **TypeScript `strict: true`**, **ESLint + Prettier**, **Tailwind** configurado.
2. **Componentes server-first**. Use **RSC** quando possível; client components só quando necessário (estado/efeitos/eventos).
3. **Dados**: `fetch` nativo com **server actions** e **revalidação** (`cache`, `next.revalidate`) OU **TanStack Query** nos clients.
4. **Forms**: `react-hook-form` + **Zod** para *schema validation* e *type inference*.
5. **UI**: **shadcn/ui** (Button, Input, Card, Dialog, Sheet, Toaster), ícones **lucide-react**.
6. **Acessibilidade**: WAI-ARIA, foco visível, labels, leitura por screen reader, conserte contrastes.
7. **i18n**: `next-intl` com `pt` default e pronto p/ `en`.
8. **Estado**: preferir **server state**. Para client state global, usar **Zustand** somente quando justificar.
9. **Teste**: **Vitest + Testing Library** (unit/integration) e **Playwright** (E2E básico).
10. **Segurança**: nunca expor segredos no client, sanitize HTML, tratar erros e estados vazios, loading e skeletons.
11. **Aderir ao design system**: tokens Tailwind, espaçamentos, tipografia e cores consistentes.

---

## Estrutura do projeto

Crie um monorepo simples ou um único app com *route groups*:

```
/src
  /app
    /(public)             # rotas públicas
    /(marketplace)        # /marketplace/*
    /(pdv)                # /pdv/*
    /(admin)              # /admin/*
    /api                  # route handlers opcional (se usar Next API)
    layout.tsx
    globals.css
  /components             # UI compartilhada (server/client)
  /features               # domínios (wallet, offers, coupons, auth, rules, stores...)
  /lib
    api-client.ts         # wrapper de fetch, interceptors, cookies/JWT
    zod-schemas.ts
    auth.ts               # helpers (getSession, withRole)
    formatters.ts
  /providers              # QueryProvider, IntlProvider, ThemeProvider
  /styles                 # tailwind config helpers
  /types                  # tipos globais (d.ts)
  /tests
```

**Config**:

* `tsconfig.json`: `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `exactOptionalPropertyTypes`.
* `next.config.mjs`: imagens remotas permitidas; `experimental.serverActions` habilitado.
* `eslint`: `@next/eslint-plugin-next`, `unused-imports`.
* `tailwind.config.ts`: `shadcn` preset, escala de cores acessíveis.

---

## Conexão com APIs

### Convenção de cliente HTTP

* `lib/api-client.ts` exporta:

  * `apiFetch<T>(path, { method, body, headers, cache, next }): Promise<T>`
  * injeta `Authorization: Bearer {accessToken}` usando cookies.
  * trata erros com `ProblemDetails` (`status`, `title`, `detail`, `errors?`).

### Tipos e validações

* Para cada resposta de API, declare **Zod schema** baseado nas APIs disponíveis:

  ```typescript
  // Exemplo baseado nas APIs reais do sistema
  export const PointBalanceSchema = z.object({
    scope: z.enum(["GLOBAL", "CUSTOMER", "FRANCHISE", "STORE"]),
    scope_id: z.string().uuid().nullable(),
    points: z.number().int(),
    as_brl: z.number().nullable()
  });
  
  export const CouponBalanceSchema = z.object({
    offer_id: z.string().uuid(),
    available_count: z.number().int(),
    redeemed_count: z.number().int()
  });
  
  export const WalletResponseSchema = z.object({
    balances: z.array(PointBalanceSchema),
    coupons: z.array(CouponBalanceSchema)
  });
  
  export type WalletResponse = z.infer<typeof WalletResponseSchema>;
  ```

### Caching e revalidação

* Para listas públicas (ex.: ofertas), use `fetch` **em Server Components** com `next: { revalidate: 60 }`.
* Para dados do usuário (carteira), desabilite cache (`no-store`) ou invalide via **server action**.

---

## Rotas e telas a implementar

### (marketplace)

* `/marketplace` — **Home**: grade de ofertas (cards com imagem, título, preço/benefício, *badge* "poucas unidades").

  * Filtros: busca, escopo (customer/franchise/store), categoria.
  * Conectar à API `/offers?scope=&scope_id=&active=true&search=&page=&page_size=`
* `/marketplace/offers/[id]` — **Detalhe da oferta**: assets, regras, validade; CTA **"Obter cupom"**.
  * Conectar à API `/offers/{id}`
* `/marketplace/wallet` — **Carteira**:

  * Aba **Pontos**: saldos por escopo, *toggle* "BRL/points".
    * Conectar à API `/wallet?display_as=points|brl`
  * Aba **Cupons**: emitidos e resgatados; ação "Ver código/QR" (exibir apenas se a API retornar o *one-time code*).
    * Conectar às APIs `/coupons/my` e `/coupons/buy`
* `/signin` / `/signup` — autenticação (e-mail/CPF, magic link opcional).
  * Implementar usando APIs `/auth/register` e `/auth/login`

### (pdv)

* `/pdv` — tela com **pareamento** (inserir registration code → salva `deviceToken`).
  * Conectar à API `/auth/pdv/register-device`
* `/pdv/redeem` — **Resgatar Cupom**:

  * Campo para QR/código → chama `attempt` e mostra **valor do desconto** + status.
    * Conectar à API `/pdv/attempt-coupon`
  * Botão **Confirmar Resgate** (usa `Idempotency-Key`).
    * Conectar à API `/pdv/redeem`
* `/pdv/earn` — **Acumular pontos**:

  * Form do pedido (itens, total, CPF).
  * Submete para `/pdv/earn-points`; renderiza pontos ganhos e saldo.

### (admin)

* `/admin` — dashboard: KPIs (ofertas ativas, cupons emitidos/resgatados, pontos do período).
* `/admin/stores`, `/admin/franchises`, `/admin/users` — CRUD básico com tabelas (DataTable) + filtros.
* `/admin/offers` — lista de **CouponOffers** (status, estoque, janela).
* `/admin/offers/new` e `/admin/offers/[id]` — wizard com:

  * Tipo do cupom (BRL/%/FREE\_SKU), janela de validade, limite por cliente, estoque inicial, segmentação JSON.
  * Upload de assets (url assinado).
* `/admin/rules` — **Point Rules** por escopo (form com preview de cálculo).
* `/admin/devices` — gerar **registration code**, listar dispositivos ativos.

---

## Schemas Zod principais baseados na API

Com base na API real, implemente os seguintes schemas:

```typescript
// Auth schemas
export const TokenSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string()
});

// Offers schemas
export const CouponTypeSchema = z.object({
  id: z.string().uuid(),
  redeem_type: z.enum(["BRL", "PERCENTAGE", "FREE_SKU"]),
  discount_amount_brl: z.number().nullable(),
  discount_amount_percentage: z.number().nullable(),
  sku_specific: z.boolean(),
  valid_skus: z.array(z.string()).nullable()
});

export const AssetSchema = z.object({
  id: z.string().uuid(),
  kind: z.enum(["BANNER", "THUMB", "DETAIL"]),
  url: z.string()
});

export const OfferSchema = z.object({
  id: z.string().uuid(),
  entity_scope: z.enum(["CUSTOMER", "FRANCHISE", "STORE"]),
  entity_id: z.string().uuid(),
  initial_quantity: z.number().int(),
  current_quantity: z.number().int(),
  max_per_customer: z.number().int(),
  is_active: z.boolean(),
  start_at: z.string().nullable(),
  end_at: z.string().nullable(),
  coupon_type: CouponTypeSchema,
  assets: z.array(AssetSchema)
});

// Coupon schemas
export const BuyCouponRequestSchema = z.object({
  offer_id: z.string().uuid()
});

export const BuyCouponResponseSchema = z.object({
  coupon_id: z.string().uuid(),
  code: z.string(),
  qr: z.object({
    format: z.string(),
    data: z.string()
  })
});

// PDV schemas
export const AttemptCouponRequestSchema = z.object({
  code: z.string(),
  order_total_brl: z.number(),
  items: z.array(z.object({
    sku_id: z.string().optional(),
    name: z.string(),
    qty: z.number(),
    price: z.number()
  })).optional(),
  store_id: z.string().uuid()
});

export const AttemptCouponResponseSchema = z.object({
  coupon_id: z.string().uuid(),
  redeemable: z.boolean(),
  discount: z.object({
    type: z.string(),
    amount_brl: z.number().optional(),
    percentage: z.number().optional()
  }).nullable(),
  message: z.string().nullable()
});

export const RedeemCouponRequestSchema = z.object({
  coupon_id: z.string().uuid(),
  order_id: z.string().optional(),
  order: z.record(z.any()).optional()
});

export const EarnPointsRequestSchema = z.object({
  person_id: z.string().uuid().optional(),
  cpf: z.string().optional(),
  order: z.object({
    total_brl: z.number(),
    tax_brl: z.number().optional(),
    items: z.array(z.any()).optional()
  }),
  store_id: z.string().uuid()
});
```

---

## Padrões de componentes

* **Server components** para páginas e listas públicas:

  ```tsx
  // app/(marketplace)/page.tsx
  import { OfferCard } from "@/components/offer-card";
  
  export default async function Page({ 
    searchParams 
  }: { 
    searchParams: { scope?: string; scope_id?: string; search?: string; page?: string } 
  }) {
    const scope = searchParams.scope;
    const scope_id = searchParams.scope_id;
    const search = searchParams.search;
    const page = parseInt(searchParams.page || "1", 10);
    
    const offers = await apiFetch<OffersResponse>(
      `/offers?scope=${scope || ""}&scope_id=${scope_id || ""}&active=true&search=${search || ""}&page=${page}&page_size=10`, 
      { next: { revalidate: 60 }}
    );
    
    return (
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-6">Ofertas disponíveis</h1>
        <OfferFilters />
        <OfferGrid offers={offers.items} />
        <Pagination 
          currentPage={page} 
          totalPages={offers.pages} 
          baseUrl="/marketplace" 
        />
      </div>
    );
  }
  ```
