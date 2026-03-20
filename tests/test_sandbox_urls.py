from django.test import TestCase
from django.urls import resolve

from wagtail_unveil.discovery.frontend import get_frontend_urls


class TestSandboxIntentionalFrontendError(TestCase):
    def test_intentional_error_route_is_discovered_as_testable_resolver_url(self):
        urls = [url for url in get_frontend_urls() if url.name == "intentional_frontend_error"]

        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].url, "/intentional-error/")
        self.assertEqual(urls[0].source, "resolver")
        self.assertTrue(urls[0].is_testable)
        self.assertEqual(urls[0].skip_reason, "")

    def test_intentional_error_route_returns_500(self):
        response = self.client.get("/intentional-error/")

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Intentional frontend error", status_code=500)


class TestSandboxWagtailAPI(TestCase):
    def test_api_v2_find_route_is_mounted(self):
        match = resolve("/api/v2/pages/find/")

        self.assertEqual(match.url_name, "find")
        self.assertEqual(match.namespace, "wagtailapi:pages")

    def test_api_v2_find_routes_are_discovered(self):
        urls = [url for url in get_frontend_urls() if url.name == "find" and url.url.startswith("/api/v2/")]

        self.assertEqual(
            {url.url for url in urls},
            {
                "/api/v2/pages/find/",
                "/api/v2/images/find/",
                "/api/v2/documents/find/",
                "/api/v2/redirects/find/",
            },
        )
