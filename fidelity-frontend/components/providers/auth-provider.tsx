'use client';

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { apiFetch, clearAuthTokens, setAuthTokens } from '../../lib/api-client';
import type { LoginRequest, Role, TokenResponse } from '../../lib/api-types';

const STORAGE_KEY = 'fidelity.auth.v1';

interface AuthUser {
  userId: string;
  role: Role | null;
  personId: string | null;
  customerId: string | null;
  franchiseId: string | null;
  storeId: string | null;
}

interface AuthContextValue {
  status: 'loading' | 'authenticated' | 'unauthenticated';
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  signIn: (credentials: LoginRequest) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type StoredAuth = {
  accessToken: string;
  refreshToken: string;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthContextValue['status']>('loading');
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const stored = getStoredAuth();
    if (stored) {
      setAccessToken(stored.accessToken);
      setRefreshToken(stored.refreshToken);
      setAuthTokens({
        accessToken: stored.accessToken,
        refreshToken: stored.refreshToken,
      });
      const parsedUser = parseUserFromToken(stored.accessToken);
      if (parsedUser) {
        setUser(parsedUser);
        setStatus('authenticated');
        return;
      }
      clearPersistedAuth();
    }
    setStatus('unauthenticated');
  }, []);

  const persistAuth = useCallback((tokens: TokenResponse) => {
    const payload: StoredAuth = {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    };

    const parsedUser = parseUserFromToken(tokens.access_token);
    if (!parsedUser) {
      clearPersistedAuth();
      clearAuthTokens();
      throw new Error('Invalid token payload received from backend.');
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    setAuthTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    setAccessToken(tokens.access_token);
    setRefreshToken(tokens.refresh_token);
    setUser(parsedUser);
    setStatus('authenticated');
  }, []);

  const signIn = useCallback(
    async (credentials: LoginRequest) => {
      setStatus('loading');
      try {
        const tokens = await apiFetch<TokenResponse>('/auth/login', 'POST', credentials, {
          auth: false,
        });
        persistAuth(tokens);
      } catch (error) {
        setStatus('unauthenticated');
        throw error;
      }
    },
    [persistAuth],
  );

  const signOut = useCallback(() => {
    clearPersistedAuth();
    clearAuthTokens();
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      accessToken,
      refreshToken,
      signIn,
      signOut,
    }),
    [status, user, accessToken, refreshToken, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

function getStoredAuth(): StoredAuth | null {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as StoredAuth;
  } catch {
    return null;
  }
}

function clearPersistedAuth() {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem(STORAGE_KEY);
}

function parseUserFromToken(token: string): AuthUser | null {
  try {
    const [, payloadPart] = token.split('.');
    if (!payloadPart) {
      return null;
    }
    const decoded = atob(base64UrlToBase64(payloadPart));
    const payload = JSON.parse(decoded) as Record<string, unknown>;
    return {
      userId: (payload.sub as string) ?? '',
      role: (payload.role as Role | undefined) ?? null,
      personId: (payload.person_id as string | undefined) ?? null,
      customerId: (payload.customer_id as string | undefined) ?? null,
      franchiseId: (payload.franchise_id as string | undefined) ?? null,
      storeId: (payload.store_id as string | undefined) ?? null,
    };
  } catch {
    return null;
  }
}

function base64UrlToBase64(value: string) {
  return value.replace(/-/g, '+').replace(/_/g, '/').padEnd(
    value.length + ((4 - (value.length % 4)) % 4),
    '=',
  );
}

