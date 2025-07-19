import json

from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden, JsonResponse
from django.test import TestCase, override_settings

from wagtail_unveil.api_urls import API_ENDPOINTS, api_index_view
from wagtail_unveil.viewsets.base import json_view_auth_required


class APIUrlsTestCase(TestCase):
    """Test case for API URL patterns and configuration."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="password123"
        )

    def test_api_endpoints_structure(self):
        """Test that API_ENDPOINTS has the correct structure."""
        self.assertIsInstance(API_ENDPOINTS, list)
        self.assertGreater(len(API_ENDPOINTS), 0)

        for endpoint in API_ENDPOINTS:
            self.assertIsInstance(endpoint, tuple)
            self.assertEqual(len(endpoint), 2)
            url_path, viewset_class = endpoint
            self.assertIsInstance(url_path, str)
            self.assertTrue(hasattr(viewset_class, "as_json_view"))

    def test_api_endpoints_completeness(self):
        """Test that all expected endpoints are present."""
        expected_endpoints = [
            "collection",
            "document",
            "form",
            "generic",
            "image",
            "locale",
            "modeladmin",
            "page",
            "redirect",
            "search-promotion",
            "settings",
            "site",
            "snippet",
            "user",
            "admin",
            "workflow",
            "workflow-task",
        ]

        actual_endpoints = [endpoint[0] for endpoint in API_ENDPOINTS]

        for expected in expected_endpoints:
            self.assertIn(expected, actual_endpoints)

    def test_api_endpoints_uniqueness(self):
        """Test that all endpoint URLs are unique."""
        url_paths = [endpoint[0] for endpoint in API_ENDPOINTS]
        self.assertEqual(len(url_paths), len(set(url_paths)))


class APIIndexViewTestCase(TestCase):
    """Test case for the API index view."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_superuser(self):
        """Test API index view access with authenticated superuser."""
        self.client.login(username="admin", password="password123")

        # Mock request object for the view function
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/")
        request.user = self.superuser

        response = api_index_view(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)

        # Parse response content
        data = json.loads(response.content)
        self.assertIn("endpoints", data)
        self.assertIsInstance(data["endpoints"], dict)

        # Check that all API endpoints are present
        for url_path, _ in API_ENDPOINTS:
            self.assertIn(url_path, data["endpoints"])

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_valid_token_header(self):
        """Test API index view access with valid token in Authorization header."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/", HTTP_AUTHORIZATION="Bearer test-token")

        # Create a regular user (not superuser)
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="password123"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_valid_token_query(self):
        """Test API index view access with valid token in query parameter."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/?token=test-token")

        # Create a regular user (not superuser)
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular2", email="regular2@example.com", password="password123"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_invalid_token(self):
        """Test API index view access denied with invalid token."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/", HTTP_AUTHORIZATION="Bearer wrong-token")

        # Create a regular user (not superuser)
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular3", email="regular3@example.com", password="password123"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    def test_api_index_view_without_token_config(self):
        """Test API index view access denied when no token is configured."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/")

        # Create a regular user (not superuser)
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular4", email="regular4@example.com", password="password123"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)


class JSONViewAuthTestCase(TestCase):
    """Test case for JSON view authentication function."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="password123"
        )

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_superuser_access(self):
        """Test that authenticated superusers can access without token."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/")
        request.user = self.superuser

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_regular_user_no_token(self):
        """Test that regular users cannot access without token."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_valid_token_header(self):
        """Test access with valid token in Authorization header."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/", HTTP_AUTHORIZATION="Bearer test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_valid_token_query(self):
        """Test access with valid token in query parameter."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/?token=test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_invalid_token_header(self):
        """Test access denied with invalid token in Authorization header."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/", HTTP_AUTHORIZATION="Bearer wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_invalid_token_query(self):
        """Test access denied with invalid token in query parameter."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/?token=wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_malformed_authorization_header(self):
        """Test access denied with malformed Authorization header."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/", HTTP_AUTHORIZATION="InvalidFormat test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN=None)
    def test_auth_required_no_token_configured(self):
        """Test that access is denied when no token is configured."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/")
        request.user = self.regular_user

        # This should return HttpResponseForbidden, not a boolean
        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="")
    def test_auth_required_empty_token_configured(self):
        """Test that access is denied when token is empty string."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)


class URLPatternsTestCase(TestCase):
    """Test case for URL pattern generation."""

    def test_url_patterns_generated(self):
        """Test that URL patterns are properly generated from API_ENDPOINTS."""
        from wagtail_unveil.api_urls import urlpatterns

        # Should have one pattern for the index view plus one for each endpoint
        expected_count = 1 + len(API_ENDPOINTS)
        self.assertEqual(len(urlpatterns), expected_count)

    def test_all_endpoints_have_url_patterns(self):
        """Test that each endpoint in API_ENDPOINTS has a corresponding URL pattern."""
        from wagtail_unveil.api_urls import urlpatterns

        # Extract URL patterns (skip the index pattern)
        api_patterns = urlpatterns[1:]

        # Check that we have the right number of patterns
        self.assertEqual(len(api_patterns), len(API_ENDPOINTS))

        # Verify each endpoint has a pattern
        for url_path, viewset_class in API_ENDPOINTS:
            pattern_found = False
            for pattern in api_patterns:
                if hasattr(pattern, "pattern") and f"{url_path}/" in str(
                    pattern.pattern
                ):
                    pattern_found = True
                    break
            self.assertTrue(
                pattern_found, f"No URL pattern found for endpoint: {url_path}"
            )


class IntegrationTestCase(TestCase):
    """Integration tests for the complete API URL system."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_endpoints_consistency(self):
        """Test that the API index returns all configured endpoints."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/unveil/api/")
        request.user = self.superuser

        response = api_index_view(request)
        data = json.loads(response.content)

        # Verify all endpoints from API_ENDPOINTS are in the response
        endpoint_names = [endpoint[0] for endpoint in API_ENDPOINTS]
        response_endpoints = list(data["endpoints"].keys())

        self.assertEqual(set(endpoint_names), set(response_endpoints))

    def test_viewset_instantiation(self):
        """Test that all ViewSet classes can be instantiated."""
        for url_path, viewset_class in API_ENDPOINTS:
            try:
                instance = viewset_class()
                self.assertTrue(hasattr(instance, "as_json_view"))
            except Exception as e:
                self.fail(f"Failed to instantiate {viewset_class.__name__}: {e}")
