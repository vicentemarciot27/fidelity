'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { AdminCouponOffer, CouponOfferStats } from '../lib/api-types';

export function useAdminOfferDetail(offerId: string | null) {
  const [offer, setOffer] = useState<AdminCouponOffer | null>(null);
  const [stats, setStats] = useState<CouponOfferStats | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(offerId));

  const fetchDetail = useCallback(async () => {
    if (!offerId) {
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const [offerDetail, offerStats] = await Promise.all([
        apiFetch<AdminCouponOffer>(`/admin/coupon-offers/${offerId}`),
        apiFetch<CouponOfferStats>(`/admin/coupon-offers/${offerId}/stats`),
      ]);
      setOffer(offerDetail);
      setStats(offerStats);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [offerId]);

  useEffect(() => {
    void fetchDetail();
  }, [fetchDetail]);

  return {
    offer,
    stats,
    error,
    isLoading,
    refresh: fetchDetail,
  };
}

