from django.test import TestCase, override_settings
from wagtail.models import Page, Site

from sandbox.core.models import BrandingSettings, StandardPage
from sandbox.home.models import HomePage
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


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class TestSandboxHomepageLinks(TestCase):
    def setUp(self):
        Site.objects.filter(is_default_site=True).update(port=8000)
        BrandingSettings.objects.update_or_create(
            pk=1,
            defaults={
                "site_name": "Sandbox Site",
                "tagline": "Sandbox tagline",
            },
        )

        root = Page.get_first_root_node()
        self.home = HomePage.objects.live().first()
        if not self.home:
            self.home = HomePage(title="Home", slug="home")
            root.add_child(instance=self.home)
            self.home.save_revision().publish()

        self.child = StandardPage(
            title="Port Check",
            slug="port-check",
            body="<p>Port check page.</p>",
        )
        self.home.add_child(instance=self.child)
        self.child.save_revision().publish()

    def test_homepage_renders_absolute_links_with_dev_port(self):
        response = self.client.get("/", HTTP_HOST="localhost:8000")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="http://localhost:8000/"')
        self.assertContains(response, 'href="http://localhost:8000/port-check/"')
