from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site
from wagtail.test.utils import WagtailTestUtils

from wagtail_unveil.urls import AdminURL, get_admin_urls
from wagtail_unveil.wagtail_hooks import UnveilReportPanel


class TestGetAdminUrls(TestCase):
    def setUp(self):
        self.urls = get_admin_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_all_urls_start_with_admin(self):
        for url in self.urls:
            self.assertTrue(url.route.startswith("admin/"), url.route)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, AdminURL)
        self.assertIsInstance(url.route, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.namespace, str)
        self.assertIsInstance(url.has_parameters, bool)
        self.assertIsInstance(url.view_name, str)

    def test_known_url_present(self):
        names = {url.name for url in self.urls}
        self.assertIn("wagtailadmin_home", names)

    def test_has_parameters_detection(self):
        parameterized = [url for url in self.urls if url.has_parameters]
        static = [url for url in self.urls if not url.has_parameters]
        self.assertGreater(len(parameterized), 0)
        self.assertGreater(len(static), 0)
        for url in static:
            self.assertNotIn("<", url.route)

    def test_is_testable_false_for_non_snippet_parameterized(self):
        for url in self.urls:
            if url.has_parameters and not url.resolved_route:
                self.assertFalse(url.is_testable, url.route)
                self.assertEqual(url.skip_reason, "URL requires parameters")

    def test_is_testable_false_for_regex_routes(self):
        regex_urls = [
            url for url in self.urls
            if "^" in url.route and not url.has_parameters
        ]
        self.assertGreater(len(regex_urls), 0)
        for url in regex_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "Regex-based route pattern")

    def test_is_testable_false_for_logout(self):
        logout = [url for url in self.urls if url.name == "wagtailadmin_logout"]
        self.assertEqual(len(logout), 1)
        self.assertFalse(logout[0].is_testable)
        self.assertEqual(logout[0].skip_reason, "POST-only view")

    def test_is_testable_false_for_error_test(self):
        error = [url for url in self.urls if url.name == "wagtailadmin_error_test"]
        self.assertEqual(len(error), 1)
        self.assertFalse(error[0].is_testable)
        self.assertEqual(error[0].skip_reason, "Intentional error endpoint")

    def test_is_testable_true_for_home(self):
        home = [url for url in self.urls if url.name == "wagtailadmin_home"]
        self.assertEqual(len(home), 1)
        self.assertTrue(home[0].is_testable)
        self.assertEqual(home[0].skip_reason, "")


class TestShowAdminUrlsCommand(TestCase):
    def _call(self, *args):
        out = StringIO()
        call_command("show_admin_urls", *args, stdout=out)
        return out.getvalue()

    def test_command_runs(self):
        output = self._call()
        self.assertIn("Total:", output)

    def test_output_contains_urls(self):
        output = self._call()
        self.assertIn("wagtailadmin_home", output)

    def test_static_filter(self):
        output = self._call("--static")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertNotIn("<", line)

    def test_parameterized_filter(self):
        output = self._call("--parameterized")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertTrue("<" in line or "(" in line, line)


