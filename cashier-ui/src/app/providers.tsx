import React from 'react';
import { AuthProvider } from '../store/authContext';

interface ProvidersProps {
  children: React.ReactNode;
}

/**
 * App-level provider wrapper.
 * AuthProvider handles session restoration on mount via GET /api/auth/me/
 */
export function Providers({ children }: ProvidersProps) {
  return <AuthProvider>{children}</AuthProvider>;
}

export default Providers;
