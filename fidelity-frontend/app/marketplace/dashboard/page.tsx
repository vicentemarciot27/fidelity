'use client';

import { useState } from 'react';
import { Protected } from '../../../components/auth/protected';
import { OfferCard } from '../../../components/marketplace/offer-card';
import { WalletSummary } from '../../../components/marketplace/wallet-summary';
import { useAuth } from '../../../components/providers/auth-provider';
import { useOffers } from '../../../hooks/use-offers';
import { useWallet } from '../../../hooks/use-wallet';

export default function MarketplaceDashboard() {
  const [displayAs, setDisplayAs] = useState<'points' | 'brl'>('points');
  const { user } = useAuth();
  const {
    wallet,
    isLoading: walletLoading,
    refresh: refreshWallet,
  } = useWallet(displayAs);
  const {
    offers,
    isLoading: offersLoading,
    refresh: refreshOffers,
  } = useOffers({ active: true, page_size: 12 });

  const personUnavailable = !user?.personId;

  return (
    <Protected>
      <div className="flex flex-col gap-8">
        <header className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">
                Welcome back
              </h1>
              <p className="text-sm text-slate-500">
                Review your point balances and explore current coupon offers.
              </p>
            </div>
            <div className="inline-flex rounded-md border border-slate-200 bg-white p-1 text-sm shadow-sm">
              <ToggleButton
                isActive={displayAs === 'points'}
                onClick={() => setDisplayAs('points')}
              >
                Points
              </ToggleButton>
              <ToggleButton
                isActive={displayAs === 'brl'}
                onClick={() => setDisplayAs('brl')}
              >
                BRL
              </ToggleButton>
            </div>
          </div>
        </header>

        {personUnavailable ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-6 text-sm text-amber-700">
            Your account is not linked to a person record yet. Contact support to
            connect your CPF before collecting points and coupons.
          </div>
        ) : (
          <WalletSummary
            wallet={wallet}
            displayAs={displayAs}
            isLoading={walletLoading}
            onRefresh={refreshWallet}
          />
        )}

        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Available offers
            </h2>
            <button
              type="button"
              onClick={refreshOffers}
              className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 transition hover:bg-slate-100"
            >
              Refresh offers
            </button>
          </div>

          {offersLoading ? (
            <div className="rounded-md border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
              Loading offers…
            </div>
          ) : offers && offers.items.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {offers.items.map((offer) => (
                <OfferCard key={offer.id} offer={offer} />
              ))}
            </div>
          ) : (
            <div className="rounded-md border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
              No offers are currently active. Check back soon!
            </div>
          )}
        </section>
      </div>
    </Protected>
  );
}

function ToggleButton({
  isActive,
  onClick,
  children,
}: {
  isActive: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1 transition ${isActive ? 'bg-slate-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'}`}
    >
      {children}
    </button>
  );
}

