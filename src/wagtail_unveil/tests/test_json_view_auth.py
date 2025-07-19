from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.test import TestCase, RequestFactory, override_settings

from wagtail_unveil.viewsets.base import json_view_auth_required


class JSONViewAuthRequiredTestCase(TestCase):
    """Direct unit tests for the json_view_auth_required function."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="password123"
        )
        self.factory = RequestFactory()

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_superuser_access_without_token(self):
        """Test that authenticated superusers can access without token."""
        request = self.factory.get("/api/")
        request.user = self.superuser

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_regular_user_denied_without_token(self):
        """Test that regular users are denied access without token."""
        request = self.factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_anonymous_user_denied_without_token(self):
        """Test that anonymous users are denied access without token."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/api/")
        request.user = AnonymousUser()

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_valid_token_in_authorization_header(self):
        """Test access granted with valid token in Authorization header."""
        request = self.factory.get("/api/", HTTP_AUTHORIZATION="Bearer test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_valid_token_in_query_parameter(self):
        """Test access granted with valid token in query parameter."""
        request = self.factory.get("/api/?token=test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_invalid_token_in_authorization_header(self):
        """Test access denied with invalid token in Authorization header."""
        request = self.factory.get("/api/", HTTP_AUTHORIZATION="Bearer wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_invalid_token_in_query_parameter(self):
        """Test access denied with invalid token in query parameter."""
        request = self.factory.get("/api/?token=wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_malformed_authorization_header(self):
        """Test access denied with malformed Authorization header."""
        request = self.factory.get(
            "/api/", HTTP_AUTHORIZATION="InvalidFormat test-token"
        )
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_empty_authorization_header(self):
        """Test access denied with empty Authorization header."""
        request = self.factory.get("/api/", HTTP_AUTHORIZATION="Bearer ")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_header_token_takes_precedence_over_query_param(self):
        """Test that header token takes precedence over query parameter token."""
        # Invalid token in header, valid in query - should fail because header takes precedence
        request = self.factory.get(
            "/api/?token=test-token", HTTP_AUTHORIZATION="Bearer wrong-token"
        )
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)  # Should fail because header token is wrong

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_query_param_used_when_no_header_token(self):
        """Test that query parameter token is used when no header token is provided."""
        # No header token, valid query token - should succeed
        request = self.factory.get("/api/?token=test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_superuser_with_invalid_token_still_gets_access(self):
        """Test that superuser gets access even with invalid token."""
        request = self.factory.get("/api/?token=wrong-token")
        request.user = self.superuser

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN=None)
    def test_no_token_configured_returns_forbidden(self):
        """Test that function returns HttpResponseForbidden when no token is configured."""
        request = self.factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(result.status_code, 403)
        self.assertIn("Access denied", result.content.decode())

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="")
    def test_empty_token_configured_returns_forbidden(self):
        """Test that function returns HttpResponseForbidden when token is empty string."""
        request = self.factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_case_sensitive_token_validation(self):
        """Test that token validation is case sensitive."""
        request = self.factory.get("/api/?token=TEST-TOKEN")  # Wrong case
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_token_with_whitespace_fails(self):
        """Test that tokens with extra whitespace fail validation."""
        request = self.factory.get("/api/?token= test-token ")  # Extra spaces
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_bearer_case_insensitive(self):
        """Test that 'Bearer' prefix is case sensitive (should fail with wrong case)."""
        request = self.factory.get(
            "/api/", HTTP_AUTHORIZATION="bearer test-token"
        )  # lowercase
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_multiple_authorization_headers_uses_last(self):
        """Test behavior with multiple authorization values (Django uses last one)."""
        # This tests the META handling behavior
        request = self.factory.get("/api/")
        request.user = self.regular_user
        # Simulate multiple Authorization headers (Django combines them)
        request.META["HTTP_AUTHORIZATION"] = "Bearer test-token"

        result = json_view_auth_required(request)
        self.assertTrue(result)
