'use client';

import type { WalletResponse } from '../../lib/api-types';
import { useEntityName } from '../../hooks/use-entity-names';
import { useOfferDetail } from '../../hooks/use-offer-detail';

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
    <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Saldo de Pontos</h2>
          <p className="text-sm text-slate-600 mt-1">
            Convertido para {displayAs === 'brl' ? 'BRL' : 'pontos'} usando as regras mais recentes.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Atualizar
        </button>
      </div>

      <div>
        {isLoading ? (
          <Placeholder message="Carregando carteira..." />
        ) : wallet && wallet.balances.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {wallet.balances.map((balance) => (
              <div
                key={`${balance.scope}-${balance.scope_id ?? 'global'}`}
                className="flex flex-col rounded-xl border border-slate-200 from-slate-50 to-white p-5 shadow-sm"
              >
                <div className="mb-3">
                  <span className={`inline-block ${getScopeColor(balance.scope)} px-3 py-1 rounded-full text-xs font-semibold`}>
                    {formatScope(balance.scope)}
                  </span>
                </div>
                <div className="mb-2">
                  <p className="text-3xl font-bold text-slate-900">
                    {displayAs === 'brl'
                      ? formatCurrency(balance.as_brl ?? 0)
                      : formatNumber(balance.points)}
                  </p>
                  {displayAs === 'brl' ? (
                    <p className="text-sm text-slate-500 mt-1">
                      {formatNumber(balance.points)} pontos
                    </p>
                  ) : balance.as_brl !== null ? (
                    <p className="text-sm text-slate-500 mt-1">
                      ≈ {formatCurrency(balance.as_brl)}
                    </p>
                  ) : null}
                </div>
                {balance.scope_id && balance.scope !== 'GLOBAL' && (
                  <BalanceEntityName scope={balance.scope} scopeId={balance.scope_id} />
                )}
              </div>
            ))}
          </div>
        ) : (
          <Placeholder message="Nenhum saldo ativo ainda. Ganhe pontos comprando em lojas participantes." />
        )}
      </div>

      <div className="mt-8 pt-6 border-t border-slate-200">
        <h3 className="text-lg font-bold text-slate-900 mb-4">
          Seus Cupons
        </h3>
        {isLoading ? (
          <Placeholder message="Carregando cupons..." />
        ) : wallet && wallet.coupons.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {wallet.coupons.map((coupon) => (
              <CouponCard key={coupon.offer_id} coupon={coupon} />
            ))}
          </div>
        ) : (
          <Placeholder message="Nenhum cupom adquirido ainda. Navegue pelas ofertas abaixo para emitir seu primeiro cupom." />
        )}
      </div>
    </section>
  );
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatScope(scope: string) {
  switch (scope) {
    case 'GLOBAL':
      return 'Global';
    case 'CUSTOMER':
      return 'Rede';
    case 'FRANCHISE':
      return 'Franquia';
    case 'STORE':
      return 'Loja';
    default:
      return scope;
  }
}

function getScopeColor(scope: string) {
  switch (scope) {
    case 'GLOBAL':
      return 'bg-slate-100 text-slate-700';
    case 'CUSTOMER':
      return 'bg-blue-100 text-blue-700';
    case 'FRANCHISE':
      return 'bg-purple-100 text-purple-700';
    case 'STORE':
      return 'bg-green-100 text-green-700';
    default:
      return 'bg-slate-100 text-slate-700';
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

function BalanceEntityName({ 
  scope, 
  scopeId 
}: { 
  scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE'; 
  scopeId: string;
}) {
  const { entityName, isLoading } = useEntityName(scope, scopeId);
  
  if (isLoading) {
    return (
      <p className="text-xs text-slate-400 mt-auto">
        Carregando...
      </p>
    );
  }
  
  return (
    <p className="text-xs text-slate-400 mt-auto">
      {entityName || scopeId}
    </p>
  );
}

function CouponCard({ coupon }: { coupon: WalletResponse['coupons'][number] }) {
  const { offer, isLoading: loadingOffer } = useOfferDetail(coupon.offer_id);
  const { entityName, isLoading: loadingName } = useEntityName(
    offer?.entity_scope || 'CUSTOMER',
    offer?.entity_id || ''
  );

  const isLoading = loadingOffer || (offer && loadingName);
  const displayName = isLoading
    ? 'Carregando...'
    : offer && entityName
    ? entityName
    : offer?.entity_id || coupon.offer_id.slice(0, 8);

  return (
    <a 
      href={`/marketplace/my-coupons?offer_id=${coupon.offer_id}`}
      className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-sm transition hover:shadow-md hover:border-slate-300 cursor-pointer"
    >
      <div>
        <p className="font-semibold text-slate-900 text-sm">
          {displayName}
        </p>
        <p className="text-xs text-slate-500 mt-0.5">
          {coupon.available_count} disponíveis
        </p>
      </div>
      <div className="text-right">
        <p className="text-2xl font-bold text-green-600">
          {coupon.available_count}
        </p>
        <p className="text-xs text-slate-500">
          {coupon.redeemed_count} resgatados
        </p>
      </div>
    </a>
  );
}

