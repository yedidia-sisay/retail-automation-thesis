// ---------------------------------------------------------------------------
// Auth types — aligned with the Django backend's UserProfileSerializer
// Backend endpoint: GET /api/auth/me/  POST /api/auth/login/
// ---------------------------------------------------------------------------

export interface LoginCredentials {
  username: string;
  password: string;
}

/**
 * Shape returned by /api/auth/login/ and /api/auth/me/
 * Matches UserProfileSerializer in backend/apps/accounts/serializers.py
 */
export interface AuthUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  /** Django group names, e.g. ["Cashier"] or ["Admin"] */
  groups: string[];
  is_staff: boolean;
  is_superuser: boolean;
}

/** Derived role based on group membership */
export type UserRole = 'cashier' | 'admin' | 'unknown';

export function getUserRole(user: AuthUser): UserRole {
  if (user.is_superuser || user.groups.includes('Admin')) return 'admin';
  if (user.groups.includes('Cashier')) return 'cashier';
  return 'unknown';
}

export function getFullName(user: AuthUser): string {
  const full = `${user.first_name} ${user.last_name}`.trim();
  return full || user.username;
}
