'use client';

import { useState } from 'react';
import { Protected } from '../../../components/auth/protected';
import { CouponOfferForm } from '../../../components/admin/coupon-offer-form';
import { CouponTypeForm } from '../../../components/admin/coupon-type-form';
import { useAuth } from '../../../components/providers/auth-provider';
import {
  useAdminCouponOffers,
} from '../../../hooks/use-admin-coupon-offers';
import { useAdminCouponTypes } from '../../../hooks/use-admin-coupon-types';
import { useAdminOfferDetail } from '../../../hooks/use-admin-offer-detail';
import { ADMIN_ROLES } from '../../../lib/roles';
import type { AdminCouponType } from '../../../lib/api-types';

export default function AdminPortalPage() {
  const { user } = useAuth();
  const [typesPage] = useState(1);
  const [offersPage, setOffersPage] = useState(1);
  const [scopeFilter, setScopeFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>(
    'active',
  );
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(null);

  const {
    couponTypes,
    refresh: refreshCouponTypes,
    isLoading: typesLoading,
  } = useAdminCouponTypes(typesPage, 10);
  const {
    couponOffers,
    refresh: refreshCouponOffers,
    isLoading: offersLoading,
  } = useAdminCouponOffers({
    entity_scope: scopeFilter || undefined,
    is_active:
      activeFilter === 'all'
        ? undefined
        : activeFilter === 'active'
        ? true
        : false,
    page: offersPage,
    page_size: 10,
  });

  const {
    offer: selectedOffer,
    stats: selectedStats,
    isLoading: detailLoading,
  } = useAdminOfferDetail(selectedOfferId);

  const couponTypeItems = couponTypes?.items ?? [];
  const couponOfferItems = couponOffers?.items ?? [];

  return (
    <Protected roles={ADMIN_ROLES}>
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="flex flex-col gap-8">
            <header className="flex flex-col gap-2">
              <h1 className="text-3xl font-bold text-slate-900">
                Painel Administrativo
              </h1>
              <p className="text-base text-slate-600">
                Gerencie tipos de cupons, publique ofertas e monitore o estoque. 
                Logado como <strong className="font-semibold text-slate-900">{user?.role}</strong>
              </p>
            </header>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">
                  Criar Tipo de Cupom
                </h2>
                <p className="mt-2 text-sm text-slate-600">
                  Defina como os descontos funcionam. Esses tipos podem ser reutilizados em múltiplas ofertas.
                </p>
                <div className="mt-6">
                  <CouponTypeForm onCreated={refreshCouponTypes} />
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">
                  Publicar Oferta de Cupom
                </h2>
                <p className="mt-2 text-sm text-slate-600">
                  Direcione para lojas, franquias ou todo o cliente. O estoque inicia na quantidade inicial e diminui conforme cupons são emitidos.
                </p>
                <div className="mt-6">
                  <CouponOfferForm
                    couponTypes={couponTypeItems}
                    onCreated={() => {
                      refreshCouponOffers();
                      refreshCouponTypes();
                    }}
                  />
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">
                    Tipos de Cupons
                  </h2>
                  <p className="text-sm text-slate-600 mt-1">
                    Visão geral das definições de desconto reutilizáveis.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={refreshCouponTypes}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Atualizar
                </button>
              </div>

              {typesLoading ? (
                <Placeholder message="Carregando tipos de cupons..." />
              ) : couponTypeItems.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                    <thead className="bg-slate-50">
                      <tr className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                        <th className="px-4 py-3">Tipo</th>
                        <th className="px-4 py-3">SKU Específico</th>
                        <th className="px-4 py-3">Desconto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {couponTypeItems.map((type) => (
                        <tr key={type.id} className="hover:bg-slate-50 transition">
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {type.redeem_type === 'BRL'
                              ? 'Desconto (R$)'
                              : type.redeem_type === 'PERCENTAGE'
                              ? 'Desconto (%)'
                              : type.redeem_type === 'FREE_SKU'
                              ? 'SKU Grátis'
                              : type.redeem_type
                            }
                          </td>
                          <td className="px-4 py-3 text-slate-600">{type.sku_specific ? 'Sim' : 'Não'}</td>
                          <td className="px-4 py-3 text-slate-600">
                            {formatDiscount(type)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Placeholder message="Nenhum tipo de cupom criado ainda." />
              )}
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">
                    Ofertas de Cupons
                  </h2>
                  <p className="text-sm text-slate-600 mt-1">
                    Filtre por escopo ou status para focar em campanhas ativas.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <select
                    value={scopeFilter}
                    onChange={(event) => {
                      setScopeFilter(event.target.value);
                      setOffersPage(1);
                    }}
                    className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  >
                    <option value="">Todos escopos</option>
                    <option value="CUSTOMER">Cliente</option>
                    <option value="FRANCHISE">Franquia</option>
                    <option value="STORE">Loja</option>
                  </select>
                  <select
                    value={activeFilter}
                    onChange={(event) => {
                      setActiveFilter(event.target.value as typeof activeFilter);
                      setOffersPage(1);
                    }}
                    className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  >
                    <option value="all">Todos</option>
                    <option value="active">Ativos</option>
                    <option value="inactive">Inativos</option>
                  </select>
                  <button
                    type="button"
                    onClick={refreshCouponOffers}
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50"
                  >
                    Atualizar
                  </button>
                </div>
              </div>

              {offersLoading ? (
                <Placeholder message="Carregando ofertas..." />
              ) : couponOfferItems.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                    <thead className="bg-slate-50">
                      <tr className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                        <th className="px-4 py-3">Escopo</th>
                        <th className="px-4 py-3">Estoque</th>
                        <th className="px-4 py-3">Custo</th>
                        <th className="px-4 py-3">Janela</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {couponOfferItems.map((offer) => (
                        <tr key={offer.id} className="hover:bg-slate-50 transition">
                          <td className="px-4 py-3">
                            <div className="font-medium text-slate-900">
                              {offer.entity_scope === 'CUSTOMER'
                                ? 'Cliente'
                                : offer.entity_scope === 'FRANCHISE'
                                ? 'Franquia'
                                : offer.entity_scope === 'STORE'
                                ? 'Loja'
                                : offer.entity_scope}
                            </div>
                            <div className="text-xs text-slate-500">{offer.entity_id}</div>
                          </td>
                          <td className="px-4 py-3 text-slate-600 font-medium">
                            {offer.current_quantity}/{offer.initial_quantity}
                          </td>
                          <td className="px-4 py-3 text-slate-600">
                            {offer.points_cost > 0
                              ? `${formatPoints(offer.points_cost)} pts`
                              : 'Grátis'}
                          </td>
                          <td className="px-4 py-3 text-slate-600 text-xs">
                            {formatWindow(offer.start_at, offer.end_at)}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${offer.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}
                            >
                              {offer.is_active ? 'Ativo' : 'Inativo'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              type="button"
                              onClick={() => setSelectedOfferId(offer.id)}
                              className="text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline"
                            >
                              Ver detalhes
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Placeholder message="Nenhuma oferta de cupom publicada ainda." />
              )}

              {couponOffers?.pages && couponOffers.pages > 1 ? (
                <div className="mt-6 flex items-center justify-end gap-3 text-sm">
                  <button
                    type="button"
                    disabled={offersPage === 1}
                    onClick={() => setOffersPage((prev) => Math.max(prev - 1, 1))}
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Anterior
                  </button>
                  <span className="text-slate-600">
                    Página <strong className="text-slate-900">{offersPage}</strong> de {couponOffers.pages}
                  </span>
                  <button
                    type="button"
                    disabled={offersPage === couponOffers.pages}
                    onClick={() =>
                      setOffersPage((prev) =>
                        couponOffers ? Math.min(prev + 1, couponOffers.pages) : prev,
                      )
                    }
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Próxima
                  </button>
                </div>
              ) : null}
            </section>

            {selectedOfferId ? (
              <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">
                      Métricas da Oferta
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                      Estoque em tempo real e tendências de resgate para{' '}
                      <code className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700">
                        {selectedOfferId}
                      </code>
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setSelectedOfferId(null)}
                      className="text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      Fechar
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedOfferId(selectedOfferId)}
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Atualizar
                    </button>
                  </div>
                </div>

                {detailLoading ? (
                  <Placeholder message="Carregando estatísticas da oferta..." />
                ) : selectedOffer && selectedStats ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Metric label="Quantidade inicial" value={selectedOffer.initial_quantity} />
                    <Metric label="Quantidade atual" value={selectedOffer.current_quantity} />
                    <Metric
                      label="Custo em pontos"
                      value={
                        selectedOffer.points_cost > 0
                          ? `${formatPoints(selectedOffer.points_cost)} pts`
                          : 'Grátis'
                      }
                    />
                    <Metric label="Status" value={selectedOffer.is_active ? 'Ativa' : 'Inativa'} />
                    <Metric
                      label="Janela de resgate"
                      value={formatWindow(selectedOffer.start_at, selectedOffer.end_at)}
                    />
                    <Metric label="Emitidos" value={selectedStats.total_issued} />
                    <Metric label="Reservados" value={selectedStats.total_reserved} />
                    <Metric label="Resgatados" value={selectedStats.total_redeemed} />
                    <Metric label="Expirados" value={selectedStats.total_expired} />
                  </div>
                ) : (
                  <Placeholder message="Não foi possível carregar as métricas desta oferta." />
                )}
              </section>
            ) : null}
          </div>
        </div>
      </div>
    </Protected>
  );
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatPoints(value: number) {
  return new Intl.NumberFormat('pt-BR').format(value);
}

function formatDiscount(type: AdminCouponType) {
  if (type.redeem_type === 'BRL' && type.discount_amount_brl !== null) {
    return `R$ ${Number(type.discount_amount_brl).toFixed(2)}`;
  }
  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage !== null) {
    return `${Number(type.discount_amount_percentage)}%`;
  }
  if (type.redeem_type === 'FREE_SKU') {
    return (type.valid_skus ?? []).join(', ') || 'Produto Grátis Selecionado';
  }
  return 'N/A';
}

function formatWindow(start: string | null, end: string | null) {
  const startText = start ? new Date(start).toLocaleString('pt-BR', { 
    day: '2-digit', 
    month: 'short', 
    hour: '2-digit', 
    minute: '2-digit' 
  }) : 'Imediato';
  const endText = end ? new Date(end).toLocaleString('pt-BR', { 
    day: '2-digit', 
    month: 'short', 
    hour: '2-digit', 
    minute: '2-digit' 
  }) : 'Sem prazo';
  return `${startText} → ${endText}`;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 from-slate-50 to-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">{label}</p>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

