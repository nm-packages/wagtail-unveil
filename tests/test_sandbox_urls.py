from django.test import TestCase

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
