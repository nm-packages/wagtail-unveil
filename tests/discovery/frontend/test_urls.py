from django.test import TestCase, override_settings

from wagtail_unveil.discovery.frontend import FrontendURL, get_frontend_urls


class TestGetFrontendUrls(TestCase):
    def setUp(self):
        self.urls = get_frontend_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, FrontendURL)
        self.assertIsInstance(url.url, str)
        self.assertIsInstance(url.source, str)
        self.assertIsInstance(url.page_type, str)
        self.assertIsInstance(url.page_title, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.resolved_url, str)
        self.assertIsInstance(url.query_params, dict)
        self.assertIsInstance(url.is_testable, bool)

    def test_sources_are_valid(self):
        for url in self.urls:
            self.assertIn(url.source, ("page", "resolver"))

    def test_page_urls_have_page_type(self):
        page_urls = [u for u in self.urls if u.source == "page"]
        self.assertGreater(len(page_urls), 0)
        for url in page_urls:
            self.assertTrue(url.page_type, url.url)
            self.assertTrue(url.page_title, url.url)

    def test_resolver_urls_present(self):
        resolver_urls = [u for u in self.urls if u.source == "resolver"]
        self.assertGreater(len(resolver_urls), 0)

    def test_no_admin_urls_included(self):
        for url in self.urls:
            self.assertFalse(url.url.startswith("/admin/"), url.url)

    def test_django_admin_urls_can_be_included(self):
        django_admin_urls = [url for url in self.urls if url.url.startswith("/django-admin/")]
        self.assertGreater(len(django_admin_urls), 0)

    def test_no_unveil_urls_included(self):
        for url in self.urls:
            self.assertNotIn("unveil-api", url.url)
            self.assertNotIn("unveil-report", url.url)

    def test_page_urls_are_testable(self):
        page_urls = [u for u in self.urls if u.source == "page"]
        testable = [u for u in page_urls if not u.skip_reason]
        for url in testable:
            self.assertTrue(url.is_testable, url.url)

    def test_parameterized_resolver_urls_not_testable(self):
        for url in self.urls:
            if url.source == "resolver" and not url.is_testable:
                self.assertTrue(url.skip_reason, url.url)

    def test_regex_parameterized_resolver_urls_not_testable(self):
        regex_urls = {
            "wagtail_serve": "URL contains regex patterns",
            "wagtaildocs_serve": "URL contains regex patterns",
        }
        for name, expected_reason in regex_urls.items():
            matches = [u for u in self.urls if u.name == name]
            self.assertTrue(matches, f"Expected to find URL named {name}")
            for url in matches:
                self.assertFalse(url.is_testable, f"{name} should not be testable")
                self.assertEqual(url.skip_reason, expected_reason, name)

    def test_urls_start_with_slash(self):
        for url in self.urls:
            self.assertTrue(url.url.startswith("/"), url.url)


@override_settings(ROOT_URLCONF="tests.discovery.frontend.urls_regex_admin")
class TestRegexMountedAdminDiscovery(TestCase):
    def test_regex_mounted_django_admin_urls_are_included_by_default(self):
        urls = get_frontend_urls()
        django_admin_urls = [url for url in urls if url.url.startswith("/django-admin/")]
        self.assertGreater(len(django_admin_urls), 0)

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["django-admin/"])
    def test_regex_mounted_django_admin_urls_respect_skip_prefixes(self):
        urls = get_frontend_urls()
        django_admin_urls = [url for url in urls if url.url.startswith("/django-admin/")]
        self.assertEqual(django_admin_urls, [])

    def test_non_admin_regex_routes_are_still_discovered(self):
        urls = get_frontend_urls()
        regex_search_urls = [url for url in urls if url.url == "/regex-search/"]
        self.assertEqual(len(regex_search_urls), 1)
        self.assertEqual(regex_search_urls[0].name, "regex_search")
