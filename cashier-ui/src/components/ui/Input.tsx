import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({
  label,
  error,
  hint,
  id,
  className = '',
  ...props
}: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-gray-700"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={[
          'w-full rounded-lg border px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
          error
            ? 'border-red-400 bg-red-50'
            : 'border-gray-300 bg-white hover:border-gray-400',
          className,
        ].join(' ')}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={
          error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
        }
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
      {hint && !error && (
        <p id={`${inputId}-hint`} className="text-xs text-gray-500">
          {hint}
        </p>
      )}
    </div>
  );
}

export default Input;
