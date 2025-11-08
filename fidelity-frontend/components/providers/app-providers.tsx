'use client';

import { type PropsWithChildren } from 'react';
import { AuthProvider } from './auth-provider';
import { ToastContainer } from '../ui/toast';

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <AuthProvider>
      {children}
      <ToastContainer />
    </AuthProvider>
  );
}

