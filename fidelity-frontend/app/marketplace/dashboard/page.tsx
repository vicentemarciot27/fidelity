'use client';

import Link from 'next/link';
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
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="flex flex-col gap-8">
            <header className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-slate-900">
                    Bem-vindo ao Marketplace
                  </h1>
                  <p className="text-base text-slate-600 mt-1">
                    Confira seu saldo de pontos e explore as ofertas disponíveis
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href="/marketplace/transactions"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:shadow-sm"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    Ver extrato
                  </Link>
                  <div className="inline-flex rounded-lg border border-slate-300 bg-white p-1 text-sm shadow-sm">
                    <ToggleButton
                      isActive={displayAs === 'points'}
                      onClick={() => setDisplayAs('points')}
                    >
                      Pontos
                    </ToggleButton>
                    <ToggleButton
                      isActive={displayAs === 'brl'}
                      onClick={() => setDisplayAs('brl')}
                    >
                      R$
                    </ToggleButton>
                  </div>
                </div>
              </div>
            </header>

            {personUnavailable ? (
              <div className="rounded-xl border border-amber-300 bg-amber-50 p-6 text-sm text-amber-800">
                <strong className="font-semibold">Atenção:</strong> Sua conta ainda não está vinculada a um registro de pessoa. 
                Entre em contato com o suporte para conectar seu CPF antes de acumular pontos e cupons.
              </div>
            ) : (
              <WalletSummary
                wallet={wallet}
                displayAs={displayAs}
                isLoading={walletLoading}
                onRefresh={refreshWallet}
              />
            )}

            <section className="flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-slate-900">
                  Ofertas Disponíveis
                </h2>
                <button
                  type="button"
                  onClick={refreshOffers}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:shadow-sm"
                >
                  Atualizar Ofertas
                </button>
              </div>
              <p className="text-sm text-slate-500 -mt-4">
                A emissão de cada cupom consome pontos do escopo indicado na oferta. Verifique seu saldo antes de comprar.
              </p>

              {offersLoading ? (
                <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-base text-slate-500">
                  Carregando ofertas...
                </div>
              ) : offers && offers.items.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {offers.items.map((offer) => (
                    <OfferCard key={offer.id} offer={offer} />
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-base text-slate-500">
                  Nenhuma oferta ativa no momento. Volte em breve!
                </div>
              )}
            </section>
          </div>
        </div>
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
      className={`rounded-lg px-4 py-2 font-medium transition ${isActive ? 'bg-slate-900 text-white shadow' : 'text-slate-700 hover:bg-slate-100'}`}
    >
      {children}
    </button>
  );
}

