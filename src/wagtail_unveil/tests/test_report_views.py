from django.urls import reverse

from wagtail_unveil.tests.base import BaseWagtailUnveilTestCase


class ReportIndexViewsTestCase(BaseWagtailUnveilTestCase):
    """Test cases for all unveil report index views (HTML pages)."""

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
        self.superuser = self.create_superuser()
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
