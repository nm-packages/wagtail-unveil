from dataclasses import replace
from datetime import date
from unittest.mock import patch

from django.test import TestCase

from tests.views.support import BaseAPIViewTestMixin
from wagtail_unveil.api_contract import get_api_contract
from wagtail_unveil.discovery.frontend import FrontendURL
from wagtail_unveil.views import _serialize_frontend_url

V1_CONTRACT = get_api_contract("v1")
API_URL = f"/unveil/{V1_CONTRACT.frontend_url_path}"


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestFrontendUrlsAPIView(BaseAPIViewTestMixin, TestCase):
    api_url = API_URL
    api_version = V1_CONTRACT.version
    report_url = "/unveil/report/frontend-urls/"

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

    def test_response_includes_query_params_field(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        for url in response.json()["urls"]:
            self.assertIn("query_params", url)
            self.assertIsInstance(url["query_params"], dict)

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
            resolved_url="",
            query_params={},
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
                "resolved_url": "",
                "query_params": {},
                "is_testable": False,
                "skip_reason": "Requires POST submission",
            },
        )
