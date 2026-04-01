from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from tests.views.support import BaseReportViewTestMixin
from wagtail_unveil.api_contract import get_latest_stable_api_contract


@override_settings(DEBUG=True)
class TestBackendUrlsReportView(BaseReportViewTestMixin, WagtailTestUtils, TestCase):
    report_url = "/unveil/report/backend-urls/"
    report_title = "Backend URLs Report"

    def setUp(self):
        self.login()

    def test_report_includes_backend_api_url(self):
        response = self.client.get(self.report_url)
        latest_contract = get_latest_stable_api_contract()
        api_url = reverse(f"wagtail_unveil:{latest_contract.backend_url_name}")
        self.assertContains(response, f'data-api-url="{api_url}"')

    def test_report_uses_summary_placeholders(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, 'id="report-total"')
        self.assertContains(response, 'id="report-testable"')
        self.assertContains(response, 'id="report-untestable"')

    def test_report_includes_page_type_column(self):
        response = self.client.get(self.report_url)
        self.assertContains(response, "<th data-sort-col=\"3\">Page Type</th>", html=True)

    def test_report_does_not_render_rows_server_side(self):
        response = self.client.get(self.report_url)
        content = response.content.decode()
        self.assertNotIn("wagtailadmin_home", content)
        self.assertNotIn('data-has-parameters="true"', content)
        self.assertNotIn('data-has-parameters="false"', content)
