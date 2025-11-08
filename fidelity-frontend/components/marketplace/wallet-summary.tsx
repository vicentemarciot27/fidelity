'use client';

import type { WalletResponse } from '../../lib/api-types';

type WalletSummaryProps = {
  wallet: WalletResponse | null;
  displayAs: 'points' | 'brl';
  isLoading: boolean;
  onRefresh: () => void;
};

export function WalletSummary({
  wallet,
  displayAs,
  isLoading,
  onRefresh,
}: WalletSummaryProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Point balances</h2>
          <p className="text-sm text-slate-500">
            Converted to {displayAs === 'brl' ? 'BRL' : 'points'} using the latest tenant rules.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 transition hover:bg-slate-100"
        >
          Refresh
        </button>
      </div>

      <div className="mt-4">
        {isLoading ? (
          <Placeholder message="Loading wallet…" />
        ) : wallet && wallet.balances.length > 0 ? (
          <ul className="space-y-3">
            {wallet.balances.map((balance) => (
              <li
                key={`${balance.scope}-${balance.scope_id ?? 'global'}`}
                className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-700">
                    {formatScope(balance.scope)}
                  </p>
                  <p className="text-xs text-slate-500">
                    {balance.scope_id ?? 'Global'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-slate-900">
                    {displayAs === 'brl'
                      ? formatCurrency(balance.as_brl ?? 0)
                      : formatNumber(balance.points)}
                  </p>
                  {displayAs === 'brl' ? (
                    <p className="text-xs text-slate-500">
                      {formatNumber(balance.points)} pts
                    </p>
                  ) : balance.as_brl !== null ? (
                    <p className="text-xs text-slate-500">
                      {formatCurrency(balance.as_brl)}
                    </p>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <Placeholder message="No active balances yet. Earn points by purchasing in participating stores." />
        )}
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Available coupons
        </h3>
        {isLoading ? (
          <Placeholder message="Loading coupons…" />
        ) : wallet && wallet.coupons.length > 0 ? (
          <ul className="mt-3 space-y-2 text-sm text-slate-600">
            {wallet.coupons.map((coupon) => (
              <li
                key={coupon.offer_id}
                className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-2"
              >
                <span className="font-medium text-slate-700">
                  Offer {coupon.offer_id}
                </span>
                <span>
                  {coupon.available_count} available • {coupon.redeemed_count}{' '}
                  redeemed
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <Placeholder message="No coupons acquired yet. Browse offers below to issue your first coupon." />
        )}
      </div>
    </section>
  );
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="mt-3 rounded-md border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatScope(scope: string) {
  switch (scope) {
    case 'GLOBAL':
      return 'Global';
    case 'CUSTOMER':
      return 'Customer';
    case 'FRANCHISE':
      return 'Franchise';
    case 'STORE':
      return 'Store';
    default:
      return scope;
  }
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('pt-BR').format(value);
}

