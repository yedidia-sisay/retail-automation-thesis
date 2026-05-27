# Requirements Document

## Introduction

This feature implements backend authentication and role-based user management for the retail checkout automation system's cashier and admin interfaces. The system uses Django's built-in authentication framework (sessions, groups, and the built-in User model) with Django REST Framework. Account creation is exclusively managed through Django Admin — there is no public registration endpoint. The frontend interacts with three API endpoints: login, logout, and current-user check.

## Glossary

- **Auth_System**: The Django authentication subsystem (`django.contrib.auth`) responsible for verifying credentials, managing sessions, and enforcing access control.
- **Admin_User**: A Django user assigned to the `Admin` group with `is_staff=True`, who can access Django Admin and manage other user accounts.
- **Cashier_User**: A Django user assigned to the `Cashier` group with `is_staff=False`, who can authenticate and use cashier-facing API routes but cannot access Django Admin.
- **Django_Admin**: The built-in Django administration interface accessible at `/admin/`.
- **Session**: A server-side session created by Django's session middleware upon successful login, used to authenticate subsequent requests.
- **Seed_Command**: The `python manage.py seed_users` management command that initialises required groups and a default cashier user for development.
- **Login_Endpoint**: `POST /api/auth/login/` — accepts credentials and establishes a session.
- **Logout_Endpoint**: `POST /api/auth/logout/` — destroys the current session.
- **Me_Endpoint**: `GET /api/auth/me/` — returns the authenticated user's profile.
- **UserAdmin**: Django's built-in `UserAdmin` class, extended to expose the required fields in Django Admin.

---

## Requirements

### Requirement 1: Role-Based Group Setup

**User Story:** As an Admin_User, I want two distinct permission groups (Admin and Cashier) to exist in the system, so that I can assign appropriate access levels to each user.

#### Acceptance Criteria

1. THE Auth_System SHALL provide an `Admin` group and a `Cashier` group as named Django `Group` objects.
2. WHEN a user is assigned to the `Admin` group, THE Auth_System SHALL grant that user access to Django_Admin provided `is_staff=True` is also set on the user.
3. WHEN a user is assigned to the `Cashier` group, THE Auth_System SHALL restrict that user from accessing Django_Admin unless `is_staff` is explicitly set to `True` on the user record.
4. THE Auth_System SHALL NOT grant Cashier_User accounts any Django Admin access by default.

---

### Requirement 2: Account Management via Django Admin

**User Story:** As an Admin_User, I want to create and manage user accounts exclusively through Django Admin, so that no public account-creation endpoint exists and account provisioning remains under administrative control.

#### Acceptance Criteria

