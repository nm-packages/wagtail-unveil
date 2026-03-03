from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth.models import User


class BaseAPIViewTestMixin:
    """Shared API view tests. Concrete class must set api_url: str."""

    api_url: str

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
        self.assertEqual(metadata["generated_at"], "2026-03-02T12:34:56+00:00")
        self.assertIsNone(metadata["applied_filter"])
        self.assertEqual(metadata["package_version"], "9.9.9")
        self.assertEqual(metadata["total_count"], response.json()["count"])
        self.assertEqual(
            metadata["testable_count"] + metadata["untestable_count"],
            metadata["total_count"],
        )

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

    def test_report_has_test_buttons(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-test-button")

    def test_report_has_open_buttons(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-open-button")

    def test_report_uses_data_attributes_for_test_targets(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn('data-url="', content)

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
        self.assertContains(response, "wagtail_unveil/css/admin_urls_report.css")

    def test_report_loads_static_js_modules(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        script_paths = [
            "wagtail_unveil/js/report_core.js",
            "wagtail_unveil/js/report_filters.js",
            "wagtail_unveil/js/report_sorting.js",
            "wagtail_unveil/js/report_row_actions.js",
            "wagtail_unveil/js/report_batch_runner.js",
            "wagtail_unveil/js/report_components.js",
            "wagtail_unveil/js/report_bootstrap.js",
        ]

        last_index = -1
        for script_path in script_paths:
            with self.subTest(script_path=script_path):
                self.assertIn(script_path, content)
                current_index = content.index(script_path)
                self.assertGreater(current_index, last_index)
                last_index = current_index

    def test_report_has_help_panel(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "help-panel")
        self.assertContains(response, "Django URL name")
        self.assertContains(response, "How It Works")

    def test_report_has_toggle_untestable_button(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "unveil-toggle-untestable-button")

    def test_report_contains_testable_counts(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "testable")
        self.assertContains(response, "untestable")

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get(self.report_url)
            self.assertEqual(response.status_code, 404)
