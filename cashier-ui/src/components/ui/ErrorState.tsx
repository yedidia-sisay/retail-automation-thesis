import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  details?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  details,
}: ErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 rounded-lg border border-red-200 bg-red-50 p-8 text-center"
      role="alert"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
        <svg
          className="h-6 w-6 text-red-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
          />
        </svg>
      </div>
      <div>
        <h3 className="text-base font-semibold text-red-800">{title}</h3>
        <p className="mt-1 text-sm text-red-600">{message}</p>
      </div>
      {details && (
        <details className="w-full text-left">
          <summary className="cursor-pointer text-xs text-red-500 hover:text-red-700">
            Technical details
          </summary>
          <pre className="mt-2 overflow-auto rounded bg-red-100 p-2 text-xs text-red-700">
            {details}
          </pre>
        </details>
      )}
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export default ErrorState;
