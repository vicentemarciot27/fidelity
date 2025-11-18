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
      visible: true,
    },
    {
      href: '/pdv',
      label: 'PDV',
      visible: true,
    },
    {
      href: '/admin/portal',
      label: 'Admin',
      visible: true,
    },
  ];

  const handleSignOut = () => {
    signOut();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-6 px-6 py-4">
          <Link href="/" className="text-xl font-bold">
            Sistema de Fidelidade
          </Link>
          <nav className="flex flex-wrap items-center gap-6 text-sm font-medium">
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
                    className={`transition-colors hover:text-white ${isActive ? 'text-white' : 'text-slate-300'}`}
                  >
                    {link.label}
                  </Link>
                );
              })}
          </nav>
          <div className="flex items-center gap-3">
            {status === 'authenticated' ? (
              <>
                <span className="text-sm text-slate-300">
                  {user?.role}
                </span>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="rounded-lg bg-white text-slate-900 px-4 py-2 text-sm font-medium transition hover:bg-slate-100"
                >
                  Sair
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-medium text-white hover:text-slate-200 transition"
                >
                  Entrar
                </Link>
                <Link
                  href="/login"
                  className="rounded-lg bg-blue-600 text-white px-5 py-2 text-sm font-medium transition hover:bg-blue-700"
                >
                  Cadastrar
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex w-full flex-1 flex-col">
        {children}
      </main>
    </div>
  );
}


