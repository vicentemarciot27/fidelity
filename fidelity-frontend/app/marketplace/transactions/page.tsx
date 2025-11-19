'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Protected } from '../../../components/auth/protected';
import { useAuth } from '../../../components/providers/auth-provider';
import { usePointTransactions } from '../../../hooks/use-point-transactions';
import { useEntityName } from '../../../hooks/use-entity-names';
import type { PointTransaction } from '../../../lib/api-types';

export default function TransactionsPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [scopeFilter, setScopeFilter] = useState<string>('');
  const { transactions, isLoading, refresh } = usePointTransactions({
    scope: scopeFilter || undefined,
    page,
    page_size: 20,
  });

  const personUnavailable = !user?.personId;

  return (
    <Protected>
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-5xl px-6 py-10">
          <div className="flex flex-col gap-8">
            <header className="flex flex-col gap-4">
              <div className="flex items-center gap-4">
                <Link
                  href="/marketplace/dashboard"
                  className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Voltar ao marketplace
                </Link>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">
                  Extrato de Pontos
                </h1>
                <p className="text-base text-slate-600 mt-1">
                  Histórico completo das suas transações de pontos
                </p>
              </div>
            </header>

            {personUnavailable ? (
              <div className="rounded-xl border border-amber-300 bg-amber-50 p-6 text-sm text-amber-800">
                <strong className="font-semibold">Atenção:</strong> Sua conta ainda não está vinculada a um registro de pessoa. 
                Entre em contato com o suporte para conectar seu CPF antes de visualizar transações.
              </div>
            ) : (
              <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">
                      Transações
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                      {transactions?.total ?? 0} transações encontradas
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <select
                      value={scopeFilter}
                      onChange={(event) => {
                        setScopeFilter(event.target.value);
                        setPage(1);
                      }}
                      className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    >
                      <option value="">Todos os escopos</option>
                      <option value="GLOBAL">Global</option>
                      <option value="CUSTOMER">Cliente</option>
                      <option value="FRANCHISE">Franquia</option>
                      <option value="STORE">Loja</option>
                    </select>
                    <button
                      type="button"
                      onClick={refresh}
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Atualizar
                    </button>
                  </div>
                </div>

                {isLoading ? (
                  <Placeholder message="Carregando transações..." />
                ) : transactions && transactions.items.length > 0 ? (
                  <div className="space-y-3">
                    {transactions.items.map((txn) => (
                      <TransactionCard key={txn.id} transaction={txn} />
                    ))}
                  </div>
                ) : (
                  <Placeholder message="Nenhuma transação encontrada. Comece comprando em lojas participantes!" />
                )}

                {transactions && transactions.pages > 1 ? (
                  <div className="mt-6 flex items-center justify-end gap-3 text-sm">
                    <button
                      type="button"
                      disabled={page === 1}
                      onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      Anterior
                    </button>
                    <span className="text-slate-600">
                      Página <strong className="text-slate-900">{page}</strong> de {transactions.pages}
                    </span>
                    <button
                      type="button"
                      disabled={page === transactions.pages}
                      onClick={() =>
                        setPage((prev) => Math.min(prev + 1, transactions.pages))
                      }
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      Próxima
                    </button>
                  </div>
                ) : null}
              </section>
            )}
          </div>
        </div>
      </div>
    </Protected>
  );
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function TransactionCard({ transaction }: { transaction: PointTransaction }) {
  const isPositive = transaction.delta > 0;
  const scopeBadgeConfig = getScopeBadgeConfig(transaction.scope);
  const { entityName, isLoading: loadingName } = useEntityName(
    transaction.scope as 'CUSTOMER' | 'FRANCHISE' | 'STORE',
    transaction.scope_id || ''
  );

  const reason = getTransactionReason(transaction);
  const isExpired = transaction.expires_at && new Date(transaction.expires_at) < new Date();

  return (
    <div className="flex items-start gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      {/* Ícone de transação */}
      <div className={`${isPositive ? 'bg-green-100' : 'bg-red-100'} p-3 rounded-xl`}>
        {isPositive ? (
          <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        )}
      </div>

      {/* Conteúdo */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-4 mb-2">
          <div>
            <h3 className="font-semibold text-slate-900 text-base">
              {reason}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`${scopeBadgeConfig.bg} ${scopeBadgeConfig.text} px-2.5 py-0.5 rounded-full text-xs font-semibold`}>
                {scopeBadgeConfig.label}
              </span>
              {isExpired && (
                <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
                  Expirado
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className={`text-2xl font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPositive ? '+' : ''}{formatNumber(transaction.delta)}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              pontos
            </p>
          </div>
        </div>

        {transaction.scope_id && transaction.scope !== 'GLOBAL' && (
          <p className="text-sm text-slate-600 mb-2">
            {loadingName ? 'Carregando...' : (entityName || transaction.scope_id.slice(0, 8))}
          </p>
        )}

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
          <span>
            {formatTimestamp(transaction.created_at)}
          </span>
          {transaction.expires_at && (
            <span>
              Expira em: {formatTimestamp(transaction.expires_at)}
            </span>
          )}
          {transaction.order_id && (
            <span className="font-mono">
              Pedido: {transaction.order_id.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function getScopeBadgeConfig(scope: string) {
  switch (scope) {
    case 'GLOBAL':
      return {
        label: 'Global',
        bg: 'bg-slate-100',
        text: 'text-slate-700',
      };
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
    default:
      return {
        label: scope,
        bg: 'bg-slate-100',
        text: 'text-slate-700',
      };
  }
}

function getTransactionReason(transaction: PointTransaction): string {
  const details = transaction.details as Record<string, unknown>;
  
  if (transaction.delta < 0) {
    if (details.reason === 'coupon_purchase') {
      return 'Compra de cupom';
    }
    if (details.reason === 'redemption') {
      return 'Resgate de pontos';
    }
    return 'Débito de pontos';
  }
  
  if (details.reason === 'welcome_bonus') {
    return 'Bônus de boas-vindas';
  }
  if (details.reason === 'franchise_campaign') {
    return 'Campanha da franquia';
  }
  if (transaction.order_id) {
    return 'Pontos de compra';
  }
  
  return 'Crédito de pontos';
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

function formatNumber(value: number) {
  return new Intl.NumberFormat('pt-BR').format(value);
}

