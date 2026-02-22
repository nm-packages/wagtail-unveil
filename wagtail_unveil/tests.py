from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from wagtail_unveil.urls import AdminURL, get_admin_urls


class TestGetAdminUrls(TestCase):
    def setUp(self):
        self.urls = get_admin_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_all_urls_start_with_admin(self):
        for url in self.urls:
            self.assertTrue(url.route.startswith("admin/"), url.route)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, AdminURL)
        self.assertIsInstance(url.route, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.namespace, str)
        self.assertIsInstance(url.has_parameters, bool)
        self.assertIsInstance(url.view_name, str)

    def test_known_url_present(self):
        names = {url.name for url in self.urls}
        self.assertIn("wagtailadmin_home", names)

    def test_has_parameters_detection(self):
        parameterized = [url for url in self.urls if url.has_parameters]
        static = [url for url in self.urls if not url.has_parameters]
        self.assertGreater(len(parameterized), 0)
        self.assertGreater(len(static), 0)
        for url in static:
            self.assertNotIn("<", url.route)


class TestShowAdminUrlsCommand(TestCase):
    def _call(self, *args):
        out = StringIO()
        call_command("show_admin_urls", *args, stdout=out)
        return out.getvalue()

    def test_command_runs(self):
        output = self._call()
        self.assertIn("Total:", output)

    def test_output_contains_urls(self):
        output = self._call()
        self.assertIn("wagtailadmin_home", output)

    def test_static_filter(self):
        output = self._call("--static")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertNotIn("<", line)

    def test_parameterized_filter(self):
        output = self._call("--parameterized")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertTrue("<" in line or "(" in line, line)


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
class TestAdminUrlsReportView(TestCase):
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
        self.assertIn("Static:", content)
        self.assertIn("Parameterized:", content)

    def test_report_has_test_buttons(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-btn")

    def test_report_disables_test_for_parameterized(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "disabled")

    def test_report_has_test_all_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-all-btn")
        self.assertContains(response, "Test All")

    def test_report_default_filter_is_static(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-filter="static">Static</button>', content)
        self.assertNotIn(
            'class="filter-btn active" data-filter="all"', content
        )
        self.assertIn(
            'class="filter-btn active" data-filter="static"', content
        )

    def test_report_parameterized_rows_hidden_by_default(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-has-parameters="true" class="hidden"', content)
        self.assertNotIn('data-has-parameters="false" class="hidden"', content)

    def test_report_loads_static_css(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(
            response, "wagtail_unveil/css/admin_urls_report.css"
        )

    def test_report_loads_static_js(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(
            response, "wagtail_unveil/js/admin_urls_report.js"
        )

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/unveil-report/admin-urls/")
            self.assertEqual(response.status_code, 404)
