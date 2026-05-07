import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../../../components/layout/DashboardLayout';
import { useAuth } from '../../../store/authContext';
import { getFullName } from '../../../types/auth';

/**
 * Main Checkout Dashboard — Phase 1 placeholder.
 * Renders the three-column layout skeleton described in the design document.
 * Full implementation (camera feeds, detection review, payment) comes in later phases.
 */
export function MainCheckoutDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  const cashierName = user ? getFullName(user) : '—';

  const headerContent = (
    <div className="flex w-full items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="font-bold text-gray-900">AI Retail Checkout</span>
        <span className="text-sm text-gray-400">|</span>
        <span className="text-sm text-gray-600">Session —</span>
        <span className="text-sm text-gray-600">Cashier: {cashierName}</span>
        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
          Open
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">
          {new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
        <button
          type="button"
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          New Session
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm text-red-600 hover:bg-red-100"
        >
          Logout
        </button>
      </div>
    </div>
  );

  return (
    <DashboardLayout header={headerContent}>
      <div className="mb-4">
        <h1 className="text-lg font-semibold text-gray-800">
          AI Retail Checkout Dashboard
        </h1>
        <p className="text-sm text-blue-600">
          Dashboard implementation comes next. Placeholder sections shown below.
        </p>
      </div>

      {/* Three-column grid */}
      <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-3">
        {/* LEFT: Input Feeds */}
        <div className="flex flex-col gap-4">
          <PlaceholderPanel
            title="Packaged Product Feed"
            badge="Live"
            badgeColor="green"
            description="Camera feed for packaged products. Capture or upload an image, then run detection."
          />
          <PlaceholderPanel
            title="Weighted Scale Feed"
            badge="Ready"
            badgeColor="blue"
            description="Camera feed for weighted items on a digital scale. One item at a time."
          />
          <PlaceholderPanel
            title="Barcode / Manual Fallback"
            description="Scan a barcode or search a product manually when vision detection is unavailable."
          />
        </div>

        {/* MIDDLE: Review & Correction */}
        <div className="flex flex-col gap-4">
          <PlaceholderPanel
            title="Packaged Detection Review"
            description="Detected packaged products appear here for cashier review and correction."
            emptyMessage="No packaged detections yet."
          />
          <PlaceholderPanel
            title="Weighted Item Review"
            description="Current weighted item candidate appears here for confirmation."
            emptyMessage="No weighted item detected."
          />
          <PlaceholderPanel
            title="Confirmed Checkout Items"
            description="All accepted items that are part of the current transaction."
            emptyMessage="No items confirmed yet."
          />
        </div>

        {/* RIGHT: Receipt Preview & Payment */}
        <div className="flex flex-col gap-4">
          <PlaceholderPanel
            title="Receipt Preview"
            description="Live receipt summary for the current checkout session."
            emptyMessage="No items added yet."
          />
          <PlaceholderPanel
            title="Checkout Actions"
            description="Confirm checkout, generate receipt, print preview, or cancel."
          />
          <PlaceholderPanel
            title="Payment"
            description="Select payment method and complete or simulate payment."
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

// ---------------------------------------------------------------------------
// Internal helper component — not exported
// ---------------------------------------------------------------------------

interface PlaceholderPanelProps {
  title: string;
  badge?: string;
  badgeColor?: 'green' | 'blue' | 'yellow' | 'gray';
  description?: string;
  emptyMessage?: string;
}

function PlaceholderPanel({
  title,
  badge,
  badgeColor = 'gray',
  description,
  emptyMessage,
}: PlaceholderPanelProps) {
  const badgeClasses: Record<string, string> = {
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    gray: 'bg-gray-100 text-gray-600',
  };

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
        {badge && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${badgeClasses[badgeColor]}`}
          >
            {badge}
          </span>
        )}
      </div>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
      {emptyMessage && (
        <p className="mt-3 rounded-lg bg-gray-50 py-4 text-center text-xs text-gray-400">
          {emptyMessage}
        </p>
      )}
    </div>
  );
}

export default MainCheckoutDashboard;
