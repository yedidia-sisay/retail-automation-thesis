interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export function LoadingState({
  message = 'Loading...',
  size = 'md',
}: LoadingStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-8 text-gray-500"
      role="status"
      aria-live="polite"
    >
      <svg
        className={`${sizeMap[size]} animate-spin text-blue-500`}
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
      <span className="text-sm">{message}</span>
    </div>
  );
}

export default LoadingState;
