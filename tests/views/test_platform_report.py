from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from tests.views.support import (
    assert_html_response_is_not_cacheable,
    production_report_settings,
)
from wagtail_unveil.api_contract import get_latest_stable_api_contract


@override_settings(DEBUG=True)
class TestPlatformReportView(WagtailTestUtils, TestCase):
    report_url = "/unveil/report/platform/"

    def setUp(self):
        self.login()

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
        assert_html_response_is_not_cacheable(self, response)
        self.assertContains(response, "Platform Report")

    def test_report_includes_platform_api_url(self):
        response = self.client.get(self.report_url)
        latest_contract = get_latest_stable_api_contract()
        api_url = reverse(f"wagtail_unveil:{latest_contract.platform_url_name}")
        self.assertContains(response, f'data-api-url="{api_url}"')

    def test_report_exposes_report_access_token_for_browser_fetch(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "data-report-access-token=")

    def test_report_does_not_expose_api_auth_token(self):
        response = self.client.get(self.report_url)
        self.assertNotContains(response, "data-api-auth-token=")

    def test_platform_nav_link_is_active(self):
        response = self.client.get(self.report_url)
        self.assertContains(
            response,
            '<a class="active" href="/unveil/report/platform/">Platform</a>',
            html=True,
        )

    def test_report_includes_platform_section_placeholders(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'id="platform-runtime-body"')
        self.assertContains(response, 'id="platform-source-body"')
        self.assertContains(response, 'id="platform-warnings-body"')
        self.assertContains(response, 'id="platform-packages-body"')
        self.assertContains(response, 'id="platform-metadata-body"')
        self.assertContains(
            response,
            '<th data-sort-col="0" data-sort-target="platform-packages-body">Name</th>',
            html=True,
        )
        self.assertContains(
            response,
            '<th data-sort-col="4" data-sort-target="platform-packages-body">Source Kind</th>',
            html=True,
        )
        self.assertContains(
            response,
            '<th data-sort-col="5" data-sort-target="platform-packages-body">Source Name</th>',
            html=True,
        )

    def test_report_does_not_render_dependency_rows_server_side(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn('<tbody id="platform-runtime-body"></tbody>', content)
        self.assertIn('<tbody id="platform-source-body"></tbody>', content)
        self.assertIn('<tbody id="platform-warnings-body"></tbody>', content)
        self.assertIn('<tbody id="platform-packages-body"></tbody>', content)
        self.assertIn('<tbody id="platform-metadata-body"></tbody>', content)

    def test_report_hides_url_testing_controls(self):
        response = self.client.get(self.report_url)
        self.assertNotContains(response, "unveil-test-all-button")
        self.assertNotContains(response, "unveil-toggle-untestable-button")
        self.assertNotContains(response, "search-input")

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get(self.report_url)
            self.assertEqual(response.status_code, 404)

    def test_report_returns_html_when_production_reports_enabled(self):
        with self.settings(**production_report_settings()):
            response = self.client.get(self.report_url)
            self.assertEqual(response.status_code, 200)
