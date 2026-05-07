from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


class SeedUsersCommandTests(TestCase):
    """Tests for the seed_users management command (Requirements 8.1–8.3)."""

    def test_seed_creates_admin_group(self):
        """8.1 — seed_users creates the Admin group."""
        call_command("seed_users", verbosity=0)
        self.assertTrue(Group.objects.filter(name="Admin").exists())

    def test_seed_creates_cashier_group(self):
        """8.2 — seed_users creates the Cashier group."""
        call_command("seed_users", verbosity=0)
        self.assertTrue(Group.objects.filter(name="Cashier").exists())

    def test_seed_creates_adamreta_user(self):
        """8.3 — seed_users creates adamreta with correct attributes and Cashier group."""
        call_command("seed_users", verbosity=0)

        user = User.objects.get(username="adamreta")
        self.assertEqual(user.first_name, "Adam")
        self.assertEqual(user.last_name, "Reta")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.groups.filter(name="Cashier").exists())


class LoginEndpointTests(TestCase):
    """Tests for POST /api/auth/login/ (Requirements 4.1, 4.3)."""

    def setUp(self):
        self.client = APIClient()
        call_command("seed_users", verbosity=0)

    def test_login_success(self):
        """8.4 — login with adamreta / 123 returns HTTP 200."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "adamreta", "password": "123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self):
        """8.5 — login with wrong password returns HTTP 400."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "adamreta", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class MeEndpointTests(TestCase):
    """Tests for GET /api/auth/me/ (Requirements 6.1–6.3)."""

    def setUp(self):
        self.client = APIClient()
        call_command("seed_users", verbosity=0)

    def test_me_unauthenticated(self):
        """8.6 — GET /api/auth/me/ without a session returns HTTP 401."""
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_authenticated(self):
        """8.7 — login then GET /api/auth/me/ returns HTTP 200 with correct profile."""
        # Log in first
        self.client.post(
            "/api/auth/login/",
            {"username": "adamreta", "password": "123"},
            format="json",
        )

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["username"], "adamreta")
        self.assertIn("groups", data)
        self.assertIn("is_staff", data)
        self.assertIn("is_superuser", data)
        self.assertFalse(data["is_staff"])
        self.assertFalse(data["is_superuser"])
        self.assertIn("Cashier", data["groups"])


class LogoutEndpointTests(TestCase):
    """Tests for POST /api/auth/logout/ (Requirement 5.1)."""

    def setUp(self):
        self.client = APIClient()
        call_command("seed_users", verbosity=0)

    def test_logout_destroys_session(self):
        """8.8 — login → logout → GET /me/ returns HTTP 401."""
        # Log in
        self.client.post(
            "/api/auth/login/",
            {"username": "adamreta", "password": "123"},
            format="json",
        )

        # Confirm we are authenticated
        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, 200)

        # Log out
        logout_response = self.client.post("/api/auth/logout/")
        self.assertEqual(logout_response.status_code, 200)

        # Session should be gone
        me_after = self.client.get("/api/auth/me/")
        self.assertEqual(me_after.status_code, 401)


class NoRegisterEndpointTests(TestCase):
    """Tests that no public registration endpoint exists (Requirement 7.3)."""

    def setUp(self):
        self.client = APIClient()

    def test_no_register_endpoint(self):
        """8.9 — GET and POST /api/auth/register/ return HTTP 404 or 405."""
        get_response = self.client.get("/api/auth/register/")
        self.assertIn(get_response.status_code, [404, 405])

        post_response = self.client.post(
            "/api/auth/register/",
            {"username": "newuser", "password": "pass"},
            format="json",
        )
        self.assertIn(post_response.status_code, [404, 405])


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# Feature: cashier-auth
# ---------------------------------------------------------------------------
import io

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

# Shared strategy for generating safe usernames.
# Django's UnicodeUsernameValidator allows letters, digits, and @/./+/-/_
# but rejects many non-ASCII letters.  We restrict to ASCII alphanumeric to
# keep generated usernames valid across all Django versions.
_username_st = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
)

# Strategy for arbitrary printable passwords (non-empty, ASCII printable).
_password_st = st.text(
    min_size=1,
    max_size=128,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd")),
)


# ---------------------------------------------------------------------------
# Property 1: Login with valid credentials returns HTTP 200 and all required
# profile fields.
# Validates: Requirements 4.1, 4.2
# ---------------------------------------------------------------------------
class Property1LoginValidCredentials(HypothesisTestCase):
    # Feature: cashier-auth, Property 1: For any active user with a known
    # password, POST /api/auth/login/ with correct credentials SHALL return
    # HTTP 200 and a JSON body containing all required fields.

    @settings(max_examples=20, deadline=None)
    @given(username=_username_st, password=_password_st)
    def test_login_valid_credentials_returns_200_with_full_profile(
        self, username, password
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            is_active=True,
        )
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        required_fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "groups",
            "is_staff",
            "is_superuser",
        ]
        for field in required_fields:
            self.assertIn(field, data, msg=f"Missing field: {field}")
        self.assertIsInstance(data["groups"], list)
        self.assertTrue(
            all(isinstance(g, str) for g in data["groups"]),
            "groups must be a list of strings",
        )


