import React from 'react';
import { useAuth } from '../store/authContext';

/**
 * Renders a full-screen loading splash while the auth context is checking
 * the existing session (GET /api/auth/me/ on mount).
 * Once initializing is false, renders children normally.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { initializing } = useAuth();

  if (initializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="flex flex-col items-center gap-3">
          <svg
            className="h-8 w-8 animate-spin text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          <p className="text-sm text-gray-500">Loading…</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default AuthGate;
