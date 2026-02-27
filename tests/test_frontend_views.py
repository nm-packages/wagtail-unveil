from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from wagtail.test.utils import WagtailTestUtils

from tests.utils import BaseAPIViewTestMixin, BaseReportViewTestMixin
from wagtail_unveil.wagtail_hooks import UnveilReportPanel


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestFrontendUrlsAPIView(BaseAPIViewTestMixin, TestCase):
    api_url = "/unveil/api/frontend-urls/"

    def test_filter_pages(self):
        response = self.client.get(
            "/unveil/api/frontend-urls/?filter=pages",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertEqual(url["source"], "page")

    def test_filter_resolver(self):
        response = self.client.get(
            "/unveil/api/frontend-urls/?filter=resolver",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertEqual(url["source"], "resolver")


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
        self.assertIn("/unveil/report/frontend-urls/", html)


@override_settings(DEBUG=True)
class TestFrontendReportPagesPerType(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_no_limit_message_by_default(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertNotContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_shows_limit_message(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertContains(response, "Showing 1 page per type")
        self.assertContains(response, "WAGTAIL_UNVEIL_PAGES_PER_TYPE")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=3)
    def test_shows_plural_limit_message(self):
        response = self.client.get("/unveil/report/frontend-urls/")
        self.assertContains(response, "Showing 3 pages per type")
