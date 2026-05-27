import axios from 'axios';

// When the Vite dev proxy is active (port 3000 → 8000), use a relative base
// so all /api/* requests go through the proxy and session cookies work correctly.
// In production, set VITE_API_BASE_URL to the real backend origin.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
  // Required for Django session auth — sends the session cookie and CSRF token
  // with every request. Works in dev via the Vite proxy (no cross-origin issues).
  withCredentials: true,
});

// Request interceptor — reads the CSRF token from the cookie Django sets
// (csrftoken) and attaches it as the X-CSRFToken header on mutating requests.
apiClient.interceptors.request.use(
  (config) => {
    const method = config.method?.toUpperCase() ?? '';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = getCsrfTokenFromCookie();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — placeholder for global error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: Handle 401 → redirect to login, 403 → show forbidden, etc.
    return Promise.reject(error);
  },
);

/** Read the Django csrftoken cookie value. */
function getCsrfTokenFromCookie(): string | null {
  const match = document.cookie
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith('csrftoken='));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

export default apiClient;
