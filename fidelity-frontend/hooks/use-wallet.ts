'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../lib/api-client';
import type { WalletResponse } from '../lib/api-types';

export function useWallet(displayAs: 'points' | 'brl') {
  const [data, setData] = useState<WalletResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchWallet = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiFetch<WalletResponse>(
        `/wallet?display_as=${displayAs}`,
        'GET',
      );
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [displayAs]);

  useEffect(() => {
    void fetchWallet();
  }, [fetchWallet]);

  return {
    wallet: data,
    error,
    isLoading,
    refresh: fetchWallet,
  };
}

