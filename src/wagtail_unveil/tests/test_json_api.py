import json

from django.http import HttpResponseForbidden, JsonResponse
from django.test import override_settings

from wagtail_unveil.api_urls import API_ENDPOINTS, api_index_view
from wagtail_unveil.viewsets.base import json_view_auth_required
from wagtail_unveil.tests.base import BaseWagtailUnveilTestCase


class JSONAPIConfigurationTestCase(BaseWagtailUnveilTestCase):
    """Test case for JSON API URL patterns and configuration."""

    def setUp(self):
        """Set up test data."""
        self.create_test_users()

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

    def test_viewset_instantiation(self):
        """Test that all ViewSet classes can be instantiated."""
        for url_path, viewset_class in API_ENDPOINTS:
            try:
                instance = viewset_class()
                self.assertTrue(hasattr(instance, "as_json_view"))
            except Exception as e:
                self.fail(f"Failed to instantiate {viewset_class.__name__}: {e}")


class JSONAPIIndexViewTestCase(BaseWagtailUnveilTestCase):
    """Test case for the JSON API index view."""

    def setUp(self):
        """Set up test data."""
        self.superuser = self.create_superuser()

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_superuser(self):
        """Test API index view access with authenticated superuser."""
        self.client.login(username="admin", password="password123")

        # Mock request object for the view function
        factory = self.request_factory
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
        factory = self.request_factory
        request = factory.get("/unveil/api/", HTTP_AUTHORIZATION="Bearer test-token")

        # Create a regular user (not superuser)
        regular_user = self.create_regular_user(
            username="regular", email="regular@example.com"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_valid_token_query(self):
        """Test API index view access with valid token in query parameter."""
        factory = self.request_factory
        request = factory.get("/unveil/api/?token=test-token")

        # Create a regular user (not superuser)
        regular_user = self.create_regular_user(
            username="regular2", email="regular2@example.com"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_index_view_with_invalid_token(self):
        """Test API index view access denied with invalid token."""
        factory = self.request_factory
        request = factory.get("/unveil/api/", HTTP_AUTHORIZATION="Bearer wrong-token")

        # Create a regular user (not superuser)
        regular_user = self.create_regular_user(
            username="regular3", email="regular3@example.com"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    def test_api_index_view_without_token_config(self):
        """Test API index view access denied when no token is configured."""
        factory = self.request_factory
        request = factory.get("/unveil/api/")

        # Create a regular user (not superuser)
        regular_user = self.create_regular_user(
            username="regular4", email="regular4@example.com"
        )
        request.user = regular_user

        response = api_index_view(request)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_api_endpoints_consistency(self):
        """Test that the API index returns all configured endpoints."""
        factory = self.request_factory
        request = factory.get("/unveil/api/")
        request.user = self.superuser

        response = api_index_view(request)
        data = json.loads(response.content)

        # Verify all endpoints from API_ENDPOINTS are in the response
        endpoint_names = [endpoint[0] for endpoint in API_ENDPOINTS]
        response_endpoints = list(data["endpoints"].keys())

        self.assertEqual(set(endpoint_names), set(response_endpoints))


class JSONAPIAuthenticationTestCase(BaseWagtailUnveilTestCase):
    """Test case for JSON API authentication and authorization logic."""

    def setUp(self):
        """Set up test data."""
        self.create_test_users()

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_superuser_access(self):
        """Test that authenticated superusers can access without token."""
        factory = self.request_factory
        request = factory.get("/api/")
        request.user = self.superuser

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_regular_user_no_token(self):
        """Test that regular users cannot access without token."""
        factory = self.request_factory
        request = factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_valid_token_header(self):
        """Test access with valid token in Authorization header."""
        factory = self.request_factory
        request = factory.get("/api/", HTTP_AUTHORIZATION="Bearer test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_valid_token_query(self):
        """Test access with valid token in query parameter."""
        factory = self.request_factory
        request = factory.get("/api/?token=test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertTrue(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_invalid_token_header(self):
        """Test access denied with invalid token in Authorization header."""
        factory = self.request_factory
        request = factory.get("/api/", HTTP_AUTHORIZATION="Bearer wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_invalid_token_query(self):
        """Test access denied with invalid token in query parameter."""
        factory = self.request_factory
        request = factory.get("/api/?token=wrong-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test-token")
    def test_auth_required_malformed_authorization_header(self):
        """Test access denied with malformed Authorization header."""
        factory = self.request_factory
        request = factory.get("/api/", HTTP_AUTHORIZATION="InvalidFormat test-token")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertFalse(result)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN=None)
    def test_auth_required_no_token_configured(self):
        """Test that access is denied when no token is configured."""
        factory = self.request_factory
        request = factory.get("/api/")
        request.user = self.regular_user

        # This should return HttpResponseForbidden, not a boolean
        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)

    @override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="")
    def test_auth_required_empty_token_configured(self):
        """Test that access is denied when token is empty string."""
        factory = self.request_factory
        request = factory.get("/api/")
        request.user = self.regular_user

        result = json_view_auth_required(request)
        self.assertIsInstance(result, HttpResponseForbidden)


@override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test_token_123")
class JSONAPIEndpointsTestCase(BaseWagtailUnveilTestCase):
    """Test all JSON API endpoints for reports via HTTP client requests."""

    # API slugs for all reports
    API_SLUGS = [
        "collection",
        "document",
        "form",
        "generic",
        "image",
        "locale",
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

    def setUp(self):
        self.superuser = self.create_superuser()
        self.client.login(username="admin", password="password123")

    def _assert_json_response(self, response, expected_status=200):
        """Helper method to assert common JSON response properties."""
        if expected_status == 200:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/json")
            json_data = response.json()
            self.assertIn("results", json_data)
            self.assertIsInstance(json_data["results"], list)
            return json_data
        else:
            self.assertIn(response.status_code, [200, 403])
            if response.status_code == 403:
                self.assertIn("Invalid or missing token", response.content.decode())
            else:
                # If it's 200, still validate the JSON structure
                self.assertEqual(response["Content-Type"], "application/json")
                json_data = response.json()
                self.assertIn("results", json_data)
                self.assertIsInstance(json_data["results"], list)

    def test_json_endpoint_without_token(self):
        """Test that JSON API endpoints require authentication token"""
        url = "/unveil/api/collection/"
        response = self.client.get(url)
        self._assert_json_response(response, expected_status=403)

    def test_json_endpoint_with_invalid_token(self):
        """Test that JSON API endpoints reject invalid tokens"""
        url = "/unveil/api/collection/"
        response = self.client.get(url, {"token": "invalid_token"})
        self._assert_json_response(response, expected_status=403)

    def test_json_endpoint_with_query_param_token(self):
        """Test JSON API endpoint with valid token as query parameter"""
        url = "/unveil/api/collection/"
        response = self.client.get(url, {"token": "test_token_123"})
        self._assert_json_response(response)

    def test_json_endpoint_with_header_token(self):
        """Test JSON API endpoint with valid token in header"""
        url = "/unveil/api/collection/"
        response = self.client.get(url, HTTP_X_API_TOKEN="test_token_123")
        self._assert_json_response(response)

    def test_all_reports_have_json_api_endpoints(self):
        """Test that all reports have working JSON API endpoints"""
        for slug in self.API_SLUGS:
            with self.subTest(report=slug):
                url = f"/unveil/api/{slug}/"
                response = self.client.get(url, {"token": "test_token_123"})
                self._assert_json_response(response)

    def test_json_response_structure(self):
        """Test that JSON API responses have the correct structure"""
        url = "/unveil/api/admin/"  # Admin report has predictable data
        response = self.client.get(url, {"token": "test_token_123"})
        json_data = self._assert_json_response(response)
        if json_data["results"]:
            entry = json_data["results"][0]
            required_fields = ["id", "model_name", "url_type", "url"]
            for field in required_fields:
                self.assertIn(field, entry, f"Missing field '{field}' in JSON response")
                self.assertIsNotNone(
                    entry[field], f"Field '{field}' should not be None"
                )
