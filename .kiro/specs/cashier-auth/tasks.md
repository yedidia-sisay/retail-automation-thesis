# Tasks

## Task List

- [x] 1. Update DRF settings in `config/settings.py`
  - [x] 1.1 Add `DEFAULT_AUTHENTICATION_CLASSES` with `SessionAuthentication`
  - [x] 1.2 Change `DEFAULT_PERMISSION_CLASSES` from `IsAuthenticatedOrReadOnly` to `IsAuthenticated`

- [x] 2. Create `UserProfileSerializer` in `apps/accounts/serializers.py`
  - [x] 2.1 Serialize `id`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_superuser`
  - [x] 2.2 Add `groups` as a `SerializerMethodField` returning a list of group name strings

- [x] 3. Implement auth views in `apps/accounts/views.py`
  - [x] 3.1 Implement `LoginView` (POST, `AllowAny`, calls `authenticate()` + `login()`, returns 200 with profile or 400 with error)
  - [x] 3.2 Implement `LogoutView` (POST, `IsAuthenticated`, calls `logout()`, returns 200)
  - [x] 3.3 Implement `MeView` (GET, `IsAuthenticated`, returns serialized `request.user`)

- [x] 4. Create `apps/accounts/urls.py` with login, logout, and me routes

- [x] 5. Update `config/urls.py`
  - [x] 5.1 Replace `path("api/auth/", include("rest_framework.urls"))` with `path("api/auth/", include("apps.accounts.urls"))`

- [x] 6. Configure `CustomUserAdmin` in `apps/accounts/admin.py`
  - [x] 6.1 Extend Django's `UserAdmin` to expose `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `groups` in the admin interface
  - [x] 6.2 Register the custom admin class for the `User` model

- [x] 7. Create `seed_users` management command
  - [x] 7.1 Create directory structure: `apps/accounts/management/commands/`
  - [x] 7.2 Implement `seed_users.py` — idempotently create `Admin` group, `Cashier` group, and `adamreta` user
  - [x] 7.3 Add stdout messages for each created/skipped resource
  - [x] 7.4 Add source-code comment warning that the default password `123` must be changed before production

- [x] 8. Write example-based tests in `apps/accounts/tests.py` (Requirement 9 — 9 required test cases)
  - [x] 8.1 `test_seed_creates_admin_group`
  - [x] 8.2 `test_seed_creates_cashier_group`
  - [x] 8.3 `test_seed_creates_adamreta_user` (verify username, first_name, last_name, is_staff=False, is_superuser=False, is_active=True, Cashier group)
  - [x] 8.4 `test_login_success` (adamreta / 123 → HTTP 200)
  - [x] 8.5 `test_login_wrong_password` (→ HTTP 400)
  - [x] 8.6 `test_me_unauthenticated` (→ HTTP 401)
  - [x] 8.7 `test_me_authenticated` (login then GET /me/ → HTTP 200 with correct profile)
  - [x] 8.8 `test_logout_destroys_session` (login → logout → GET /me/ → HTTP 401)
  - [x] 8.9 `test_no_register_endpoint` (GET/POST /api/auth/register/ → HTTP 404 or 405)

- [x] 9. Write property-based tests using Hypothesis
  - [x] 9.1 Install `hypothesis[django]` (add to requirements if not present)
  - [x] 9.2 Property 1 test — login with valid credentials returns HTTP 200 and all required profile fields (`Feature: cashier-auth, Property 1`)
  - [x] 9.3 Property 2 test — login with wrong password returns HTTP 400 (`Feature: cashier-auth, Property 2`)
  - [x] 9.4 Property 3 test — logout destroys session; subsequent /me/ returns HTTP 401 (`Feature: cashier-auth, Property 3`)
  - [x] 9.5 Property 4 test — /me/ returns profile matching DB record for any authenticated user (`Feature: cashier-auth, Property 4`)
  - [x] 9.6 Property 5 test — seed_users is idempotent across multiple runs (`Feature: cashier-auth, Property 5`)
  - [x] 9.7 Property 6 test — seed_users stdout contains a message for each resource (`Feature: cashier-auth, Property 6`)

- [x] 10. Run the full test suite and verify all tests pass
  - [x] 10.1 Run `python manage.py test apps.accounts` from `backend/`
  - [x] 10.2 Confirm all 9 example tests and 6 property tests pass
