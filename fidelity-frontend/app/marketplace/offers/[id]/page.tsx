'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Protected } from '../../../../components/auth/protected';
import { useAuth } from '../../../../components/providers/auth-provider';
import { ApiError, apiFetch } from '../../../../lib/api-client';
import { isAdminRole } from '../../../../lib/roles';
import { useOfferDetail } from '../../../../hooks/use-offer-detail';
import { useEntityName } from '../../../../hooks/use-entity-names';
import type { BuyCouponResponse } from '../../../../lib/api-types';
import { showToast } from '../../../../components/ui/toast';

export default function OfferDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const offerId = params?.id ?? '';
  const shouldGenerate = searchParams.get('generate') === 'true';
  const { offer, error, isLoading, refresh } = useOfferDetail(offerId);
  const { user } = useAuth();
  const [purchaseResult, setPurchaseResult] = useState<BuyCouponResponse | null>(null);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const { entityName, isLoading: loadingName } = useEntityName(
    offer?.entity_scope || 'CUSTOMER',
    offer?.entity_id || ''
  );

  const canBuy = Boolean(user?.personId) && !isAdminRole(user?.role ?? null);

  const handleBuyCoupon = async () => {
    if (!offer) return;
    setIsPurchasing(true);
    setPurchaseError(null);

    try {
      const response = await apiFetch<BuyCouponResponse>('/coupons/buy', 'POST', {
        offer_id: offer.id,
      });
      setPurchaseResult(response);
      showToast('Coupon issued successfully!', 'success');
      await refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = (err.body as { detail?: string })?.detail;
        const errorMsg = detail ?? 'Failed to issue coupon.';
        setPurchaseError(errorMsg);
        showToast(errorMsg, 'error');
      } else {
        const errorMsg = 'Unexpected error while issuing the coupon.';
        setPurchaseError(errorMsg);
        showToast(errorMsg, 'error');
      }
    } finally {
      setIsPurchasing(false);
    }
  };

  // Auto-generate coupon if coming from wallet
  useEffect(() => {
    if (shouldGenerate && offer && canBuy && !purchaseResult && !isPurchasing) {
      handleBuyCoupon();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldGenerate, offer, canBuy]);

  const scopeBadgeConfig = offer ? getScopeBadgeConfig(offer.entity_scope) : null;

  return (
    <Protected>
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-4xl px-6 py-10">
          <div className="flex flex-col gap-6">
            <Link
              href="/marketplace/dashboard"
              className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Voltar para ofertas
            </Link>

            {isLoading ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-base text-slate-500">
                Carregando oferta...
              </div>
            ) : error ? (
              <div className="rounded-xl border border-rose-300 bg-rose-50 p-8 text-base text-rose-700">
                Não foi possível carregar os detalhes da oferta. Tente novamente mais tarde.
              </div>
            ) : offer && scopeBadgeConfig ? (
              <article className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
                <header className="flex flex-col gap-4">
                  <div className="flex items-start gap-4 mb-4">
                    {/* Ícone grande */}
                    <div className={`${scopeBadgeConfig.bg} ${scopeBadgeConfig.text} p-4 rounded-2xl`}>
                      {offer.entity_scope === 'CUSTOMER' && (
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      )}
                      {offer.entity_scope === 'FRANCHISE' && (
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      )}
                      {offer.entity_scope === 'STORE' && (
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`${scopeBadgeConfig.bg} ${scopeBadgeConfig.text} px-3 py-1.5 rounded-full text-xs font-semibold`}>
                          {scopeBadgeConfig.label}
                        </span>
                        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600">
                          {getRedeemTypeLabel(offer.coupon_type.redeem_type)}
                        </span>
                        {offer.is_active && (
                          <span className="rounded-full bg-green-100 px-3 py-1.5 text-xs font-semibold text-green-700">
                            Ativa
                          </span>
                        )}
                      </div>
                      <p className="text-lg font-semibold text-slate-600 mb-1">
                        {loadingName ? 'Carregando...' : (entityName || offer.entity_id)}
                      </p>
                    </div>
                  </div>
                  <h1 className="text-4xl font-bold text-slate-900 mb-2">
                    {offer.coupon_type.redeem_type === 'BRL' && offer.coupon_type.discount_amount_brl
                      ? `R$ ${offer.coupon_type.discount_amount_brl.toFixed(2)} de desconto`
                      : offer.coupon_type.redeem_type === 'PERCENTAGE' &&
                          offer.coupon_type.discount_amount_percentage
                        ? `${offer.coupon_type.discount_amount_percentage}% de desconto`
                        : 'Oferta de cupom'}
                  </h1>
                  <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <span>
                        Estoque: <strong className="text-slate-900">{offer.current_quantity}</strong> / {offer.initial_quantity}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span>
                        Limite por cliente: <strong className="text-slate-900">{offer.max_per_customer === 0 ? 'Ilimitado' : offer.max_per_customer}</strong>
                      </span>
                    </div>
                  </div>
                </header>

                {offer.assets.length > 0 ? (
                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {offer.assets.map((asset) => (
                      <div key={asset.id} className="overflow-hidden rounded-xl border border-slate-200 shadow-sm">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={asset.url}
                          alt={`${asset.kind} asset`}
                          className="h-48 w-full object-cover"
                        />
                      </div>
                    ))}
                  </div>
                ) : null}

                <section className="mt-8 pt-6 border-t border-slate-200">
                  <h2 className="text-xl font-bold text-slate-900 mb-4">Detalhes da Oferta</h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">ID da Entidade</p>
                      <p className="text-sm font-mono text-slate-900">{offer.entity_id}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Criada em</p>
                      <p className="text-sm text-slate-900">{formatTimestamp(offer.created_at)}</p>
                    </div>
                    {offer.start_at && (
                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Inicia em</p>
                        <p className="text-sm text-slate-900">{formatTimestamp(offer.start_at)}</p>
                      </div>
                    )}
                    {offer.end_at && (
                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Termina em</p>
                        <p className="text-sm text-slate-900">{formatTimestamp(offer.end_at)}</p>
                      </div>
                    )}
                    {offer.coupon_type.valid_skus?.length && (
                      <div className="rounded-lg bg-slate-50 p-4 sm:col-span-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">SKUs Válidos</p>
                        <p className="text-sm text-slate-900">{offer.coupon_type.valid_skus.join(', ')}</p>
                      </div>
                    )}
                  </div>
                </section>

                {purchaseError ? (
                  <div className="mt-6 rounded-xl border border-rose-300 bg-rose-50 p-4 text-sm text-rose-700">
                    <strong className="font-semibold">Erro:</strong> {purchaseError}
                  </div>
                ) : null}

                {purchaseResult ? (
                  <section className="mt-6 rounded-xl border border-green-300 bg-green-50 p-6">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h2 className="text-xl font-bold text-green-900">
                        Cupom emitido com sucesso!
                      </h2>
                    </div>
                    <p className="text-sm text-green-800 mb-4">
                      Apresente este código no checkout ou escaneie o QR code abaixo.
                    </p>
                    <div className="flex flex-wrap items-center gap-6">
                      <div className="rounded-lg bg-white border-2 border-green-300 px-6 py-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Código do Cupom</p>
                        <p className="text-2xl font-bold text-slate-900 font-mono">
                          {purchaseResult.code}
                        </p>
                      </div>
                      {purchaseResult.qr?.data ? (
                        <div className="rounded-lg bg-white border-2 border-green-300 p-3">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={purchaseResult.qr.data}
                            alt="QR code do cupom"
                            className="h-32 w-32"
                          />
                        </div>
                      ) : null}
                    </div>
                  </section>
                ) : (
                  <button
                    type="button"
                    disabled={!canBuy || isPurchasing || offer.current_quantity <= 0}
                    onClick={handleBuyCoupon}
                    className="mt-8 w-full inline-flex h-12 items-center justify-center rounded-lg bg-slate-900 px-6 text-base font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isPurchasing ? 'Emitindo cupom...' : offer.current_quantity <= 0 ? 'Estoque esgotado' : canBuy ? 'Obter cupom' : 'Login necessário'}
                  </button>
                )}
              </article>
            ) : null}
          </div>
        </div>
      </div>
    </Protected>
  );
}

function getScopeBadgeConfig(scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE') {
  switch (scope) {
    case 'CUSTOMER':
      return {
        label: 'Cliente',
        bg: 'bg-blue-100',
        text: 'text-blue-700',
      };
    case 'FRANCHISE':
      return {
        label: 'Franquia',
        bg: 'bg-purple-100',
        text: 'text-purple-700',
      };
    case 'STORE':
      return {
        label: 'Loja',
        bg: 'bg-green-100',
        text: 'text-green-700',
      };
  }
}

function getRedeemTypeLabel(type: 'BRL' | 'PERCENTAGE' | 'FREE_SKU') {
  switch (type) {
    case 'BRL':
      return 'Desconto R$';
    case 'PERCENTAGE':
      return 'Desconto %';
    case 'FREE_SKU':
      return 'Produto Grátis';
  }
}

function formatTimestamp(value: string | undefined) {
  if (!value) return '-';
  const date = new Date(value);
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

