'use client';

import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api-client';
import type { Customer, Franchise, Store, PaginatedResponse } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

export function useCustomers() {
  const { status } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        setLoading(true);
        const response = await apiFetch<PaginatedResponse<Customer>>(
          '/admin/customers?page=1&page_size=100',
          'GET'
        );
        setCustomers(response.items);
      } catch (err) {
        setError('Failed to load customers');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch when auth is ready
    if (status === 'authenticated') {
      fetchCustomers();
    } else if (status === 'unauthenticated') {
      setLoading(false);
    }
  }, [status]);

  return { customers, loading, error };
}

export function useFranchises(customerId?: string) {
  const { status } = useAuth();
  const [franchises, setFranchises] = useState<Franchise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFranchises = async () => {
      try {
        setLoading(true);
        const url = customerId
          ? `/admin/franchises?customer_id=${customerId}&page=1&page_size=100`
          : '/admin/franchises?page=1&page_size=100';
        const response = await apiFetch<PaginatedResponse<Franchise>>(url, 'GET');
        setFranchises(response.items);
      } catch (err) {
        setError('Failed to load franchises');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch when auth is ready
    if (status === 'authenticated') {
      fetchFranchises();
    } else if (status === 'unauthenticated') {
      setLoading(false);
    }
  }, [customerId, status]);

  return { franchises, loading, error };
}

export function useStores(franchiseId?: string) {
  const { status } = useAuth();
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStores = async () => {
      try {
        setLoading(true);
        const url = franchiseId
          ? `/admin/stores?franchise_id=${franchiseId}&page=1&page_size=100`
          : '/admin/stores?page=1&page_size=100';
        const response = await apiFetch<PaginatedResponse<Store>>(url, 'GET');
        setStores(response.items);
      } catch (err) {
        setError('Failed to load stores');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch when auth is ready
    if (status === 'authenticated') {
      fetchStores();
    } else if (status === 'unauthenticated') {
      setLoading(false);
    }
  }, [franchiseId, status]);

  return { stores, loading, error };
}

