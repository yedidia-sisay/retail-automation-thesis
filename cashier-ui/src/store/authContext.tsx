import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import * as authApi from '../api/authApi';
import type { AuthUser } from '../types/auth';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuthState {
  user: AuthUser | null;
  /** true while the initial /me check is running on mount */
  initializing: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    initializing: true,
    isAuthenticated: false,
  });

  // On mount, try to restore the session by calling /me.
  // If the session cookie is still valid, the user is already logged in.
  useEffect(() => {
    authApi
      .getMe()
      .then((user) => {
        setState({ user, initializing: false, isAuthenticated: true });
      })
      .catch(() => {
        // No active session — that's fine, just mark initializing done.
        setState({ user: null, initializing: false, isAuthenticated: false });
      });
  }, []);

  const login = useCallback(
    async (username: string, password: string): Promise<AuthUser> => {
      const user = await authApi.login({ username, password });
      setState({ user, initializing: false, isAuthenticated: true });
      return user;
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      // Clear local state regardless of whether the server call succeeded.
      setState({ user: null, initializing: false, isAuthenticated: false });
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ ...state, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
