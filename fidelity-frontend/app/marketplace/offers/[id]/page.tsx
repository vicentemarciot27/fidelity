'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { Protected } from '../../../../components/auth/protected';
import { useAuth } from '../../../../components/providers/auth-provider';
import { ApiError, apiFetch } from '../../../../lib/api-client';
import { isAdminRole } from '../../../../lib/roles';
import { useOfferDetail } from '../../../../hooks/use-offer-detail';
import type { BuyCouponResponse } from '../../../../lib/api-types';
import { showToast } from '../../../../components/ui/toast';

export default function OfferDetailPage() {
  const params = useParams<{ id: string }>();
  const offerId = params?.id ?? '';
  const { offer, error, isLoading, refresh } = useOfferDetail(offerId);
  const { user } = useAuth();
  const [purchaseResult, setPurchaseResult] = useState<BuyCouponResponse | null>(null);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);
  const [isPurchasing, setIsPurchasing] = useState(false);

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

  return (
    <Protected>
      <div className="flex flex-col gap-6">
        <Link
          href="/marketplace/dashboard"
          className="text-sm text-slate-600 underline decoration-slate-300 hover:text-slate-900"
        >
          ← Back to offers
        </Link>

        {isLoading ? (
          <div className="rounded-md border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
            Loading offer…
          </div>
        ) : error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
            Unable to load offer details. Try again later.
          </div>
        ) : offer ? (
          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <header className="flex flex-col gap-3">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
                <span>{offer.entity_scope}</span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                  {offer.coupon_type.redeem_type}
                </span>
              </div>
              <h1 className="text-2xl font-semibold text-slate-900">
                {offer.coupon_type.redeem_type === 'BRL' && offer.coupon_type.discount_amount_brl
                  ? `R$ ${offer.coupon_type.discount_amount_brl.toFixed(2)} discount`
                  : offer.coupon_type.redeem_type === 'PERCENTAGE' &&
                      offer.coupon_type.discount_amount_percentage
                    ? `${offer.coupon_type.discount_amount_percentage}% off`
                    : 'Coupon offer'}
              </h1>
              <p className="text-sm text-slate-500">
                Inventory: {offer.current_quantity} / {offer.initial_quantity} • Limit per customer:{' '}
                {offer.max_per_customer === 0 ? 'Unlimited' : offer.max_per_customer}
              </p>
            </header>

            {offer.assets.length > 0 ? (
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                {offer.assets.map((asset) => (
                  <div key={asset.id} className="overflow-hidden rounded-md border">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={asset.url}
                      alt={`${asset.kind} asset`}
                      className="h-36 w-full object-cover"
                    />
                  </div>
                ))}
              </div>
            ) : null}

            <section className="mt-6 flex flex-col gap-4">
              <h2 className="text-lg font-semibold text-slate-900">Details</h2>
              <ul className="space-y-2 text-sm text-slate-600">
                <li>Scope ID: {offer.entity_id}</li>
                <li>Offer created at: {formatTimestamp(offer.created_at)}</li>
                {offer.start_at ? <li>Starts: {formatTimestamp(offer.start_at)}</li> : null}
                {offer.end_at ? <li>Ends: {formatTimestamp(offer.end_at)}</li> : null}
                {offer.coupon_type.valid_skus?.length ? (
                  <li>Valid SKUs: {offer.coupon_type.valid_skus.join(', ')}</li>
                ) : null}
              </ul>
            </section>

            {purchaseError ? (
              <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                {purchaseError}
              </div>
            ) : null}

            {purchaseResult ? (
              <section className="mt-6 rounded-md border border-teal-200 bg-teal-50 p-4">
                <h2 className="text-lg font-semibold text-teal-900">
                  Coupon issued successfully!
                </h2>
                <p className="mt-1 text-sm text-teal-800">
                  Present this code at checkout or scan the QR below.
                </p>
                <div className="mt-4 flex flex-wrap items-center gap-6">
                  <div className="rounded-md bg-white px-3 py-2 text-lg font-semibold text-slate-900">
                    {purchaseResult.code}
                  </div>
                  {purchaseResult.qr?.data ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={purchaseResult.qr.data}
                      alt="Coupon QR code"
                      className="h-32 w-32 rounded-md border border-slate-200 bg-white p-2"
                    />
                  ) : null}
                </div>
              </section>
            ) : (
              <button
                type="button"
                disabled={!canBuy || isPurchasing || offer.current_quantity <= 0}
                onClick={handleBuyCoupon}
                className="mt-6 inline-flex h-11 items-center justify-center rounded-md bg-slate-900 px-6 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isPurchasing ? 'Issuing…' : 'Get coupon'}
              </button>
            )}
          </article>
        ) : null}
      </div>
    </Protected>
  );
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

