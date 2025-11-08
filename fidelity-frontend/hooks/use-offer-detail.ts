'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { CouponOfferDetail } from '../lib/api-types';

export function useOfferDetail(offerId: string | null) {
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
    void fetchOffer();
  }, [fetchOffer]);

  return {
    offer: data,
    error,
    isLoading,
    refresh: fetchOffer,
  };
}

