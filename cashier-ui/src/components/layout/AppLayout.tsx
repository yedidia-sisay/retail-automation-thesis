import React from 'react';

interface AppLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Generic full-page wrapper. Provides the light gray background
 * and centers content with a max-width container.
 */
export function AppLayout({ children, className = '' }: AppLayoutProps) {
  return (
    <div className={`min-h-screen bg-gray-100 ${className}`}>
      {children}
    </div>
  );
}

export default AppLayout;
