'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { AdminCouponOffer, PaginatedResponse } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

type AdminOfferFilters = {
  entity_scope?: string | null;
  entity_id?: string | null;
  is_active?: boolean | null;
  page?: number;
  page_size?: number;
};

export function useAdminCouponOffers(filters: AdminOfferFilters = {}) {
  const { status } = useAuth();
  const [data, setData] = useState<PaginatedResponse<AdminCouponOffer> | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOffers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.entity_scope) params.set('entity_scope', filters.entity_scope);
      if (filters.entity_id) params.set('entity_id', filters.entity_id);
      if (filters.is_active !== null && filters.is_active !== undefined) {
        params.set('is_active', String(filters.is_active));
      }
      params.set('page', String(filters.page ?? 1));
      params.set('page_size', String(filters.page_size ?? 10));

      const result = await apiFetch<PaginatedResponse<AdminCouponOffer>>(
        `/admin/coupon-offers?${params.toString()}`,
      );
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [
    filters.entity_id,
    filters.entity_scope,
    filters.is_active,
    filters.page,
    filters.page_size,
  ]);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status === 'authenticated') {
      void fetchOffers();
    } else if (status === 'unauthenticated') {
      setIsLoading(false);
    }
  }, [fetchOffers, status]);

  return {
    couponOffers: data,
    error,
    isLoading,
    refresh: fetchOffers,
  };
}

