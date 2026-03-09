from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings

from wagtail_unveil.api_contract import get_api_contract


class BaseAPIViewTestMixin:
    """Shared API view tests. Concrete class must set api_url: str."""

    api_url: str
    api_version: str = "v1"

    def test_returns_json(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("urls", data)
        self.assertIn("count", data)
        self.assertIn("metadata", data)
        self.assertGreater(data["count"], 0)
        self.assertEqual(len(data["urls"]), data["count"])
        self.assertEqual(data["metadata"]["total_count"], data["count"])

    @patch("wagtail_unveil.views._get_package_version", return_value="9.9.9")
    @patch("wagtail_unveil.views.timezone.now")
    def test_returns_metadata(self, mock_now, _mock_version):
        mock_now.return_value = datetime(2026, 3, 2, 12, 34, 56, tzinfo=timezone.utc)

        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        metadata = response.json()["metadata"]
        contract = get_api_contract(self.api_version)
        self.assertEqual(metadata["api_version"], self.api_version)
        self.assertEqual(metadata["api_lifecycle"]["status"], contract.status)
        self.assertEqual(
            metadata["api_lifecycle"]["deprecated_on"],
            contract.deprecated_on.isoformat() if contract.deprecated_on else None,
        )
        self.assertEqual(
            metadata["api_lifecycle"]["sunset_on"],
            contract.sunset_on.isoformat() if contract.sunset_on else None,
        )
        self.assertEqual(metadata["generated_at"], "2026-03-02T12:34:56+00:00")
        self.assertIsNone(metadata["applied_filter"])
        self.assertEqual(metadata["package_version"], "9.9.9")
        self.assertEqual(metadata["total_count"], response.json()["count"])
        self.assertEqual(
            metadata["testable_count"] + metadata["untestable_count"],
            metadata["total_count"],
        )
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)

    def test_requires_api_key(self):
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 403)

    def test_rejects_wrong_key(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_500_when_no_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY=""):
                response = self.client.get(
                    self.api_url,
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )
                self.assertEqual(response.status_code, 500)

    def test_uses_settings_fallback_when_env_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY="test-from-settings"):
                response = self.client.get(
                    self.api_url,
                    HTTP_AUTHORIZATION="Bearer test-from-settings",
                )
                self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False)
    def test_non_bearer_authorization_header_does_not_trigger_missing_api_key_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY=""):
                response = self.client.get(
                    self.api_url,
                    HTTP_AUTHORIZATION="Basic abc123",
                )
                self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_allows_superuser_session_without_authorization_header(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")

        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    def test_rejects_staff_session_without_authorization_header(self):
        User.objects.create_user(username="editor", password="password", is_staff=True)
        self.client.login(username="editor", password="password")

        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_rejects_superuser_session_without_authorization_header_when_not_debug(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")

        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_rejects_wrong_authorization_header_even_for_superuser_session(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")

        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_allows_superuser_session_with_non_bearer_authorization_header(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")

        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Basic abc123",
        )

        self.assertEqual(response.status_code, 200)


class BaseReportViewTestMixin:
    """Shared report view tests. Concrete class must set report_url: str and report_title: str."""

    report_url: str
    report_title: str

    def test_report_requires_login(self):
        self.client.logout()
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 302)

    def test_report_requires_superuser(self):
        self.client.logout()
        User.objects.create_user(username="editor", password="password", is_staff=True)
        self.client.login(username="editor", password="password")
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 302)

    def test_report_returns_html(self):
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(self.report_title, content)
        self.assertIn("<table", content)

    def test_report_contains_counts(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn("Total:", content)
        self.assertIn("URLs", content)

    def test_report_has_testing_columns(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "<th>Test</th>", html=True)
        self.assertContains(response, "<th>Status</th>", html=True)

    def test_report_exposes_api_configuration(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn('data-api-url="', content)
        self.assertIn('data-report-kind="', content)
        self.assertIn('data-report-state="loading"', content)
        self.assertIn('data-loading-feedback="hidden"', content)

    def test_report_has_shell_wrapper(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'class="report-shell"')

    def test_report_has_loading_screen(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'class="report-screen report-screen-loading"')
        self.assertContains(response, "Loading report")

    def test_report_has_error_screen(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'class="report-screen report-screen-error"')
        self.assertContains(response, 'id="report-retry-button"')

    def test_report_has_noscript_message(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "JavaScript is required to load this report.")

    def test_report_does_not_use_inline_onclick_handlers(self):
        response = self.client.get(self.report_url)
        self.assertNotContains(response, "onclick=")

    def test_report_has_reset_button(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-reset-button")

    def test_report_has_test_all_button(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-test-all-button")

    def test_report_has_search_input(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "search-input")

    def test_report_has_sortable_headers(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn('data-sort-col="0"', content)
        self.assertIn('data-sort-col="1"', content)
        self.assertIn('data-sort-col="2"', content)
        self.assertIn('data-sort-col="3"', content)

    def test_report_loads_static_css(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "wagtail_unveil/css/admin_urls_report.min.css")

    def test_report_loads_static_js_bundle(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn("wagtail_unveil/js/report.bundle.min.js", content)

    def test_report_has_toggle_untestable_button(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-toggle-untestable-button")

    def test_report_contains_testable_counts(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "testable")
        self.assertContains(response, "untestable")

    def test_report_has_settings_nav_link(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'href="/unveil/report/settings/"')
        self.assertContains(response, ">Settings<")

    def test_report_starts_with_empty_table_body(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn("<tbody></tbody>", content)

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get(self.report_url)
            self.assertEqual(response.status_code, 404)
