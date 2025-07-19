from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class UnveilReportsIndexViewTest(TestCase):
    """Test cases for all unveil report index views."""

    # Define all report configurations in one place
    REPORT_CONFIGS = [
        ("collection", "Collection"),
        ("document", "Document"),
        ("form", "Form"),
        ("generic", "Generic"),
        ("image", "Image"),
        ("locale", "Locale"),
        ("page", "Page"),
        ("redirect", "Redirect"),
        ("search_promotion", "Search Promotion"),
        ("settings", "Settings"),
        ("site", "Site"),
        ("snippet", "Snippet"),
        ("user", "User"),
        ("admin", "Admin"),
        ("workflow", "Workflow"),
        ("workflow_task", "Workflow Task"),
    ]

    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

    def _test_report_index_route(self, report_name, display_name):
        """Helper method to test a report index route."""
        url = reverse(f"unveil_{report_name}_report:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtail_unveil/unveil_url_report.html")
        self.assertContains(response, f"Unveil {display_name}")

    def test_all_report_index_routes(self):
        """Test all report index routes using subTest for better error reporting."""
        for report_name, display_name in self.REPORT_CONFIGS:
            with self.subTest(report=report_name):
                self._test_report_index_route(report_name, display_name)


@override_settings(WAGTAIL_UNVEIL_JSON_TOKEN="test_token_123")
class UnveilReportsJSONAPITest(TestCase):
    """Test the JSON API endpoints for all reports"""

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
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
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
