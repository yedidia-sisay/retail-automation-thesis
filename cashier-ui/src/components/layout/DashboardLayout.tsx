import React from 'react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  /** Content rendered inside the top header bar */
  header?: React.ReactNode;
}

/**
 * Dashboard layout with a sticky top header and a scrollable main content area.
 * Used for the cashier dashboard and other authenticated pages.
 */
export function DashboardLayout({ children, header }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-100">
      {/* Top header bar */}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
        {header ?? (
          <span className="text-sm font-semibold text-gray-700">
            AI Retail Checkout
          </span>
        )}
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-4">{children}</main>
    </div>
  );
}

export default DashboardLayout;
