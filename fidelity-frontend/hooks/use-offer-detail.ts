'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { CouponOfferDetail } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

export function useOfferDetail(offerId: string | null) {
  const { status } = useAuth();
  const [data, setData] = useState<CouponOfferDetail | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(offerId));

  const fetchOffer = useCallback(async () => {
    if (!offerId) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await apiFetch<CouponOfferDetail>(`/offers/${offerId}`);
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [offerId]);

  useEffect(() => {
    // Only fetch when auth is ready and we have an offerId
    if (status === 'authenticated' && offerId) {
      void fetchOffer();
    } else if (status === 'unauthenticated' || !offerId) {
      setIsLoading(false);
    }
  }, [fetchOffer, status, offerId]);

  return {
    offer: data,
    error,
    isLoading,
    refresh: fetchOffer,
  };
}

