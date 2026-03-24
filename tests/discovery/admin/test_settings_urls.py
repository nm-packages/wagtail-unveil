from django.test import TestCase
from wagtail.models import Site

from wagtail_unveil.discovery.backend import get_admin_urls


class TestSettingsURLDiscovery(TestCase):
    """Test that Wagtail site and generic settings URLs are discovered and testable."""

    def setUp(self):
        from sandbox.core.models import BrandingSettings, SocialMediaSettings

        site = Site.objects.first()
        SocialMediaSettings.objects.get_or_create(
            site=site,
            defaults={
                "facebook": "https://facebook.com/test",
                "twitter": "https://twitter.com/test",
                "instagram": "https://instagram.com/test",
            },
        )
        if not BrandingSettings.objects.exists():
            BrandingSettings.objects.create(
                site_name="Test Site",
                tagline="Test tagline",
            )

        self.urls = get_admin_urls()
        self.settings_urls = [u for u in self.urls if u.namespace == "wagtailsettings"]

    def test_settings_urls_discovered(self):
        self.assertGreater(len(self.settings_urls), 0)

    def test_settings_urls_have_correct_namespace(self):
        for url in self.settings_urls:
            self.assertEqual(url.namespace, "wagtailsettings")

    def test_settings_edit_urls_present(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)

    def test_settings_urls_are_parameterised(self):
        for url in self.settings_urls:
            self.assertTrue(url.has_parameters, url.route)

    def test_settings_routes_contain_settings_prefix(self):
        for url in self.settings_urls:
            self.assertTrue(url.route.startswith("admin/settings/"), url.route)

    def test_settings_redirect_url_is_testable(self):
        redirect_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" not in u.route]
        self.assertGreater(len(redirect_urls), 0)
        for url in redirect_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_settings_edit_url_is_testable(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)
            self.assertNotIn("<", url.resolved_route)

    def test_settings_resolved_route_contains_app_and_model(self):
        for url in self.settings_urls:
            if url.resolved_route:
                self.assertIn("/core/", url.resolved_route)

    def test_settings_edit_url_uses_site_pk(self):
        """For BaseSiteSetting edit URL, resolved_route should contain site pk, not settings row pk."""
        from sandbox.core.models import SocialMediaSettings

        settings_instance = SocialMediaSettings.objects.first()
        self.assertIsNotNone(settings_instance)
        expected_site_pk = settings_instance.site_id

        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route and u.resolved_route]
        self.assertGreater(len(edit_urls), 0)

        for url in edit_urls:
            self.assertIn(f"/{expected_site_pk}/", url.resolved_route)

    def test_settings_preview_url_is_non_testable(self):
        """preview_on_edit URL should be non-testable since sandbox settings don't implement PreviewableMixin."""
        preview_urls = [u for u in self.settings_urls if u.name == "preview_on_edit"]

        for url in preview_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertTrue(url.skip_reason)
