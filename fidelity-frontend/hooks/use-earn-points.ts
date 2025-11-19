'use client';

import { useState } from 'react';
import { apiFetch, ApiError } from '../lib/api-client';

export interface EarnPointsRequest {
  person_id?: string;
  cpf?: string;
  order: {
    total_brl: number;
    tax_brl?: number;
    items?: Record<string, unknown>;
    shipping?: Record<string, unknown>;
    checkout_ref?: string;
    external_id?: string;
  };
  store_id: string;
}

export interface EarnPointsResponse {
  order_id: string;
  points_earned: number;
  wallet_snapshot: {
    total_points: number;
  };
}

export function useEarnPoints() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const earnPoints = async (data: EarnPointsRequest): Promise<EarnPointsResponse> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiFetch<EarnPointsResponse>('/pdv/earn-points', 'POST', data);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    earnPoints,
    isLoading,
    error,
  };
}
