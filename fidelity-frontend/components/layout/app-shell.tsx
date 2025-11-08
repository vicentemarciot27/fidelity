'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useAuth } from '../providers/auth-provider';
import { isAdminRole } from '../../lib/roles';

export function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, user, signOut } = useAuth();

  const links = [
    {
      href: '/marketplace/dashboard',
      label: 'Marketplace',
      visible: status === 'authenticated' && Boolean(user?.personId),
    },
    {
      href: '/admin/portal',
      label: 'Admin',
      visible:
        status === 'authenticated' && Boolean(isAdminRole(user?.role)),
    },
    {
      href: '/login',
      label: 'Login',
      visible: status === 'unauthenticated',
    },
  ];

  const handleSignOut = () => {
    signOut();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <Link href="/" className="text-lg font-semibold text-slate-900">
            Fidelity
          </Link>
          <nav className="flex flex-wrap items-center gap-4 text-sm font-medium text-slate-600">
            {links
              .filter((link) => link.visible)
              .map((link) => {
                const isActive =
                  pathname === link.href ||
                  (link.href !== '/' && pathname?.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`transition-colors hover:text-slate-900 ${isActive ? 'text-slate-900' : ''}`}
                  >
                    {link.label}
                  </Link>
                );
              })}
          </nav>
          {status === 'authenticated' ? (
            <div className="flex items-center gap-3 text-sm">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                {user?.role ?? 'Unknown'} role
              </span>
              <button
                type="button"
                onClick={handleSignOut}
                className="rounded-md border border-slate-300 px-3 py-1 text-slate-600 transition hover:bg-slate-100"
              >
                Sign out
              </button>
            </div>
          ) : null}
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
        {children}
      </main>
    </div>
  );
}


