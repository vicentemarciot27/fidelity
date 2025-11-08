'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, apiFetch } from '../lib/api-client';
import type { AdminCouponType, PaginatedResponse } from '../lib/api-types';

export function useAdminCouponTypes(page = 1, pageSize = 10) {
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
    void fetchTypes();
  }, [fetchTypes]);

  return {
    couponTypes: data,
    error,
    isLoading,
    refresh: fetchTypes,
  };
}

