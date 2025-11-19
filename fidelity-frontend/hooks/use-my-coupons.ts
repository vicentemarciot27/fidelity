'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../lib/api-client';
import type { MyCouponWithCode } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

export function useMyCoupons(offerId?: string) {
  const { status } = useAuth();
  const [data, setData] = useState<MyCouponWithCode[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCoupons = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const url = offerId
        ? `/coupons/my-with-codes?offer_id=${offerId}`
        : '/coupons/my-with-codes';
      const result = await apiFetch<MyCouponWithCode[]>(url, 'GET');
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [offerId]);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status === 'authenticated') {
      void fetchCoupons();
    } else if (status === 'unauthenticated') {
      setIsLoading(false);
    }
  }, [fetchCoupons, status]);

  return {
    coupons: data,
    error,
    isLoading,
    refresh: fetchCoupons,
  };
}

