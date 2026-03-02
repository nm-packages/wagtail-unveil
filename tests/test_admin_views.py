import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from wagtail.test.utils import WagtailTestUtils

from tests.utils import BaseAPIViewTestMixin, BaseReportViewTestMixin
from wagtail_unveil.discovery.backend import BackendURL
from wagtail_unveil.views import _authenticate_api_request, _serialize_backend_url
from wagtail_unveil.wagtail_hooks import UnveilReportPanel


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestAdminUrlsAPIView(BaseAPIViewTestMixin, TestCase):
    api_url = "/unveil/api/admin-urls/"

    def test_filter_static(self):
        response = self.client.get(
            "/unveil/api/admin-urls/?filter=static",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertFalse(url["has_parameters"], url["route"])

    def test_filter_parameterized(self):
        response = self.client.get(
            "/unveil/api/admin-urls/?filter=parameterized",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertTrue(url["has_parameters"], url["route"])


class TestAdminAPIViewHelpers(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
    def test_authenticate_api_request_accepts_matching_bearer_token(self):
        request = self.factory.get(
            "/unveil/api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertIsNone(_authenticate_api_request(request))

    @patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
    def test_authenticate_api_request_rejects_wrong_bearer_token(self):
        request = self.factory.get(
            "/unveil/api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer wrong-key",
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
                "is_testable": True,
                "skip_reason": "",
                "resolved_route": "admin/pages/1/edit/",
            },
        )


@override_settings(DEBUG=True)
class TestAdminUrlsReportView(BaseReportViewTestMixin, WagtailTestUtils, TestCase):
    report_url = "/unveil/report/admin-urls/"
    report_title = "Admin URLs Report"

    def setUp(self):
        self.login()

    def test_report_contains_known_url(self):
        response = self.client.get("/unveil/report/admin-urls/")
        self.assertContains(response, "wagtailadmin_home")

    def test_report_disables_test_for_non_testable(self):
        response = self.client.get("/unveil/report/admin-urls/")
        self.assertContains(response, "disabled")
        self.assertContains(response, "POST-only view")
        self.assertContains(response, "Intentional error endpoint")

    def test_report_shows_all_rows_by_default(self):
        response = self.client.get("/unveil/report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-has-parameters="true"', content)
        self.assertIn('data-has-parameters="false"', content)
        self.assertNotIn('class="hidden"', content.split("<tbody>")[1].split("</tbody>")[0])

    def test_report_has_help_button(self):
        response = self.client.get("/unveil/report/admin-urls/")
        self.assertContains(response, "unveil-help-button")


@override_settings(DEBUG=True)
class TestDashboardPanel(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.panel = UnveilReportPanel()
        self.superuser = User.objects.create_superuser(username="admin", password="password")
        self.regular_user = User.objects.create_user(username="editor", password="password", is_staff=True)

    def _render(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return self.panel.render_html({"request": request})

    def test_panel_visible_for_superuser(self):
        html = self._render(self.superuser)
        self.assertIn("View Admin URLs Report", html)
        self.assertIn("/unveil/report/admin-urls/", html)
        self.assertIn("w-panel w-panel--dashboard", html)

    def test_panel_hidden_for_non_superuser(self):
        html = self._render(self.regular_user)
        self.assertEqual(html, "")

    def test_panel_hidden_when_not_debug(self):
        with self.settings(DEBUG=False):
            html = self._render(self.superuser)
            self.assertEqual(html, "")
