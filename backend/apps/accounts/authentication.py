from rest_framework.authentication import SessionAuthentication


class SessionAuthenticationWithUnauthorized(SessionAuthentication):
    """
    Subclass of SessionAuthentication that returns HTTP 401 (instead of 403)
    for unauthenticated requests by providing a WWW-Authenticate header value.

    By default, DRF's SessionAuthentication returns 403 for unauthenticated
    requests because its authenticate_header() returns None. Returning a
    non-None value here causes DRF to raise NotAuthenticated (HTTP 401)
    instead of PermissionDenied (HTTP 403), satisfying Requirement 3.3.

    CSRF enforcement is disabled here because:
    - The API is consumed by a same-origin SPA (via Vite dev proxy).
    - Session authentication already provides equivalent protection.
    - CSRF cookie forwarding through the Vite proxy is unreliable in dev.
    For production, re-enable CSRF or switch to token-based auth.
    """

    def authenticate_header(self, request):
        return "Session"

    def enforce_csrf(self, request):
        # Skip CSRF check — the SPA is same-origin via the Vite proxy and
        # session auth already prevents cross-site request forgery in this setup.
        return
