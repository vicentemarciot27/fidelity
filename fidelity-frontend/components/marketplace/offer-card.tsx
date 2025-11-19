'use client';

import Link from 'next/link';
import type { CouponOffer } from '../../lib/api-types';
import { useEntityName } from '../../hooks/use-entity-names';

type OfferCardProps = {
  offer: CouponOffer;
};

export function OfferCard({ offer }: OfferCardProps) {
  const discountLabel = getDiscountLabel(offer);
  const lowInventory = offer.current_quantity <= 10;
  const scopeBadgeConfig = getScopeBadgeConfig(offer.entity_scope);
  const { entityName, isLoading: loadingName } = useEntityName(offer.entity_scope, offer.entity_id);

  return (
    <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition group">
      <div className="flex flex-col gap-4">
        {/* Header com ícone e badges */}
        <div className="flex items-start gap-4">
          {/* Ícone da oferta */}
          <div className={`${scopeBadgeConfig.bg} ${scopeBadgeConfig.text} p-3 rounded-xl`}>
            {offer.entity_scope === 'CUSTOMER' && (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            )}
            {offer.entity_scope === 'FRANCHISE' && (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            )}
            {offer.entity_scope === 'STORE' && (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            )}
          </div>
          
          {/* Badges e nome */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`${scopeBadgeConfig.bg} ${scopeBadgeConfig.text} px-2.5 py-1 rounded-full text-xs font-semibold`}>
                {scopeBadgeConfig.label}
              </span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                {getRedeemTypeLabel(offer.coupon_type.redeem_type)}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 truncate">
              {loadingName ? 'Carregando...' : (entityName || offer.entity_id)}
            </h3>
          </div>
        </div>
        
        <div className="border-t border-slate-100 pt-4">
          <h4 className="text-xl font-bold text-slate-900 mb-2">
            {discountLabel.title}
          </h4>
          <p className="text-sm text-slate-600">{discountLabel.subtitle}</p>
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-600">
          <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-3.866 0-7 1.79-7 4s3.134 4 7 4 7-1.79 7-4-3.134-4-7-4zm0 0V4m0 12v4" />
          </svg>
          <span>
            {offer.points_cost > 0
              ? `${formatPoints(offer.points_cost)} pts para emitir`
              : 'Sem custo em pontos'}
          </span>
        </div>

        {offer.start_at || offer.end_at ? (
          <div className="text-xs text-slate-500 flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {offer.start_at ? formatDateRange(offer.start_at) : 'Inicia imediatamente'}
            {offer.end_at ? ` • Termina ${formatDateRange(offer.end_at)}` : ''}
          </div>
        ) : null}
        
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-1.5 text-slate-600">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <span>
              Estoque: <strong className="text-slate-900">{offer.current_quantity}</strong>
            </span>
          </div>
          {lowInventory ? (
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
              Estoque baixo
            </span>
          ) : null}
        </div>
      </div>

      <Link
        href={`/marketplace/offers/${offer.id}`}
        className="mt-6 inline-flex h-11 items-center justify-center rounded-lg bg-slate-900 text-sm font-medium text-white transition hover:bg-slate-800"
      >
        Ver detalhes
      </Link>
    </div>
  );
}

function getScopeBadgeConfig(scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE') {
  switch (scope) {
    case 'CUSTOMER':
      return {
        label: 'Rede',
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

function getDiscountLabel(offer: CouponOffer) {
  const type = offer.coupon_type;
  if (type.redeem_type === 'BRL' && type.discount_amount_brl) {
    return {
      title: `R$ ${type.discount_amount_brl.toFixed(2)} de desconto`,
      subtitle: 'Desconto em valor fixo no resgate.',
    };
  }

  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage) {
    return {
      title: `${type.discount_amount_percentage}% de desconto`,
      subtitle: 'Desconto percentual aplicado ao pedido.',
    };
  }

  if (type.redeem_type === 'FREE_SKU') {
    return {
      title: 'Produto Grátis',
      subtitle: type.valid_skus
        ? `Válido para SKUs: ${type.valid_skus.join(', ')}`
        : 'Promoção de produto grátis.',
    };
  }

  return {
    title: 'Oferta de cupom',
    subtitle: 'Veja os detalhes completos para saber mais.',
  };
}

function formatDateRange(value: string) {
  const date = new Date(value);
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatPoints(value: number) {
  return new Intl.NumberFormat('pt-BR').format(value);
}

