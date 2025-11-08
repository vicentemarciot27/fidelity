'use client';

/**
 * Simple fetch wrapper that automatically prefixes the FastAPI base URL and
 * injects bearer tokens when present. Consumers can update the runtime auth
 * tokens via `setAuthTokens`.
 */

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

type RequestOptions = Omit<RequestInit, 'headers'> & {
  auth?: boolean;
  headers?: HeadersInit;
};

let accessToken: string | null = null;
let refreshToken: string | null = null;

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

export function setAuthTokens(tokens: {
  accessToken: string | null;
  refreshToken?: string | null;
}) {
  accessToken = tokens.accessToken ?? null;
  refreshToken =
    tokens.refreshToken !== undefined ? tokens.refreshToken : refreshToken;
}

export function clearAuthTokens() {
  accessToken = null;
  refreshToken = null;
}

export async function apiFetch<TResponse>(
  path: string,
  method: HttpMethod = 'GET',
  body?: unknown,
  options: RequestOptions = {}
): Promise<TResponse> {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  const headers = new Headers(options.headers);
  if (options.auth !== false && accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  if (body !== undefined && !(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    method,
    ...options,
    headers,
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
        ? body
        : JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await safeParseJson(response);
    const error = new ApiError(response.status, response.statusText, errorBody);
    throw error;
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await safeParseJson(response)) as TResponse;
}

async function safeParseJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly statusText: string;
  public readonly body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(statusText);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export function getStoredTokens() {
  return {
    accessToken,
    refreshToken,
  };
}

