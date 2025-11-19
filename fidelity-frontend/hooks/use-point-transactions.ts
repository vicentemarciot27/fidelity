'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { PointTransaction, PaginatedResponse } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

type TransactionFilters = {
  scope?: string | null;
  scope_id?: string | null;
  page?: number;
  page_size?: number;
};

export function usePointTransactions(filters: TransactionFilters = {}) {
  const { status } = useAuth();
  const [data, setData] = useState<PaginatedResponse<PointTransaction> | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.scope) params.set('scope', filters.scope);
      if (filters.scope_id) params.set('scope_id', filters.scope_id);
      params.set('page', String(filters.page ?? 1));
      params.set('page_size', String(filters.page_size ?? 20));

      const result = await apiFetch<PaginatedResponse<PointTransaction>>(
        `/wallet/transactions?${params.toString()}`,
      );
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [filters.scope, filters.scope_id, filters.page, filters.page_size]);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status === 'authenticated') {
      void fetchTransactions();
    } else if (status === 'unauthenticated') {
      setIsLoading(false);
    }
  }, [fetchTransactions, status]);

  return {
    transactions: data,
    error,
    isLoading,
    refresh: fetchTransactions,
  };
}

