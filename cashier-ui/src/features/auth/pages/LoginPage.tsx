import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../../../components/layout/AppLayout';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { useAuth } from '../../../store/authContext';
import { getUserRole } from '../../../types/auth';
import type { AxiosError } from 'axios';

interface ApiErrorResponse {
  error?: string;
  detail?: string;
}

export function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect immediately.
  if (isAuthenticated && user) {
    const role = getUserRole(user);
    navigate(role === 'admin' ? '/cashier/dashboard' : '/cashier/dashboard', {
      replace: true,
    });
    return null;
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (!username.trim()) {
      setError('Username is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }

    setLoading(true);
    try {
      const loggedInUser = await login(username.trim(), password);
      const role = getUserRole(loggedInUser);
      // Both cashier and admin go to the dashboard for now.
      // Admin-specific routing can be added in a later phase.
      navigate(role === 'admin' ? '/cashier/dashboard' : '/cashier/dashboard', {
        replace: true,
      });
    } catch (err) {
      const axiosErr = err as AxiosError<ApiErrorResponse>;
      const serverMsg =
        axiosErr.response?.data?.error ??
        axiosErr.response?.data?.detail ??
        null;

      if (axiosErr.response?.status === 400) {
        setError(serverMsg ?? 'Invalid username or password.');
      } else if (axiosErr.response?.status === 401) {
        setError('Session expired. Please log in again.');
      } else if (!axiosErr.response) {
        setError(
          'Cannot reach the server. Check your connection or try again later.',
        );
      } else {
        setError(serverMsg ?? 'An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout className="flex items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">
            AI Retail Checkout
          </h1>
          <p className="mt-1 text-sm text-gray-500">Cashier Login</p>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <Input
            label="Username"
            id="username"
            type="text"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            placeholder="Enter your username"
          />

          <Input
            label="Password"
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            placeholder="Enter your password"
          />

          {/* Error message */}
          {error && (
            <div
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={loading}
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>
      </div>
    </AppLayout>
  );
}

export default LoginPage;
