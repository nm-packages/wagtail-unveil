from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from wagtail_unveil.urls import AdminURL, get_admin_urls


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
