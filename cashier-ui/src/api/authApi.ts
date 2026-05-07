import { apiClient } from './client';
import type { AuthUser, LoginCredentials } from '../types/auth';

/**
 * POST /api/auth/login/
 * Returns the authenticated user's profile on success.
 * Throws an AxiosError on failure (400 = bad credentials, 403 = inactive).
 */
export async function login(credentials: LoginCredentials): Promise<AuthUser> {
  const response = await apiClient.post<AuthUser>('/api/auth/login/', credentials);
  return response.data;
}

/**
 * POST /api/auth/logout/
 * Clears the Django session. Returns a detail message.
 */
export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout/');
}

/**
 * GET /api/auth/me/
 * Returns the currently authenticated user's profile.
 * Throws a 401 AxiosError if the session has expired or is missing.
 */
export async function getMe(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>('/api/auth/me/');
  return response.data;
}
