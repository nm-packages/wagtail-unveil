import json
from dataclasses import replace
from datetime import date
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings
from wagtail.models import Page

from tests.views.support import BaseAPIViewTestMixin
from wagtail_unveil.api_contract import get_api_contract
from wagtail_unveil.discovery.backend import BackendURL
from wagtail_unveil.views import (
    _authenticate_api_request,
    _build_lifecycle_detail,
    _get_display_package_version,
    _get_package_version,
    _serialize_backend_url,
)

V1_CONTRACT = get_api_contract("v1")
API_URL = f"/unveil/{V1_CONTRACT.backend_url_path}"


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestAdminUrlsAPIView(BaseAPIViewTestMixin, TestCase):
    api_url = API_URL
    api_version = V1_CONTRACT.version

    def test_filter_static(self):
        response = self.client.get(
            f"{self.api_url}?filter=static",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        self.assertEqual(data["metadata"]["applied_filter"], "static")
        self.assertEqual(data["metadata"]["total_count"], data["count"])
        for url in data["urls"]:
            self.assertFalse(url["has_parameters"], url["route"])

    def test_filter_parameterized(self):
        response = self.client.get(
            f"{self.api_url}?filter=parameterized",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        self.assertEqual(data["metadata"]["applied_filter"], "parameterized")
        self.assertEqual(data["metadata"]["total_count"], data["count"])
        for url in data["urls"]:
            self.assertTrue(url["has_parameters"], url["route"])

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

    def test_page_edit_route_is_serialized_as_testable_with_resolved_route(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        edit_urls = [
            url for url in response.json()["urls"] if url["namespace"] == "wagtailadmin_pages" and url["name"] == "edit"
        ]

        expected_page_types = {
            f"{type(page)._meta.app_label}.{type(page)._meta.object_name}"
            for page in Page.objects.exclude(depth=1).specific()
        }

        self.assertEqual(len(edit_urls), len(expected_page_types))
        self.assertTrue(all(url["is_testable"] for url in edit_urls))
        self.assertTrue(all(url["skip_reason"] == "" for url in edit_urls))
        self.assertTrue(all(url["resolved_route"] for url in edit_urls))
        self.assertTrue(all(url["page_type"] for url in edit_urls))
        self.assertEqual({url["page_type"] for url in edit_urls}, expected_page_types)

    def test_workflow_task_edit_route_is_serialized_as_testable_with_resolved_route(self):
        response = self.client.get(
            self.api_url,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        edit_task_urls = [
            url
            for url in response.json()["urls"]
            if url["namespace"] == "wagtailadmin_workflows" and url["name"] == "edit_task"
        ]

        self.assertEqual(len(edit_task_urls), 1)
        self.assertTrue(edit_task_urls[0]["is_testable"])
        self.assertEqual(edit_task_urls[0]["skip_reason"], "")
        self.assertTrue(edit_task_urls[0]["resolved_route"])

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


class TestAdminAPIViewHelpers(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
    def test_authenticate_api_request_accepts_matching_bearer_token(self):
        request = self.factory.get(
            API_URL,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertIsNone(_authenticate_api_request(request))

    @patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
    def test_authenticate_api_request_rejects_wrong_bearer_token(self):
        request = self.factory.get(
            API_URL,
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        response = _authenticate_api_request(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content),
            {"error": "Invalid or missing API key"},
        )

    @override_settings(DEBUG=False)
    def test_authenticate_api_request_rejects_non_bearer_header_without_api_key(self):
        request = self.factory.get(
            API_URL,
            HTTP_AUTHORIZATION="Basic abc123",
        )
        response = _authenticate_api_request(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content),
            {"error": "Invalid or missing API key"},
        )

    def test_serialize_backend_url(self):
        url = BackendURL(
            route="admin/pages/1/edit/",
            name="edit",
            namespace="wagtailadmin_pages",
            has_parameters=True,
            view_name="wagtail.admin.views.pages.edit.EditView",
            page_type="core.StandardPage",
            is_testable=True,
            skip_reason="",
            resolved_route="admin/pages/1/edit/",
        )

        self.assertEqual(
            _serialize_backend_url(url),
            {
                "route": "admin/pages/1/edit/",
                "name": "edit",
                "namespace": "wagtailadmin_pages",
                "has_parameters": True,
                "view_name": "wagtail.admin.views.pages.edit.EditView",
                "page_type": "core.StandardPage",
                "is_testable": True,
                "skip_reason": "",
                "resolved_route": "admin/pages/1/edit/",
            },
        )

    def test_get_package_version_returns_empty_string_when_lookup_fails(self):
        with patch("wagtail_unveil.views.version", side_effect=PackageNotFoundError):
            self.assertEqual(_get_package_version(), "")

    def test_get_display_package_version_returns_unknown_when_lookup_is_empty(self):
        with patch("wagtail_unveil.views._get_package_version", return_value=""):
            self.assertEqual(_get_display_package_version(), "Unknown")

    def test_build_lifecycle_detail_returns_dates_when_present(self):
        deprecated_contract = replace(
            V1_CONTRACT,
            status="deprecated",
            deprecated_on=date(2026, 1, 1),
            sunset_on=date(2026, 12, 31),
        )

        detail = _build_lifecycle_detail(deprecated_contract)

        self.assertIn("Deprecated on 2026-01-01", detail)
        self.assertIn("Sunsets on 2026-12-31", detail)
