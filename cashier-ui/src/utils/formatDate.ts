/**
 * Format an ISO date string to a human-readable date.
 * Example: "2024-01-15T10:42:00Z" → "Jan 15, 2024"
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format an ISO date string to a human-readable time.
 * Example: "2024-01-15T10:42:00Z" → "10:42 AM"
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format an ISO date string to date + time.
 * Example: "2024-01-15T10:42:00Z" → "Jan 15, 2024 10:42 AM"
 */
export function formatDateTime(isoString: string): string {
  return `${formatDate(isoString)} ${formatTime(isoString)}`;
}
