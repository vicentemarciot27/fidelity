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
      <div className="flex flex-col gap-8">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold text-slate-900">
            Admin operations
          </h1>
          <p className="text-sm text-slate-500">
            Manage coupon types, publish offers, and monitor inventory. Logged in
            as <strong>{user?.role}</strong>.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Create coupon type
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Define how discounts behave. These types can be reused across
              multiple offers.
            </p>
            <div className="mt-4">
              <CouponTypeForm onCreated={refreshCouponTypes} />
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Publish coupon offer
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Target stores, franchises, or the entire customer. Inventory starts
              at the initial quantity and decrements as coupons are issued.
            </p>
            <div className="mt-4">
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

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Coupon types
              </h2>
              <p className="text-sm text-slate-500">
                Overview of reusable discount definitions.
              </p>
            </div>
            <button
              type="button"
              onClick={refreshCouponTypes}
              className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 transition hover:bg-slate-100"
            >
              Refresh
            </button>
          </div>

          {typesLoading ? (
            <Placeholder message="Loading coupon types…" />
          ) : couponTypeItems.length > 0 ? (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">SKU specific</th>
                    <th className="px-3 py-2">Discount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {couponTypeItems.map((type) => (
                    <tr key={type.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-medium text-slate-700">
                        {type.redeem_type}
                      </td>
                      <td className="px-3 py-2">{type.sku_specific ? 'Yes' : 'No'}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {formatDiscount(type)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Placeholder message="No coupon types created yet." />
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Coupon offers
              </h2>
              <p className="text-sm text-slate-500">
                Filter by scope or status to focus on active campaigns.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
              <select
                value={scopeFilter}
                onChange={(event) => {
                  setScopeFilter(event.target.value);
                  setOffersPage(1);
                }}
                className="rounded-md border border-slate-300 px-3 py-1 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
              >
                <option value="">All scopes</option>
                <option value="CUSTOMER">Customer</option>
                <option value="FRANCHISE">Franchise</option>
                <option value="STORE">Store</option>
              </select>
              <select
                value={activeFilter}
                onChange={(event) => {
                  setActiveFilter(event.target.value as typeof activeFilter);
                  setOffersPage(1);
                }}
                className="rounded-md border border-slate-300 px-3 py-1 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <button
                type="button"
                onClick={refreshCouponOffers}
                className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 transition hover:bg-slate-100"
              >
                Refresh
              </button>
            </div>
          </div>

          {offersLoading ? (
            <Placeholder message="Loading offers…" />
          ) : couponOfferItems.length > 0 ? (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Scope</th>
                    <th className="px-3 py-2">Inventory</th>
                    <th className="px-3 py-2">Window</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {couponOfferItems.map((offer) => (
                    <tr key={offer.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-medium text-slate-700">
                        {offer.entity_scope}
                        <div className="text-xs text-slate-500">{offer.entity_id}</div>
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {offer.current_quantity}/{offer.initial_quantity}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {formatWindow(offer.start_at, offer.end_at)}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${offer.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}
                        >
                          {offer.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedOfferId(offer.id)}
                          className="text-sm font-medium text-slate-600 underline decoration-slate-300 hover:text-slate-900"
                        >
                          View details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Placeholder message="No coupon offers published yet." />
          )}

          {couponOffers?.pages && couponOffers.pages > 1 ? (
            <div className="mt-4 flex items-center justify-end gap-3 text-sm text-slate-600">
              <button
                type="button"
                disabled={offersPage === 1}
                onClick={() => setOffersPage((prev) => Math.max(prev - 1, 1))}
                className="rounded-md border border-slate-300 px-3 py-1 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Previous
              </button>
              <span>
                Page {offersPage} of {couponOffers.pages}
              </span>
              <button
                type="button"
                disabled={offersPage === couponOffers.pages}
                onClick={() =>
                  setOffersPage((prev) =>
                    couponOffers ? Math.min(prev + 1, couponOffers.pages) : prev,
                  )
                }
                className="rounded-md border border-slate-300 px-3 py-1 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Next
              </button>
            </div>
          ) : null}
        </section>

        {selectedOfferId ? (
          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Offer metrics
                </h2>
                <p className="text-sm text-slate-500">
                  Real-time inventory and redemption trends for{' '}
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">
                    {selectedOfferId}
                  </code>
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedOfferId(null)}
                  className="text-sm text-slate-600 underline decoration-slate-300 hover:text-slate-900"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedOfferId(selectedOfferId)}
                  className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 transition hover:bg-slate-100"
                >
                  Refresh
                </button>
              </div>
            </div>

            {detailLoading ? (
              <Placeholder message="Loading offer statistics…" />
            ) : selectedOffer && selectedStats ? (
              <div className="mt-4 grid gap-6 lg:grid-cols-2">
                <div className="space-y-3">
                  <Metric label="Initial quantity" value={selectedOffer.initial_quantity} />
                  <Metric label="Current quantity" value={selectedOffer.current_quantity} />
                  <Metric label="Active status" value={selectedOffer.is_active ? 'Active' : 'Inactive'} />
                  <Metric
                    label="Redemption window"
                    value={formatWindow(selectedOffer.start_at, selectedOffer.end_at)}
                  />
                </div>
                <div className="space-y-3">
                  <Metric label="Issued" value={selectedStats.total_issued} />
                  <Metric label="Reserved" value={selectedStats.total_reserved} />
                  <Metric label="Redeemed" value={selectedStats.total_redeemed} />
                  <Metric label="Expired" value={selectedStats.total_expired} />
                </div>
              </div>
            ) : (
              <Placeholder message="Unable to load metrics for this offer." />
            )}
          </section>
        ) : null}
      </div>
    </Protected>
  );
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="mt-4 rounded-md border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatDiscount(type: ReturnType<typeof useAdminCouponTypes>['couponTypes']['items'][number]) {
  if (type.redeem_type === 'BRL' && type.discount_amount_brl !== null) {
    return `R$ ${Number(type.discount_amount_brl).toFixed(2)}`;
  }
  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage !== null) {
    return `${Number(type.discount_amount_percentage)}%`;
  }
  if (type.redeem_type === 'FREE_SKU') {
    return (type.valid_skus ?? []).join(', ') || 'Free selected SKU';
  }
  return 'N/A';
}

function formatWindow(start: string | null, end: string | null) {
  const startText = start ? new Date(start).toLocaleString('pt-BR') : 'Immediate';
  const endText = end ? new Date(end).toLocaleString('pt-BR') : 'Open ended';
  return `${startText} → ${endText}`;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