1. THE Django_Admin SHALL expose a user management interface that allows Admin_User to create new user accounts.
2. THE Django_Admin SHALL display the following fields for each user: `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `groups`.
3. WHEN an Admin_User creates a user via Django_Admin, THE Auth_System SHALL store the user with a hashed password.
4. THE Django_Admin SHALL allow Admin_User to assign users to the `Admin` or `Cashier` group.
5. THE Django_Admin SHALL allow Admin_User to activate or deactivate user accounts by toggling `is_active`.
6. THE Django_Admin SHALL allow Admin_User to set or reset a user's password.
7. THE Auth_System SHALL NOT expose a public HTTP endpoint for user registration or account creation.

---

### Requirement 3: Session-Based Authentication Configuration

**User Story:** As a developer, I want the API to use Django session-based authentication, so that the frontend can authenticate using cookies without requiring token management.

#### Acceptance Criteria

1. THE Auth_System SHALL use `rest_framework.authentication.SessionAuthentication` as the sole DRF authentication class.
2. THE Auth_System SHALL use `rest_framework.permissions.IsAuthenticated` as the default DRF permission class.
3. WHEN a request arrives without a valid session, THE Auth_System SHALL return HTTP 401 for protected endpoints.
4. THE Auth_System SHALL include Django's `SessionMiddleware` and `AuthenticationMiddleware` in the middleware stack.

---

### Requirement 4: Login Endpoint

**User Story:** As a Cashier_User or Admin_User, I want to log in with my username and password, so that I can obtain an authenticated session to use the system.

#### Acceptance Criteria

1. WHEN a `POST` request is sent to `/api/auth/login/` with valid `username` and `password` fields, THE Login_Endpoint SHALL authenticate the user, create a Session, and return HTTP 200 with the user's profile JSON.
2. THE Login_Endpoint SHALL return a JSON object containing: `id`, `username`, `first_name`, `last_name`, `email`, `groups` (list of group name strings), `is_staff`, and `is_superuser`.
3. WHEN a `POST` request is sent to `/api/auth/login/` with an incorrect password or non-existent username, THE Login_Endpoint SHALL return HTTP 400 with a descriptive error message.
4. WHEN a `POST` request is sent to `/api/auth/login/` with missing `username` or `password` fields, THE Login_Endpoint SHALL return HTTP 400 with a descriptive error message.
5. THE Login_Endpoint SHALL be accessible without a prior authenticated session (i.e., it must be exempt from the default `IsAuthenticated` permission).
6. WHEN a `POST` request is sent to `/api/auth/login/` for a user whose `is_active=False`, THE Login_Endpoint SHALL return HTTP 400 with a descriptive error message.

---

### Requirement 5: Logout Endpoint

**User Story:** As an authenticated Cashier_User or Admin_User, I want to log out, so that my session is invalidated and the system is secured.

#### Acceptance Criteria

1. WHEN a `POST` request is sent to `/api/auth/logout/` with a valid Session, THE Logout_Endpoint SHALL call Django's `logout()`, destroy the Session, and return HTTP 200 with a success message.
2. WHEN a `POST` request is sent to `/api/auth/logout/` without a valid Session, THE Logout_Endpoint SHALL return HTTP 401.

---

### Requirement 6: Current-User Endpoint

**User Story:** As an authenticated Cashier_User or Admin_User, I want to retrieve my current user profile, so that the frontend can display my identity and determine my role.

#### Acceptance Criteria

1. WHEN a `GET` request is sent to `/api/auth/me/` with a valid Session, THE Me_Endpoint SHALL return HTTP 200 with the authenticated user's profile JSON.
2. THE Me_Endpoint SHALL return a JSON object containing: `id`, `username`, `first_name`, `last_name`, `email`, `groups` (list of group name strings), `is_staff`, and `is_superuser`.
3. WHEN a `GET` request is sent to `/api/auth/me/` without a valid Session, THE Me_Endpoint SHALL return HTTP 401.

---

### Requirement 7: URL Routing

**User Story:** As a developer, I want the authentication endpoints registered under a consistent URL prefix, so that the frontend can reliably locate them.

#### Acceptance Criteria

1. THE Auth_System SHALL register all authentication endpoints under the prefix `api/auth/` in `config/urls.py` using `path("api/auth/", include("apps.accounts.urls"))`.
2. THE Auth_System SHALL expose exactly three custom endpoints: `POST /api/auth/login/`, `POST /api/auth/logout/`, and `GET /api/auth/me/`.
3. THE Auth_System SHALL NOT expose a `POST /api/auth/register/` endpoint or any equivalent public account-creation route.

---

### Requirement 8: Seed Command

**User Story:** As a developer, I want a management command that seeds required groups and a default cashier user, so that a fresh development environment is ready to use immediately after setup.

#### Acceptance Criteria

1. WHEN `python manage.py seed_users` is executed, THE Seed_Command SHALL create the `Admin` group if it does not already exist.
2. WHEN `python manage.py seed_users` is executed, THE Seed_Command SHALL create the `Cashier` group if it does not already exist.
3. WHEN `python manage.py seed_users` is executed, THE Seed_Command SHALL create a user with `username=adamreta`, `first_name=Adam`, `last_name=Reta`, `password=123`, `is_staff=False`, `is_superuser=False`, `is_active=True`, assigned to the `Cashier` group, if that user does not already exist.
4. WHEN `python manage.py seed_users` is executed and the `adamreta` user already exists, THE Seed_Command SHALL NOT create a duplicate user or modify the existing user's password.
5. WHEN `python manage.py seed_users` is executed and the `Admin` or `Cashier` group already exists, THE Seed_Command SHALL NOT create a duplicate group.
6. THE Seed_Command SHALL include a source-code comment stating that the default password `123` MUST be changed before deploying to production.
7. THE Seed_Command SHALL print a confirmation message to stdout for each resource that is created and a skip message for each resource that already exists.

---

### Requirement 9: Test Coverage

**User Story:** As a developer, I want automated tests for all authentication behaviours, so that regressions are caught before deployment.

#### Acceptance Criteria

1. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies the Seed_Command creates the `Admin` group.
2. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies the Seed_Command creates the `Cashier` group.
3. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies the Seed_Command creates the `adamreta` Cashier_User with the correct attributes.
4. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies login succeeds with credentials `adamreta` / `123`.
5. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies login fails when an incorrect password is supplied.
6. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies `GET /api/auth/me/` returns HTTP 401 when no session is present.
7. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies `GET /api/auth/me/` returns the correct user profile when a valid session is present.
8. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies `POST /api/auth/logout/` destroys the session and subsequent requests to `/api/auth/me/` return HTTP 401.
9. WHEN the test suite is run, THE Auth_System SHALL include a test that verifies no HTTP endpoint exists at `/api/auth/register/` (i.e., it returns HTTP 404 or 405).
