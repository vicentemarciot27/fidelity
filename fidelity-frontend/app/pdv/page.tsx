'use client';

import { useState } from 'react';
import { useEarnPoints } from '../../hooks/use-earn-points';
import { useStores } from '../../hooks/use-admin-entities';

export default function PdvPage() {
  const [userId, setUserId] = useState('');
  const [cpf, setCpf] = useState('');
  const [orderValue, setOrderValue] = useState('');
  const [storeId, setStoreId] = useState('');
  const [result, setResult] = useState<{
    points: number;
    totalPoints: number;
    orderId: string;
  } | null>(null);

  const { earnPoints, isLoading: earnPointsLoading } = useEarnPoints();
  const { stores, loading: storesLoading } = useStores();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    // Validação
    if (!userId && !cpf) {
      alert('Por favor, informe o ID do usuário ou CPF');
      return;
    }

    if (!orderValue || parseFloat(orderValue) <= 0) {
      alert('Por favor, informe um valor válido para o pedido');
      return;
    }

    if (!storeId) {
      alert('Por favor, selecione uma loja');
      return;
    }

    try {
      const response = await earnPoints({
        person_id: userId || undefined,
        cpf: cpf || undefined,
        order: {
          total_brl: parseFloat(orderValue),
          tax_brl: 0,
          items: {},
        },
        store_id: storeId,
      });

      setResult({
        points: response.points_earned,
        totalPoints: response.wallet_snapshot.total_points,
        orderId: response.order_id,
      });

      // Limpar formulário após sucesso
      setUserId('');
      setCpf('');
      setOrderValue('');
    } catch (error: unknown) {
      if (error instanceof Error) {
        alert(`Erro ao adicionar pontos: ${error.message}`);
      } else {
        alert('Erro ao adicionar pontos');
      }
      console.error('Erro ao adicionar pontos:', error);
    }
  };

  const handleReset = () => {
    setResult(null);
    setUserId('');
    setCpf('');
    setOrderValue('');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">PDV - Adicionar Pontos</h1>
          <p className="mt-2 text-slate-600">
            Registre vendas e adicione pontos automaticamente aos clientes
          </p>
        </div>

        {result ? (
          <div className="rounded-lg border border-green-200 bg-green-50 p-6">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-600 text-white">
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold text-green-900">Pontos Adicionados!</h2>
                <p className="text-sm text-green-700">Pedido #{result.orderId.slice(0, 8)}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between border-b border-green-200 pb-2">
                <span className="font-medium text-green-900">Pontos Ganhos:</span>
                <span className="text-xl font-bold text-green-600">
                  +{result.points} pontos
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-green-900">Saldo Total:</span>
                <span className="text-xl font-bold text-green-600">
                  {result.totalPoints} pontos
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleReset}
              className="mt-6 w-full rounded-lg bg-green-600 px-4 py-3 font-medium text-white transition hover:bg-green-700"
            >
              Nova Venda
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-slate-900">
                Identificação do Cliente
              </h2>
              <p className="mb-4 text-sm text-slate-600">
                Informe o ID do usuário OU o CPF (pelo menos um)
              </p>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="userId"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    ID do Usuário
                  </label>
                  <input
                    id="userId"
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="UUID do usuário"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>

                <div>
                  <label
                    htmlFor="cpf"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    CPF
                  </label>
                  <input
                    id="cpf"
                    type="text"
                    value={cpf}
                    onChange={(e) => setCpf(e.target.value)}
                    placeholder="000.000.000-00"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-slate-900">Dados da Venda</h2>

              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="storeId"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Loja <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="storeId"
                    value={storeId}
                    onChange={(e) => setStoreId(e.target.value)}
                    required
                    disabled={storesLoading}
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">
                      {storesLoading ? 'Carregando lojas...' : 'Selecione uma loja'}
                    </option>
                    {stores?.map((store) => (
                      <option key={store.id} value={store.id}>
                        {store.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="orderValue"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Valor da Venda (R$) <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="orderValue"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={orderValue}
                    onChange={(e) => setOrderValue(e.target.value)}
                    placeholder="0.00"
                    required
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleReset}
                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Limpar
              </button>
              <button
                type="submit"
                disabled={earnPointsLoading}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {earnPointsLoading ? 'Processando...' : 'Adicionar Pontos'}
              </button>
            </div>
          </form>
        )}

        {/* Info Box */}
        <div className="mt-8 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <h3 className="mb-2 font-semibold text-blue-900">Como funciona?</h3>
          <ul className="space-y-1 text-sm text-blue-800">
            <li>• Os pontos são calculados automaticamente baseado nas regras configuradas</li>
            <li>• Você pode buscar o cliente por ID ou CPF</li>
            <li>• A loja é obrigatória para identificar a origem da venda</li>
            <li>• O cliente receberá os pontos imediatamente após o registro</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

