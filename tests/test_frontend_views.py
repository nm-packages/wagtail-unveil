from dataclasses import replace
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from tests.utils import BaseAPIViewTestMixin, BaseReportViewTestMixin
from wagtail_unveil.api_contract import get_api_contract, get_latest_stable_api_contract
from wagtail_unveil.discovery.frontend import FrontendURL
from wagtail_unveil.views import _serialize_frontend_url
from wagtail_unveil.wagtail_hooks import UnveilReportPanel

V1_CONTRACT = get_api_contract("v1")
API_URL = f"/unveil/{V1_CONTRACT.frontend_url_path}"


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestFrontendUrlsAPIView(BaseAPIViewTestMixin, TestCase):
    api_url = API_URL
    api_version = V1_CONTRACT.version

    def test_filter_pages(self):
        response = self.client.get(
            f"{self.api_url}?filter=pages",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        self.assertEqual(data["metadata"]["applied_filter"], "pages")
        self.assertEqual(data["metadata"]["total_count"], data["count"])
        for url in data["urls"]:
            self.assertEqual(url["source"], "page")

    def test_filter_resolver(self):
        response = self.client.get(
            f"{self.api_url}?filter=resolver",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        self.assertEqual(data["metadata"]["applied_filter"], "resolver")
        self.assertEqual(data["metadata"]["total_count"], data["count"])
        for url in data["urls"]:
            self.assertEqual(url["source"], "resolver")

    def test_invalid_filter_does_not_apply_metadata_filter(self):
        response = self.client.get(
            f"{self.api_url}?filter=unknown",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertIsNone(response.json()["metadata"]["applied_filter"])

    def test_response_includes_api_version_metadata(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertEqual(response.json()["metadata"]["api_version"], self.api_version)

    @patch("wagtail_unveil.views.get_api_contract")
    def test_response_sets_deprecation_headers_for_deprecated_contract(self, mock_get_api_contract):
        deprecated_contract = replace(
            V1_CONTRACT,
            status="deprecated",
            deprecated_on=date(2026, 1, 1),
            sunset_on=date(2026, 12, 31),
        )
        mock_get_api_contract.return_value = deprecated_contract

        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        self.assertEqual(response["Deprecation"], "true")
        self.assertIn("Sunset", response)
        self.assertEqual(response.json()["metadata"]["api_lifecycle"]["status"], "deprecated")


class TestFrontendAPIViewHelpers(TestCase):
    def test_serialize_frontend_url(self):
        url = FrontendURL(
            url="/contact/",
            source="page",
            page_type="core.ContactPage",
            page_title="Contact",
            name="",
            is_testable=False,
            skip_reason="Requires POST submission",
        )

        self.assertEqual(
            _serialize_frontend_url(url),
            {
                "url": "/contact/",
                "source": "page",
                "page_type": "core.ContactPage",
                "page_title": "Contact",
                "name": "",
                "is_testable": False,
                "skip_reason": "Requires POST submission",
            },
        )


@override_settings(DEBUG=True)
class TestFrontendUrlsReportView(BaseReportViewTestMixin, WagtailTestUtils, TestCase):
    report_url = "/unveil/report/frontend-urls/"
    report_title = "Frontend URLs Report"

    def setUp(self):
        self.login()

    def test_report_has_sortable_headers(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertIn('data-sort-col="0"', content)
        self.assertIn('data-sort-col="1"', content)
        self.assertIn('data-sort-col="2"', content)
        self.assertIn('data-sort-col="3"', content)
        self.assertIn('data-sort-col="4"', content)

    def test_report_shows_source_column(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertContains(response, "Source")

    def test_report_includes_frontend_api_url(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        latest_contract = get_latest_stable_api_contract()
        api_url = reverse(f"wagtail_unveil:{latest_contract.frontend_url_name}")
        self.assertContains(response, f'data-api-url="{api_url}"')

    def test_report_does_not_render_rows_server_side(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        content = response.content.decode()
        self.assertNotIn('data-source="page"', content)
        self.assertNotIn('data-source="resolver"', content)

    def test_report_does_not_render_inline_help(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertNotContains(response, "unveil-help-button")
        self.assertNotContains(response, "How It Works")


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
        self.assertIn("Frontend URLs", html)
        self.assertIn("/unveil/report/frontend-urls/", html)
        self.assertIn("Inspect discovered public page and resolver URLs.", html)
        self.assertIn("Settings", html)
        self.assertIn("/unveil/report/settings/", html)
        self.assertIn("listing listing--dashboard", html)
        self.assertIn("Open report", html)
        self.assertIn("Open settings", html)
        self.assertIn('id="unveil-section"', html)
        self.assertIn("data-panel-toggle", html)


@override_settings(DEBUG=True)
class TestFrontendReportSettingsMessage(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_does_not_show_limit_setting_when_unlimited(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertNotContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")
        self.assertNotContains(response, "Showing 0 pages per type")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_does_not_show_limit_setting_when_limited(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertNotContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")
        self.assertNotContains(response, "Showing 1 page per type")