# ---------------------------------------------------------------------------
# Property 2: Login with wrong password returns HTTP 400.
# Validates: Requirements 4.3
# ---------------------------------------------------------------------------
class Property2LoginWrongPassword(HypothesisTestCase):
    # Feature: cashier-auth, Property 2: For any existing user, POST
    # /api/auth/login/ with an incorrect password SHALL return HTTP 400 and
    # the response body SHALL NOT contain a session cookie.

    @settings(max_examples=20, deadline=None)
    @given(username=_username_st, correct_password=_password_st)
    def test_login_wrong_password_returns_400(self, username, correct_password):
        User.objects.create_user(username=username, password=correct_password)
        # Guarantee the wrong password differs from the correct one.
        wrong_password = correct_password + "_WRONG"
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": wrong_password},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        # No session cookie should be set on a failed login.
        self.assertNotIn("sessionid", response.cookies)


# ---------------------------------------------------------------------------
# Property 3: Logout destroys session; subsequent /me/ returns HTTP 401.
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------
class Property3LogoutDestroysSession(HypothesisTestCase):
    # Feature: cashier-auth, Property 3: For any authenticated user, after a
    # successful POST to /api/auth/logout/ (HTTP 200), a subsequent GET to
    # /api/auth/me/ SHALL return HTTP 401.

    @settings(max_examples=20, deadline=None)
    @given(username=_username_st, password=_password_st)
    def test_logout_destroys_session(self, username, password):
        User.objects.create_user(username=username, password=password, is_active=True)
        client = APIClient()

        # Log in.
        login_response = client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)

        # Log out.
        logout_response = client.post("/api/auth/logout/")
        self.assertEqual(logout_response.status_code, 200)

        # /me/ must now return 401.
        me_response = client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, 401)


# ---------------------------------------------------------------------------
# Property 4: /me/ returns profile matching DB record for any authenticated
# user.
# Validates: Requirements 6.1, 6.2
# ---------------------------------------------------------------------------
class Property4MeMatchesDBRecord(HypothesisTestCase):
    # Feature: cashier-auth, Property 4: For any active user who has logged in,
    # GET /api/auth/me/ SHALL return HTTP 200 and a JSON body where username,
    # groups, is_staff, and is_superuser match the user's actual database record.

    @settings(max_examples=20, deadline=None)
    @given(
        username=_username_st,
        password=_password_st,
        is_staff=st.booleans(),
        is_superuser=st.booleans(),
    )
    def test_me_profile_matches_db_record(
        self, username, password, is_staff, is_superuser
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            is_active=True,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        # Optionally assign a group so the groups list is non-trivial sometimes.
        group, _ = Group.objects.get_or_create(name="TestGroup")
        user.groups.add(group)

        client = APIClient()
        client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )

        response = client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Reload from DB to get the authoritative state.
        user.refresh_from_db()
        expected_groups = list(user.groups.values_list("name", flat=True))

        self.assertEqual(data["username"], user.username)
        self.assertEqual(sorted(data["groups"]), sorted(expected_groups))
        self.assertEqual(data["is_staff"], user.is_staff)
        self.assertEqual(data["is_superuser"], user.is_superuser)


# ---------------------------------------------------------------------------
# Property 5: seed_users is idempotent across multiple runs.
# Validates: Requirements 8.1, 8.2, 8.4, 8.5
# ---------------------------------------------------------------------------
class Property5SeedUsersIdempotent(HypothesisTestCase):
    # Feature: cashier-auth, Property 5: For any number of executions of
    # seed_users (≥ 1), the resulting state SHALL contain exactly one Admin
    # group, exactly one Cashier group, and exactly one adamreta user.

    @settings(max_examples=20, deadline=None)
    @given(num_runs=st.integers(min_value=1, max_value=5))
    def test_seed_users_is_idempotent(self, num_runs):
        for _ in range(num_runs):
            call_command("seed_users", verbosity=0)

        self.assertEqual(Group.objects.filter(name="Admin").count(), 1)
        self.assertEqual(Group.objects.filter(name="Cashier").count(), 1)
        self.assertEqual(User.objects.filter(username="adamreta").count(), 1)


# ---------------------------------------------------------------------------
# Property 6: seed_users stdout contains a message for each resource.
# Validates: Requirements 8.7
# ---------------------------------------------------------------------------
class Property6SeedUsersStdoutMessages(HypothesisTestCase):
    # Feature: cashier-auth, Property 6: For any execution of seed_users, the
    # captured stdout SHALL contain a message for each of the three managed
    # resources (Admin group, Cashier group, adamreta user).

    @settings(max_examples=20, deadline=None)
    @given(
        admin_pre_exists=st.booleans(),
        cashier_pre_exists=st.booleans(),
        user_pre_exists=st.booleans(),
    )
    def test_seed_users_stdout_contains_message_for_each_resource(
        self, admin_pre_exists, cashier_pre_exists, user_pre_exists
    ):
        # Optionally pre-create resources to exercise the "already exists" path.
        if admin_pre_exists:
            Group.objects.get_or_create(name="Admin")
        if cashier_pre_exists:
            Group.objects.get_or_create(name="Cashier")
        if user_pre_exists:
            user, created = User.objects.get_or_create(
                username="adamreta",
                defaults={
                    "first_name": "Adam",
                    "last_name": "Reta",
                    "is_staff": False,
                    "is_superuser": False,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("123")
                user.save()

        captured = io.StringIO()
        call_command("seed_users", stdout=captured, verbosity=1)
        output = captured.getvalue()

        # The command must emit at least one line mentioning each resource.
        self.assertRegex(output, r"(?i)admin", msg="No message for Admin group")
        self.assertRegex(output, r"(?i)cashier", msg="No message for Cashier group")
        self.assertRegex(output, r"(?i)adamreta", msg="No message for adamreta user")
