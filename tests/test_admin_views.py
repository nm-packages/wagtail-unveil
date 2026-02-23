from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from wagtail.test.utils import WagtailTestUtils

from wagtail_unveil.wagtail_hooks import UnveilReportPanel


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestAdminUrlsAPIView(TestCase):
    def test_returns_json(self):
        response = self.client.get(
            "/unveil-api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("urls", data)
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)
        self.assertEqual(len(data["urls"]), data["count"])

    def test_requires_api_key(self):
        response = self.client.get("/unveil-api/admin-urls/")
        self.assertEqual(response.status_code, 403)

    def test_rejects_wrong_key(self):
        response = self.client.get(
            "/unveil-api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_500_when_no_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.get(
                "/unveil-api/admin-urls/",
                HTTP_AUTHORIZATION="Bearer test-secret",
            )
            self.assertEqual(response.status_code, 500)

    def test_filter_static(self):
        response = self.client.get(
            "/unveil-api/admin-urls/?filter=static",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertFalse(url["has_parameters"], url["route"])

    def test_filter_parameterized(self):
        response = self.client.get(
            "/unveil-api/admin-urls/?filter=parameterized",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertTrue(url["has_parameters"], url["route"])


@override_settings(DEBUG=True)
class TestAdminUrlsReportView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_report_requires_login(self):
        self.client.logout()
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_requires_superuser(self):
        self.client.logout()
        User.objects.create_user(username="editor", password="password", is_staff=True)
        self.client.login(username="editor", password="password")
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_returns_html(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Admin URLs Report", content)
        self.assertIn("<table", content)

    def test_report_contains_known_url(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "wagtailadmin_home")

    def test_report_contains_counts(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn("Total:", content)
        self.assertIn("URLs", content)

    def test_report_has_test_buttons(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-btn")

    def test_report_disables_test_for_non_testable(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "disabled")
        self.assertContains(response, "POST-only view")
        self.assertContains(response, "Intentional error endpoint")

    def test_report_has_reset_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "reset-btn")
        self.assertContains(response, "Reset")

    def test_report_has_test_all_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-all-btn")
        self.assertContains(response, "Test All")

    def test_report_shows_all_rows_by_default(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-has-parameters="true"', content)
        self.assertIn('data-has-parameters="false"', content)
        self.assertNotIn('class="hidden"', content.split("<tbody>")[1].split("</tbody>")[0])

    def test_report_has_search_input(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "search-input")

    def test_report_has_sortable_headers(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-sort-col="0"', content)
        self.assertIn('data-sort-col="1"', content)
        self.assertIn('data-sort-col="2"', content)
        self.assertIn('data-sort-col="3"', content)

    def test_report_loads_static_css(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "wagtail_unveil/css/admin_urls_report.css")

    def test_report_loads_static_js(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "wagtail_unveil/js/admin_urls_report.js")

    def test_report_has_help_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "help-btn")

    def test_report_has_help_panel(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "help-panel")
        self.assertContains(response, "Django URL name")
        self.assertContains(response, "How It Works")

    def test_report_has_toggle_untestable_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "toggle-untestable-btn")
        self.assertContains(response, "Hide Untestable")

    def test_report_contains_testable_counts(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "testable")
        self.assertContains(response, "untestable")

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/unveil-report/admin-urls/")
            self.assertEqual(response.status_code, 404)


@override_settings(DEBUG=True)
class TestDashboardPanel(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.panel = UnveilReportPanel()
        self.superuser = User.objects.create_superuser(username="admin", password="password")
        self.regular_user = User.objects.create_user(username="editor", password="password", is_staff=True)

    def _render(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return self.panel.render_html({"request": request})

    def test_panel_visible_for_superuser(self):
        html = self._render(self.superuser)
        self.assertIn("View Admin URLs Report", html)
        self.assertIn("/unveil-report/admin-urls/", html)
        self.assertIn("w-panel w-panel--dashboard", html)

    def test_panel_hidden_for_non_superuser(self):
        html = self._render(self.regular_user)
        self.assertEqual(html, "")

    def test_panel_hidden_when_not_debug(self):
        with self.settings(DEBUG=False):
            html = self._render(self.superuser)
            self.assertEqual(html, "")
