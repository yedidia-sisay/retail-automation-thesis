from rest_framework.authentication import SessionAuthentication


class SessionAuthenticationWithUnauthorized(SessionAuthentication):
    """
    Subclass of SessionAuthentication that returns HTTP 401 (instead of 403)
    for unauthenticated requests by providing a WWW-Authenticate header value.

    By default, DRF's SessionAuthentication returns 403 for unauthenticated
    requests because its authenticate_header() returns None. Returning a
    non-None value here causes DRF to raise NotAuthenticated (HTTP 401)
    instead of PermissionDenied (HTTP 403), satisfying Requirement 3.3.
    """

    def authenticate_header(self, request):
        return "Session"
