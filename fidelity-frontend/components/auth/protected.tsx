'use client';

import { useRouter } from 'next/navigation';
import { type ReactNode, useEffect } from 'react';
import type { Role } from '../../lib/api-types';
import { useAuth } from '../providers/auth-provider';

type ProtectedProps = {
  children: ReactNode;
  roles?: Role[];
  fallback?: ReactNode;
  redirectTo?: string;
};

export function Protected({
  children,
  roles,
  fallback = null,
  redirectTo,
}: ProtectedProps) {
  const router = useRouter();
  const { status, user } = useAuth();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace(redirectTo ?? '/login');
    }
  }, [redirectTo, router, status]);

  if (status === 'loading') {
    return (
      <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-slate-200 bg-white text-sm text-slate-500">
        Checking your session...
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return fallback;
  }

  if (roles && user?.role && !roles.includes(user.role)) {
    if (redirectTo) {
      router.replace(redirectTo);
      return null;
    }
    return (
      <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
        You do not have permission to access this content.
      </div>
    );
  }

  return <>{children}</>;
}

