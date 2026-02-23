from django.test import TestCase, override_settings

from wagtail_unveil.settings import get_pages_per_type
from wagtail_unveil.urls import get_frontend_urls


class TestGetPagesPerType(TestCase):
    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_default_returns_zero(self):
        self.assertEqual(get_pages_per_type(), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_returns_configured_value(self):
        self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=5)
    def test_returns_higher_value(self):
        self.assertEqual(get_pages_per_type(), 5)


class TestPagesPerTypeLimit(TestCase):
    """Test that WAGTAIL_UNVEIL_PAGES_PER_TYPE limits page URLs per type."""

    def setUp(self):
        from wagtail.models import Page

        root = Page.objects.first()
        home = root.get_children().first()

        # Create multiple pages of different types using sandbox models
        from sandbox.core.models import StandardPage

        for i in range(3):
            home.add_child(instance=StandardPage(
                title=f"Standard {i}",
                slug=f"standard-{i}",
            ))

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_default_returns_all_pages(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        # Should include all pages (home + 3 standard pages)
        standard_urls = [u for u in page_urls if "StandardPage" in u.page_type]
        self.assertEqual(len(standard_urls), 3)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_limit_one_per_type(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        # Count per page_type — each should have at most 1
        type_counts = {}
        for u in page_urls:
            type_counts[u.page_type] = type_counts.get(u.page_type, 0) + 1
        for page_type, count in type_counts.items():
            self.assertLessEqual(count, 1, f"{page_type} has {count} URLs")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=2)
    def test_limit_two_per_type(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        type_counts = {}
        for u in page_urls:
            type_counts[u.page_type] = type_counts.get(u.page_type, 0) + 1
        standard_count = type_counts.get("core.StandardPage", 0)
        self.assertEqual(standard_count, 2)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_zero_means_no_limit(self):
        urls = get_frontend_urls()
        page_urls = [u for u in urls if u.source == "page"]
        standard_urls = [u for u in page_urls if "StandardPage" in u.page_type]
        self.assertEqual(len(standard_urls), 3)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_resolver_urls_not_affected(self):
        urls = get_frontend_urls()
        resolver_urls = [u for u in urls if u.source == "resolver"]
        self.assertGreater(len(resolver_urls), 0)
