from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from wagtail.test.utils import WagtailTestUtils


@override_settings(DEBUG=True)
class TestSettingsReportView(WagtailTestUtils, TestCase):
    report_url = "/unveil/report/settings/"

    def setUp(self):
        self.login()

    def assert_masked_api_key_output(self, response, *, secret):
        self.assertNotContains(response, secret)
        self.assertContains(response, f"Configured ({len(secret)} chars)")
        self.assertContains(response, "Environment variable")

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
        self.assertContains(response, "Wagtail Unveil Settings")

    def test_report_has_settings_page_body_class(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, '<body class="settings-report-page">')

    def test_report_shows_diagnostics_sections(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "Package Settings")
        self.assertContains(response, "Runtime Access")
        self.assertContains(response, "Versions")
        self.assertContains(response, "URL Diagnostics")
        self.assertContains(response, "WAGTAIL_UNVEIL_API_KEY")
        self.assertContains(response, "/unveil/api/v1/backend-urls/")
        self.assertContains(response, "/unveil/report/frontend-urls/")

    @patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "full-secret-value"})
    def test_report_masks_api_key_value(self):
        response = self.client.get(self.report_url)
        self.assert_masked_api_key_output(response, secret="full-secret-value")

    def test_settings_nav_link_is_active(self):
        response = self.client.get(self.report_url)
        self.assertContains(
            response,
            '<a class="active settings-link" href="/unveil/report/settings/">Settings</a>',
            html=True,
        )

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get(self.report_url)
            self.assertEqual(response.status_code, 404)
