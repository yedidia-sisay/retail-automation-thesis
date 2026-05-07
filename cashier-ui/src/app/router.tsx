import { createBrowserRouter, Navigate } from 'react-router-dom';
import LoginPage from '../features/auth/pages/LoginPage';
import MainCheckoutDashboard from '../features/cashier/pages/MainCheckoutDashboard';
import { CheckoutSessionPage } from '../features/cashier/pages/CheckoutSessionPage';

// Placeholder component factory — keeps things DRY for stub routes
function placeholder(title: string, description?: string) {
  return function PlaceholderPage() {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="rounded-xl bg-white p-10 shadow text-center max-w-md w-full">
          <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
          {description && (
            <p className="mt-2 text-sm text-gray-500">{description}</p>
          )}
        </div>
      </div>
    );
  };
}

const ReceiptDetailPage = placeholder(
  'Receipt Detail',
  'Receipt detail implementation comes next.',
);
const PrintReceiptPage = placeholder(
  'Print Receipt',
  'Print preview implementation comes next.',
);
const TransactionsPage = placeholder(
  'Transactions',
  'Transactions list implementation comes next.',
);
const TransactionDetailPage = placeholder(
  'Transaction Detail',
  'Transaction detail implementation comes next.',
);
const ProductSearchPage = placeholder(
  'Product Search',
  'Product search implementation comes next.',
);
const SettingsPage = placeholder(
  'Settings',
  'Settings implementation comes next.',
);

export const router = createBrowserRouter([
  // Redirect root to login
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },

  // Auth
  {
    path: '/login',
    element: <LoginPage />,
  },

  // Cashier dashboard (home)
  {
    path: '/cashier/dashboard',
    element: <MainCheckoutDashboard />,
  },

  // Active checkout session
  {
    path: '/cashier/session/:sessionId',
    element: <CheckoutSessionPage />,
  },

  // Receipts
  {
    path: '/receipts/:receiptId',
    element: <ReceiptDetailPage />,
  },
  {
    path: '/receipts/:receiptId/print',
    element: <PrintReceiptPage />,
  },

  // Transactions
  {
    path: '/transactions',
    element: <TransactionsPage />,
  },
  {
    path: '/transactions/:transactionId',
    element: <TransactionDetailPage />,
  },

  // Products
  {
    path: '/products/search',
    element: <ProductSearchPage />,
  },

  // Settings
  {
    path: '/settings',
    element: <SettingsPage />,
  },

  // Catch-all → 404
  {
    path: '*',
    element: placeholder(
      'Page Not Found',
      'The page you are looking for does not exist.',
    )(),
  },
]);

export default router;
