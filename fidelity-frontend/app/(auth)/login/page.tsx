'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ApiError } from '../../../lib/api-client';
import { isAdminRole } from '../../../lib/roles';
import { useAuth } from '../../../components/providers/auth-provider';

export default function LoginPage() {
  const { status, user, signIn } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (status === 'authenticated' && user) {
      const redirectParam = searchParams?.get('redirectTo');
      if (redirectParam) {
        router.replace(redirectParam);
        return;
      }

      if (isAdminRole(user.role)) {
        router.replace('/admin/portal');
      } else if (user.personId) {
        router.replace('/marketplace/dashboard');
      } else {
        router.replace('/');
      }
    }
  }, [router, searchParams, status, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await signIn({ email, password });
    } catch (err) {
      if (err instanceof ApiError) {
        const body = err.body as { detail?: string };
        setError(body?.detail ?? 'Unable to sign in. Please try again.');
      } else {
        setError('Unexpected error. Please try again.');
      }
      setIsSubmitting(false);
      return;
    }

    setIsSubmitting(false);
  };

  return (
    <div className="mx-auto w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Sign in</h1>
      <p className="mt-2 text-sm text-slate-500">
        Use your Fidelity account credentials. New users can register via the
        FastAPI backend or Admin portal.
      </p>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-1 text-sm text-slate-600">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-base text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
            autoComplete="email"
            required
          />
        </label>

        <label className="flex flex-col gap-1 text-sm text-slate-600">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-base text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
            autoComplete="current-password"
            required
          />
        </label>

        {error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex h-11 items-center justify-center rounded-md bg-slate-900 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <Link
        href="/"
        className="mt-6 inline-block text-sm font-medium text-slate-600 underline decoration-slate-300 hover:text-slate-900"
      >
        Back to homepage
      </Link>
    </div>
  );
}

