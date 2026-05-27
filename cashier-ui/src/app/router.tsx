import { createBrowserRouter, Navigate } from 'react-router-dom';
import LoginPage from '../features/auth/pages/LoginPage';
import MainCheckoutDashboard from '../features/cashier/pages/MainCheckoutDashboard';
import { CheckoutSessionPage } from '../features/cashier/pages/CheckoutSessionPage';
import { ReceiptDetailPage } from '../features/receipts/pages/ReceiptDetailPage';
import { PrintReceiptPage } from '../features/receipts/pages/PrintReceiptPage';
import CameraSettingsPage from '../features/settings/pages/CameraSettingsPage';

function placeholder(title: string, description?: string) {
  return function PlaceholderPage() {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="rounded-xl bg-white p-10 shadow text-center max-w-md w-full">
          <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
          {description && <p className="mt-2 text-sm text-gray-500">{description}</p>}
        </div>
      </div>
    );
  };
}

const TransactionsPage = placeholder('Transactions', 'Transactions list — coming soon.');
const TransactionDetailPage = placeholder('Transaction Detail', 'Transaction detail — coming soon.');
const ProductSearchPage = placeholder('Product Search', 'Product search — coming soon.');
const SettingsPage = placeholder('Settings', 'Settings — coming soon.');

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },

  { path: '/login', element: <LoginPage /> },

  { path: '/cashier/dashboard', element: <MainCheckoutDashboard /> },
  { path: '/cashier/session/:sessionId', element: <CheckoutSessionPage /> },

  { path: '/receipts/:receiptId', element: <ReceiptDetailPage /> },
  { path: '/receipts/:receiptId/print', element: <PrintReceiptPage /> },

  { path: '/transactions', element: <TransactionsPage /> },
  { path: '/transactions/:transactionId', element: <TransactionDetailPage /> },

  { path: '/products/search', element: <ProductSearchPage /> },
  { path: '/settings', element: <SettingsPage /> },
  { path: '/settings/cameras', element: <CameraSettingsPage /> },

  {
    path: '*',
    element: placeholder('Page Not Found', 'The page you are looking for does not exist.')(),
  },
]);

export default router;
