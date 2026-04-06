import os

from django.test import TestCase, override_settings

from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.frontend import get_frontend_urls


class TestPagesPerTypeLimit(TestCase):
    """Test that WAGTAIL_UNVEIL_PAGES_PER_TYPE limits page URLs per type."""

    def setUp(self):
        from wagtail.models import Page

        from sandbox.core.models import StandardPage

        root = Page.objects.first()
        home = root.get_children().first()

        for i in range(3):
            home.add_child(
                instance=StandardPage(
                    title=f"Standard {i}",
                    slug=f"standard-{i}",
                )
            )

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_limit_one_per_type(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        type_counts = {}
        for url in page_urls:
            type_counts[url.page_type] = type_counts.get(url.page_type, 0) + 1
        for page_type, count in type_counts.items():
            self.assertLessEqual(count, 1, f"{page_type} has {count} URLs")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=2)
    def test_limit_two_per_type(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        type_counts = {}
        for url in page_urls:
            type_counts[url.page_type] = type_counts.get(url.page_type, 0) + 1
        standard_count = type_counts.get("core.StandardPage", 0)
        self.assertEqual(standard_count, 2)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_zero_means_no_limit_at_frontend_discovery_layer(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        standard_urls = [u for u in page_urls if "StandardPage" in u.page_type]
        self.assertEqual(len(standard_urls), 3)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_resolver_urls_not_affected(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        self.assertGreater(len(resolver_urls), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="abc")
    def test_invalid_setting_does_not_crash_frontend_discovery(self):
        urls = get_frontend_urls()
        self.assertGreater(len(urls), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=-1)
    def test_negative_setting_does_not_crash_frontend_discovery(self):
        urls = get_frontend_urls()
        self.assertGreater(len(urls), 0)


class TestSkipUrlPrefixesFilter(TestCase):
    def setUp(self):
        self._orig_env = os.environ.pop("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES", None)

    def tearDown(self):
        if self._orig_env is not None:
            os.environ["WAGTAIL_UNVEIL_SKIP_URL_PREFIXES"] = self._orig_env

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["search/"])
    def test_skip_prefix_excludes_frontend_resolver_url(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        search_urls = [u for u in resolver_urls if u.url.startswith("/search")]
        self.assertEqual(search_urls, [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=[])
    def test_no_skip_prefix_includes_frontend_resolver_url(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        search_urls = [u for u in resolver_urls if u.url.startswith("/search")]
        self.assertGreater(len(search_urls), 0)

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["admin/images/"])
    def test_skip_prefix_excludes_admin_url(self):
        urls = get_admin_urls()
        images_urls = [u for u in urls if u.route.startswith("admin/images/")]
        self.assertEqual(images_urls, [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=[])
    def test_no_skip_prefix_includes_admin_url(self):
        urls = get_admin_urls()
        images_urls = [u for u in urls if u.route.startswith("admin/images/")]
        self.assertGreater(len(images_urls), 0)

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["/search/"])
    def test_leading_slash_prefix_also_works(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        search_urls = [u for u in resolver_urls if u.url.startswith("/search")]
        self.assertEqual(search_urls, [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["django-admin/"])
    def test_skip_prefix_excludes_path_mounted_django_admin_url(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        django_admin_urls = [u for u in resolver_urls if u.url.startswith("/django-admin/")]
        self.assertEqual(django_admin_urls, [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["events/past/"])
    def test_skip_prefix_excludes_routable_sub_url(self):
        from wagtail.models import Page

        from sandbox.events.models import EventIndexPage

        root = Page.objects.first()
        home = root.get_children().first()
        home.add_child(instance=EventIndexPage(title="Events", slug="events"))
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        matches = [u for u in page_urls if u.url.startswith("/events/past")]
        self.assertEqual(matches, [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["api-page/"])
    def test_skip_prefix_excludes_page_source_url(self):
        from wagtail.models import Page

        from sandbox.core.models import StandardPage

        root = Page.objects.first()
        home = root.get_children().first()
        home.add_child(instance=StandardPage(title="API Page", slug="api-page"))
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        matches = [u for u in page_urls if u.url.startswith("/api-page")]
        self.assertEqual(matches, [])
