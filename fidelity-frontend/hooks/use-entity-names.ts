'use client';

import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api-client';
import type { Customer, Franchise, Store } from '../lib/api-types';
import { useAuth } from '../components/providers/auth-provider';

type EntityCache = Map<string, string | null>;

const entityCache: EntityCache = new Map();

export function useEntityName(entityScope: 'CUSTOMER' | 'FRANCHISE' | 'STORE', entityId: string) {
  const { status } = useAuth();
  const [entityName, setEntityName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Don't fetch if entityId is empty
    if (!entityId) {
      setEntityName(null);
      setIsLoading(false);
      return;
    }

    // Only fetch when auth is ready
    if (status !== 'authenticated') {
      if (status === 'unauthenticated') {
        setIsLoading(false);
      }
      return;
    }

    const cacheKey = `${entityScope}:${entityId}`;
    
    // Check cache first
    if (entityCache.has(cacheKey)) {
      setEntityName(entityCache.get(cacheKey) || null);
      setIsLoading(false);
      return;
    }

    const fetchEntityName = async () => {
      try {
        let endpoint = '';
        if (entityScope === 'CUSTOMER') {
          endpoint = `/admin/customers/${entityId}`;
        } else if (entityScope === 'FRANCHISE') {
          endpoint = `/admin/franchises/${entityId}`;
        } else if (entityScope === 'STORE') {
          endpoint = `/admin/stores/${entityId}`;
        }

        const entity = await apiFetch<Customer | Franchise | Store>(endpoint, 'GET');
        const name = entity.name;
        
        entityCache.set(cacheKey, name);
        setEntityName(name);
      } catch (error) {
        console.warn(`Failed to fetch entity name for ${entityScope}:${entityId}`, error);
        entityCache.set(cacheKey, null);
        setEntityName(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEntityName();
  }, [entityScope, entityId, status]);

  return { entityName, isLoading };
}

// Batch version for multiple entities
export function useEntityNames(entities: Array<{ scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE'; id: string }>) {
  const { status } = useAuth();
  const [entityNames, setEntityNames] = useState<Map<string, string | null>>(new Map());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Only fetch when auth is ready
    if (status !== 'authenticated') {
      if (status === 'unauthenticated') {
        setIsLoading(false);
      }
      return;
    }

    const fetchNames = async () => {
      const names = new Map<string, string | null>();
      
      for (const entity of entities) {
        const cacheKey = `${entity.scope}:${entity.id}`;
        
        // Check cache first
        if (entityCache.has(cacheKey)) {
          names.set(cacheKey, entityCache.get(cacheKey) || null);
          continue;
        }

        try {
          let endpoint = '';
          if (entity.scope === 'CUSTOMER') {
            endpoint = `/admin/customers/${entity.id}`;
          } else if (entity.scope === 'FRANCHISE') {
            endpoint = `/admin/franchises/${entity.id}`;
          } else if (entity.scope === 'STORE') {
            endpoint = `/admin/stores/${entity.id}`;
          }

          const result = await apiFetch<Customer | Franchise | Store>(endpoint, 'GET');
          const name = result.name;
          
          entityCache.set(cacheKey, name);
          names.set(cacheKey, name);
        } catch (error) {
          console.warn(`Failed to fetch entity name for ${entity.scope}:${entity.id}`, error);
          entityCache.set(cacheKey, null);
          names.set(cacheKey, null);
        }
      }

      setEntityNames(names);
      setIsLoading(false);
    };

    fetchNames();
  }, [entities, status]);

  return { entityNames, isLoading };
}

