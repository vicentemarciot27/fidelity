'use client';

import Link from 'next/link';
import type { CouponOffer } from '../../lib/api-types';

type OfferCardProps = {
  offer: CouponOffer;
};

export function OfferCard({ offer }: OfferCardProps) {
  const discountLabel = getDiscountLabel(offer);
  const lowInventory = offer.current_quantity <= 10;

  return (
    <div className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
          <span>{offer.entity_scope}</span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
            {offer.coupon_type.redeem_type}
          </span>
        </div>
        <h3 className="text-lg font-semibold text-slate-900">
          {discountLabel.title}
        </h3>
        <p className="text-sm text-slate-600">{discountLabel.subtitle}</p>
        {offer.start_at || offer.end_at ? (
          <p className="text-xs text-slate-500">
            {offer.start_at ? formatDateRange(offer.start_at) : 'Starts immediately'}
            {offer.end_at ? ` • Ends ${formatDateRange(offer.end_at)}` : ''}
          </p>
        ) : null}
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <span>
            Stock: <strong>{offer.current_quantity}</strong>
          </span>
          {lowInventory ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
              Low stock
            </span>
          ) : null}
        </div>
      </div>

      <Link
        href={`/marketplace/offers/${offer.id}`}
        className="mt-6 inline-flex h-10 items-center justify-center rounded-md border border-slate-300 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
      >
        View details
      </Link>
    </div>
  );
}

function getDiscountLabel(offer: CouponOffer) {
  const type = offer.coupon_type;
  if (type.redeem_type === 'BRL' && type.discount_amount_brl) {
    return {
      title: `R$ ${type.discount_amount_brl.toFixed(2)} off`,
      subtitle: 'Fixed amount discount at redemption.',
    };
  }

  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage) {
    return {
      title: `${type.discount_amount_percentage}% back`,
      subtitle: 'Percentage discount applied to the order.',
    };
  }

  if (type.redeem_type === 'FREE_SKU') {
    return {
      title: 'Free selected SKU',
      subtitle: type.valid_skus
        ? `Valid for SKUs: ${type.valid_skus.join(', ')}`
        : 'Free SKU promotion.',
    };
  }

  return {
    title: 'Coupon offer',
    subtitle: 'See full details to learn more.',
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

