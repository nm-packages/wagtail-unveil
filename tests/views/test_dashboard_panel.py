from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings

from wagtail_unveil.wagtail_hooks import UnveilReportPanel


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
        self.assertIn("Backend URLs", html)
        self.assertIn("/unveil/report/backend-urls/", html)
        self.assertIn("Frontend URLs", html)
        self.assertIn("/unveil/report/frontend-urls/", html)
        self.assertIn("Platform", html)
        self.assertIn("/unveil/report/platform/", html)
        self.assertIn("Settings", html)
        self.assertIn("/unveil/report/settings/", html)
        self.assertIn("Inspect discovered backend and admin routes.", html)
        self.assertIn("Inspect discovered public page and resolver URLs.", html)
        self.assertIn("Inspect runtime versions, dependency inventory, and platform warnings.", html)
        self.assertIn("Review active Unveil settings and runtime diagnostics.", html)
        self.assertIn("Open report", html)
        self.assertIn("Open settings", html)
        self.assertIn("w-panel w-panel--dashboard", html)
        self.assertIn("listing listing--dashboard", html)
        self.assertIn('id="unveil-section"', html)
        self.assertIn('id="unveil-heading"', html)
        self.assertIn('id="unveil-content"', html)
        self.assertIn("data-panel", html)
        self.assertIn("data-panel-toggle", html)
        self.assertIn('aria-controls="unveil-content"', html)

    def test_panel_hidden_for_non_superuser(self):
        html = self._render(self.regular_user)
        self.assertEqual(html, "")

    def test_panel_hidden_when_not_debug(self):
        with self.settings(DEBUG=False):
            html = self._render(self.superuser)
            self.assertEqual(html, "")

    def test_panel_visible_when_production_reports_enabled(self):
        with self.settings(DEBUG=False, WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True):
            html = self._render(self.superuser)
            self.assertIn("Backend URLs", html)
            self.assertIn("Frontend URLs", html)
            self.assertIn("Settings", html)
