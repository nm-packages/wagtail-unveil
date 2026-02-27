from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from wagtail.test.utils import WagtailTestUtils

from wagtail_unveil.wagtail_hooks import UnveilReportPanel


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestFrontendUrlsAPIView(TestCase):
    def test_returns_json(self):
        response = self.client.get(
            "/unveil-api/frontend-urls/",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("urls", data)
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)
        self.assertEqual(len(data["urls"]), data["count"])

    def test_requires_api_key(self):
        response = self.client.get("/unveil-api/frontend-urls/")
        self.assertEqual(response.status_code, 403)

    def test_rejects_wrong_key(self):
        response = self.client.get(
            "/unveil-api/frontend-urls/",
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_500_when_no_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY=""):
                response = self.client.get(
                    "/unveil-api/frontend-urls/",
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )
                self.assertEqual(response.status_code, 500)

    def test_uses_settings_fallback_when_env_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY="test-from-settings"):
                response = self.client.get(
                    "/unveil-api/frontend-urls/",
                    HTTP_AUTHORIZATION="Bearer test-from-settings",
                )
                self.assertEqual(response.status_code, 200)

    def test_filter_pages(self):
        response = self.client.get(
            "/unveil-api/frontend-urls/?filter=pages",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertEqual(url["source"], "page")

    def test_filter_resolver(self):
        response = self.client.get(
            "/unveil-api/frontend-urls/?filter=resolver",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertEqual(url["source"], "resolver")


@override_settings(DEBUG=True)
class TestFrontendUrlsReportView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_report_requires_login(self):
        self.client.logout()
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_requires_superuser(self):
        self.client.logout()
        User.objects.create_user(username="editor", password="password", is_staff=True)
        self.client.login(username="editor", password="password")
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_returns_html(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Frontend URLs Report", content)
        self.assertIn("<table", content)

    def test_report_contains_counts(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        content = response.content.decode()
        self.assertIn("Total:", content)
        self.assertIn("URLs", content)

    def test_report_has_test_buttons(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "test-btn")

    def test_report_has_reset_button(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "reset-btn")

    def test_report_has_test_all_button(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "test-all-btn")
        self.assertContains(response, "Test All")

    def test_report_has_search_input(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "search-input")

    def test_report_has_sortable_headers(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        content = response.content.decode()
        self.assertIn('data-sort-col="0"', content)
        self.assertIn('data-sort-col="1"', content)
        self.assertIn('data-sort-col="2"', content)
        self.assertIn('data-sort-col="3"', content)
        self.assertIn('data-sort-col="4"', content)

    def test_report_loads_static_css(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "wagtail_unveil/css/admin_urls_report.css")

    def test_report_loads_static_js(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "wagtail_unveil/js/admin_urls_report.js")

    def test_report_has_help_panel(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "help-panel")
        self.assertContains(response, "How It Works")

    def test_report_has_toggle_untestable_button(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "toggle-untestable-btn")
        self.assertContains(response, "Hide Untestable")

    def test_report_contains_testable_counts(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "testable")
        self.assertContains(response, "untestable")

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/unveil-report/frontend-urls/")
            self.assertEqual(response.status_code, 404)

    def test_report_shows_source_column(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "Source")
        self.assertContains(response, 'data-source="page"')


class TestDashboardPanelFrontendLink(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.panel = UnveilReportPanel()
        self.superuser = User.objects.create_superuser(username="admin", password="password")

    @override_settings(DEBUG=True)
    def test_panel_shows_frontend_link(self):
        request = self.factory.get("/admin/")
        request.user = self.superuser
        html = self.panel.render_html({"request": request})
        self.assertIn("View Frontend URLs Report", html)
        self.assertIn("/unveil-report/frontend-urls/", html)


@override_settings(DEBUG=True)
class TestFrontendReportPagesPerType(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_no_limit_message_by_default(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertNotContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_shows_limit_message(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "Showing 1 page per type")
        self.assertContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=3)
    def test_shows_plural_limit_message(self):
        response = self.client.get("/unveil-report/frontend-urls/")
        self.assertContains(response, "Showing 3 pages per type")