@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestAdminUrlsAPIView(TestCase):
    def test_returns_json(self):
        response = self.client.get(
            "/unveil-api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("urls", data)
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)
        self.assertEqual(len(data["urls"]), data["count"])

    def test_requires_api_key(self):
        response = self.client.get("/unveil-api/admin-urls/")
        self.assertEqual(response.status_code, 403)

    def test_rejects_wrong_key(self):
        response = self.client.get(
            "/unveil-api/admin-urls/",
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_500_when_no_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.get(
                "/unveil-api/admin-urls/",
                HTTP_AUTHORIZATION="Bearer test-secret",
            )
            self.assertEqual(response.status_code, 500)

    def test_filter_static(self):
        response = self.client.get(
            "/unveil-api/admin-urls/?filter=static",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertFalse(url["has_parameters"], url["route"])

    def test_filter_parameterized(self):
        response = self.client.get(
            "/unveil-api/admin-urls/?filter=parameterized",
            HTTP_AUTHORIZATION="Bearer test-secret",
        )
        data = response.json()
        for url in data["urls"]:
            self.assertTrue(url["has_parameters"], url["route"])


@override_settings(DEBUG=True)
class TestAdminUrlsReportView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_report_requires_login(self):
        self.client.logout()
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_requires_superuser(self):
        self.client.logout()
        User.objects.create_user(
            username="editor", password="password", is_staff=True
        )
        self.client.login(username="editor", password="password")
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 302)

    def test_report_returns_html(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Admin URLs Report", content)
        self.assertIn("<table", content)

    def test_report_contains_known_url(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "wagtailadmin_home")

    def test_report_contains_counts(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn("Total:", content)
        self.assertIn("URLs", content)

    def test_report_has_test_buttons(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-btn")

    def test_report_disables_test_for_non_testable(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "disabled")
        self.assertContains(response, "POST-only view")
        self.assertContains(response, "Intentional error endpoint")
        self.assertContains(response, "Regex-based route pattern")

    def test_report_has_reset_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "reset-btn")
        self.assertContains(response, "Reset")

    def test_report_has_test_all_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "test-all-btn")
        self.assertContains(response, "Test All")

    def test_report_shows_all_rows_by_default(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-has-parameters="true"', content)
        self.assertIn('data-has-parameters="false"', content)
        self.assertNotIn('class="hidden"', content.split("<tbody>")[1].split("</tbody>")[0])

    def test_report_has_search_input(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "search-input")

    def test_report_has_sortable_headers(self):
        response = self.client.get("/unveil-report/admin-urls/")
        content = response.content.decode()
        self.assertIn('data-sort-col="0"', content)
        self.assertIn('data-sort-col="1"', content)
        self.assertIn('data-sort-col="2"', content)
        self.assertIn('data-sort-col="3"', content)

    def test_report_loads_static_css(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(
            response, "wagtail_unveil/css/admin_urls_report.css"
        )

    def test_report_loads_static_js(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(
            response, "wagtail_unveil/js/admin_urls_report.js"
        )

    def test_report_has_help_button(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "help-btn")

    def test_report_has_help_panel(self):
        response = self.client.get("/unveil-report/admin-urls/")
        self.assertContains(response, "help-panel")
        self.assertContains(response, "Django URL name")
        self.assertContains(response, "How It Works")

    def test_report_returns_404_when_not_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/unveil-report/admin-urls/")
            self.assertEqual(response.status_code, 404)


@override_settings(DEBUG=True)
class TestDashboardPanel(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.panel = UnveilReportPanel()
        self.superuser = User.objects.create_superuser(
            username="admin", password="password"
        )
        self.regular_user = User.objects.create_user(
            username="editor", password="password", is_staff=True
        )

    def _render(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return self.panel.render_html({"request": request})

    def test_panel_visible_for_superuser(self):
        html = self._render(self.superuser)
        self.assertIn("View Admin URLs Report", html)
        self.assertIn("/unveil-report/admin-urls/", html)
        self.assertIn("w-panel w-panel--dashboard", html)

    def test_panel_hidden_for_non_superuser(self):
        html = self._render(self.regular_user)
        self.assertEqual(html, "")

    def test_panel_hidden_when_not_debug(self):
        with self.settings(DEBUG=False):
            html = self._render(self.superuser)
            self.assertEqual(html, "")


class TestParameterisedURLResolution(TestCase):
    """Test that parameterised admin URLs are resolved using real model instances."""

    def setUp(self):
        # Create instances for models that need them
        from wagtail.contrib.redirects.models import Redirect

        self.redirect = Redirect.objects.create(
            old_path="/test-redirect",
            site=Site.objects.first(),
            redirect_link="/destination",
        )
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.document = Document.objects.create(
            title="Test document",
            file="test.pdf",
        )
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )
        self.group = Group.objects.create(name="Test group")

        self.urls = get_admin_urls()
        self.snippet_urls = [
            u for u in self.urls
            if u.namespace.startswith("wagtailsnippets_") and u.has_parameters
        ]

    def test_snippet_edit_url_is_testable(self):
        edit_urls = [u for u in self.snippet_urls if u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_snippet_copy_url_is_testable(self):
        copy_urls = [u for u in self.snippet_urls if u.name == "copy"]
        self.assertGreater(len(copy_urls), 0)
        for url in copy_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_snippet_delete_url_is_testable(self):
        delete_urls = [u for u in self.snippet_urls if u.name == "delete"]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_resolved_route_contains_pk(self):
        for url in self.snippet_urls:
            if url.resolved_route:
                self.assertNotIn("<", url.resolved_route)
                self.assertRegex(url.resolved_route, r"/\d+/")

    def test_redirect_edit_url_is_testable(self):
        edit_urls = [
            u for u in self.urls
            if "redirect" in u.namespace and u.name == "edit"
        ]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_redirect_delete_url_is_testable(self):
        delete_urls = [
            u for u in self.urls
            if "redirect" in u.namespace and u.name == "delete"
        ]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_image_edit_url_is_testable(self):
        edit_urls = [
            u for u in self.urls
            if "wagtailimages" in u.namespace and u.name == "edit"
        ]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_image_delete_url_is_testable(self):
        delete_urls = [
            u for u in self.urls
            if "wagtailimages" in u.namespace and u.name == "delete"
        ]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_document_edit_url_is_testable(self):
        edit_urls = [
            u for u in self.urls
            if "wagtaildocs" in u.namespace and u.name == "edit"
        ]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_user_edit_url_is_testable(self):
        edit_urls = [
            u for u in self.urls
            if "wagtailusers_users" in u.namespace and u.name == "edit"
        ]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_resolved_route_has_no_angle_brackets(self):
        resolved = [u for u in self.urls if u.resolved_route]
        self.assertGreater(len(resolved), 0)
        for url in resolved:
            self.assertNotIn("<", url.resolved_route, url.route)

    def test_multi_param_urls_remain_untestable(self):
        multi_param = [
            u for u in self.urls
            if u.has_parameters and u.route.count("<") > 1
            and not u.resolved_route
        ]
        for url in multi_param:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "URL requires parameters")

    def test_unresolvable_parameterised_urls_are_untestable(self):
        unresolvable = [
            u for u in self.urls
            if u.has_parameters and not u.resolved_route
        ]
        self.assertGreater(len(unresolvable), 0)
        for url in unresolvable:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "URL requires parameters")
