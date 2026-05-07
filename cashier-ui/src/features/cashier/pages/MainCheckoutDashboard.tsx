import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../store/authContext';
import { getFullName } from '../../../types/auth';
import * as checkoutApi from '../../../api/checkoutApi';

/**
 * Cashier Home — shown at /cashier/dashboard.
 * The cashier starts a new session from here, which creates a session on the
 * backend and redirects to /cashier/session/:sessionId.
 */
export function MainCheckoutDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cashierName = user ? getFullName(user) : '—';

  async function handleStartSession() {
    setStarting(true);
    setError(null);
    try {
      const session = await checkoutApi.createSession();
      navigate(`/cashier/session/${session.id}`);
    } catch {
      setError('Failed to start a new checkout session. Is the backend running?');
    } finally {
      setStarting(false);
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#C2BFB0] font-sans text-[#291714]">

      {/* Header */}
      <header className="flex items-center justify-between border-b border-[#e7bdb7] bg-[#fff8f7] px-6 py-3 shadow-sm">
        <div className="flex items-center gap-4">
          <span className="text-2xl font-black tracking-tight text-[#bb0010]">VisionPOS AI</span>
          <div className="h-6 w-px bg-[#e7bdb7]" />
          <div className="flex flex-col">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#ab332c]">Cashier</span>
            <span className="text-sm font-semibold">{cashierName}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/settings')}
            className="rounded-lg p-2 text-[#5d3f3c] hover:bg-[#fff0ee] transition-colors"
            title="Settings"
          >
            ⚙️
          </button>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-[#ba1a1a] px-4 py-2 text-xs font-bold text-[#ba1a1a] hover:bg-red-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-1 flex-col items-center justify-center gap-8 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-black tracking-tight text-[#bb0010]">AI Retail Checkout</h1>
          <p className="mt-1 text-sm text-[#5d3f3c]">Welcome back, {cashierName}</p>
        </div>

        {error && (
          <div className="w-full max-w-sm rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Start checkout CTA */}
        <button
          onClick={handleStartSession}
          disabled={starting}
          className="flex items-center gap-3 rounded-2xl bg-[#bb0010] px-10 py-5 text-lg font-black text-white shadow-lg hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
        >
          {starting ? (
            <>
              <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Starting…
            </>
          ) : (
            <>+ Start New Checkout</>
          )}
        </button>

        {/* Quick links */}
        <div className="flex gap-4">
          {[
            { label: 'Transactions', path: '/transactions' },
            { label: 'Product Search', path: '/products/search' },
            { label: 'Settings', path: '/settings' },
          ].map(({ label, path }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className="rounded-xl border border-[#e7bdb7] bg-white px-5 py-3 text-sm font-semibold text-[#291714] shadow-sm hover:border-[#bb0010]/40 hover:bg-[#fff0ee] transition-all"
            >
              {label}
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}

export default MainCheckoutDashboard;
