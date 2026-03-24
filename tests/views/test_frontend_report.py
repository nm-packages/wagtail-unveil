from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from tests.views.support import BaseReportViewTestMixin
from wagtail_unveil.api_contract import get_latest_stable_api_contract


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
