'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { CouponOffer, PaginatedResponse } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

type OfferFilters = {
  scope?: string | null;
  scope_id?: string | null;
  search?: string | null;
  page?: number;
  page_size?: number;
  active?: boolean;
};

export function useOffers(filters: OfferFilters = {}) {
  const { status } = useAuth();
  const [data, setData] = useState<PaginatedResponse<CouponOffer> | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOffers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.scope) params.set('scope', filters.scope);
      if (filters.scope_id) params.set('scope_id', filters.scope_id);
      if (filters.search) params.set('search', filters.search);
      if (filters.page) params.set('page', String(filters.page));
      if (filters.page_size) params.set('page_size', String(filters.page_size));
      if (filters.active !== undefined) params.set('active', String(filters.active));
      else params.set('active', 'true');

      const query = params.toString();
      const result = await apiFetch<PaginatedResponse<CouponOffer>>(
        `/offers${query ? `?${query}` : ''}`,
      );
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [filters.active, filters.page, filters.page_size, filters.scope, filters.scope_id, filters.search]);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status === 'authenticated') {
      void fetchOffers();
    } else if (status === 'unauthenticated') {
      setIsLoading(false);
    }
  }, [fetchOffers, status]);

  return {
    offers: data,
    error,
    isLoading,
    refresh: fetchOffers,
  };
}

