'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Protected } from '../../../components/auth/protected';
import { useMyCoupons } from '../../../hooks/use-my-coupons';
import { useEntityName } from '../../../hooks/use-entity-names';
import type { MyCouponWithCode } from '../../../lib/api-types';

export default function MyCouponsPage() {
  const searchParams = useSearchParams();
  const offerId = searchParams?.get('offer_id') || undefined;
  const { coupons, isLoading, refresh } = useMyCoupons(offerId);
  const [selectedCoupon, setSelectedCoupon] = useState<MyCouponWithCode | null>(null);

  return (
    <Protected>
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900">Meus Cupons</h1>
            <p className="mt-2 text-slate-600">
              Gerencie seus cupons e visualize os códigos QR para utilizar nas lojas
            </p>
          </div>

          {isLoading ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-base text-slate-500">
              Carregando cupons...
            </div>
          ) : coupons.length > 0 ? (
            <>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {coupons.map((coupon) => (
                  <CouponCard
                    key={coupon.id}
                    coupon={coupon}
                    onClick={() => setSelectedCoupon(coupon)}
                  />
                ))}
              </div>

              {/* Modal para exibir QR Code */}
              {selectedCoupon && (
                <CouponModal
                  coupon={selectedCoupon}
                  onClose={() => setSelectedCoupon(null)}
                />
              )}
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
              <svg
                className="mx-auto h-12 w-12 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-4 text-base text-slate-500">
                Você ainda não possui cupons disponíveis
              </p>
              <a
                href="/marketplace/dashboard"
                className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
              >
                Ver Ofertas
              </a>
            </div>
          )}
        </div>
      </div>
    </Protected>
  );
}

function CouponCard({
  coupon,
  onClick,
}: {
  coupon: MyCouponWithCode;
  onClick: () => void;
}) {
  const { entityName, isLoading } = useEntityName(
    coupon.offer.entity_scope,
    coupon.offer.entity_id
  );

  const discountLabel = getDiscountLabel(coupon);
  const statusInfo = getStatusInfo(coupon.status);

  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:shadow-lg hover:border-slate-300"
    >
      {/* Status Badge */}
      <div className="absolute right-4 top-4">
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${statusInfo.className}`}
        >
          {statusInfo.label}
        </span>
      </div>

      {/* Content */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-slate-900">
          {isLoading ? 'Carregando...' : entityName || 'Cupom de Desconto'}
        </h3>
        <p className="mt-1 text-sm text-slate-500">
          {coupon.offer.entity_scope === 'STORE'
            ? 'Válido na loja'
            : coupon.offer.entity_scope === 'FRANCHISE'
            ? 'Válido na franquia'
            : 'Válido na rede'}
        </p>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold text-blue-600">{discountLabel}</p>
          <p className="mt-1 text-xs text-slate-500">
            Emitido em {new Date(coupon.issued_at).toLocaleDateString('pt-BR')}
          </p>
        </div>
        <svg
          className="h-8 w-8 text-slate-400 transition group-hover:text-blue-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
          />
        </svg>
      </div>

      {/* Click indicator */}
      <p className="mt-4 text-center text-xs font-medium text-blue-600">
        Clique para ver o QR Code
      </p>
    </button>
  );
}

function CouponModal({
  coupon,
  onClose,
}: {
  coupon: MyCouponWithCode;
  onClose: () => void;
}) {
  const { entityName, isLoading } = useEntityName(
    coupon.offer.entity_scope,
    coupon.offer.entity_id
  );

  const discountLabel = getDiscountLabel(coupon);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="relative max-w-lg w-full rounded-2xl bg-white p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-900">
            {isLoading ? 'Carregando...' : entityName || 'Seu Cupom'}
          </h2>
          <p className="mt-2 text-lg font-semibold text-blue-600">{discountLabel}</p>
        </div>

        {/* QR Code */}
        <div className="my-8 flex justify-center">
          <div className="rounded-2xl border-4 border-slate-200 bg-white p-4">
            <img
              src={coupon.qr.data}
              alt="QR Code do Cupom"
              className="h-64 w-64"
            />
          </div>
        </div>

        {/* Coupon Code */}
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-center text-xs font-medium text-slate-600">Código do Cupom</p>
          <p className="mt-2 text-center font-mono text-lg font-bold text-slate-900">
            {coupon.code}
          </p>
        </div>

        {/* Instructions */}
        <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <p className="text-sm text-blue-900">
            <strong>Como usar:</strong> Apresente este QR Code ou código no caixa da loja
            para utilizar seu cupom de desconto.
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-6 w-full rounded-lg bg-slate-900 px-4 py-3 font-medium text-white transition hover:bg-slate-800"
        >
          Fechar
        </button>
      </div>
    </div>
  );
}

function getDiscountLabel(coupon: MyCouponWithCode): string {
  const type = coupon.coupon_type;
  if (type.redeem_type === 'BRL' && type.discount_amount_brl) {
    return `R$ ${type.discount_amount_brl.toFixed(2)} OFF`;
  }
  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage) {
    return `${type.discount_amount_percentage}% OFF`;
  }
  if (type.redeem_type === 'FREE_SKU') {
    return 'Produto Grátis';
  }
  return 'Desconto';
}

function getStatusInfo(status: string): { label: string; className: string } {
  switch (status) {
    case 'ISSUED':
      return {
        label: 'Disponível',
        className: 'bg-green-100 text-green-700',
      };
    case 'RESERVED':
      return {
        label: 'Reservado',
        className: 'bg-yellow-100 text-yellow-700',
      };
    case 'REDEEMED':
      return {
        label: 'Utilizado',
        className: 'bg-slate-100 text-slate-700',
      };
    case 'CANCELLED':
      return {
        label: 'Cancelado',
        className: 'bg-red-100 text-red-700',
      };
    case 'EXPIRED':
      return {
        label: 'Expirado',
        className: 'bg-slate-100 text-slate-600',
      };
    default:
      return {
        label: status,
        className: 'bg-slate-100 text-slate-700',
      };
  }
}

