'use client';

import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api-client';
import type { Customer, Franchise, Store, PaginatedResponse } from '../lib/api-types';

export function useCustomers() {
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

    fetchCustomers();
  }, []);

  return { customers, loading, error };
}

export function useFranchises(customerId?: string) {
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

    fetchFranchises();
  }, [customerId]);

  return { franchises, loading, error };
}

export function useStores(franchiseId?: string) {
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

    fetchStores();
  }, [franchiseId]);

  return { stores, loading, error };
}

