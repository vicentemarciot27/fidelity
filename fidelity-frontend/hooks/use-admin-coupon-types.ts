'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { AdminCouponType, PaginatedResponse } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

export function useAdminCouponTypes(page = 1, pageSize = 10) {
  const { status } = useAuth();
  const [data, setData] = useState<PaginatedResponse<AdminCouponType> | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTypes = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      const result = await apiFetch<PaginatedResponse<AdminCouponType>>(
        `/admin/coupon-types?${params.toString()}`,
      );
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status === 'authenticated') {
      void fetchTypes();
    } else if (status === 'unauthenticated') {
      setIsLoading(false);
    }
  }, [fetchTypes, status]);

  return {
    couponTypes: data,
    error,
    isLoading,
    refresh: fetchTypes,
  };
}

