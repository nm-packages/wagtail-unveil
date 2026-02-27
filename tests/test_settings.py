import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from wagtail_unveil.settings import get_api_key, get_pages_per_type, get_skip_url_prefixes
from wagtail_unveil.urls import get_admin_urls, get_frontend_urls


class TestGetPagesPerType(TestCase):
    def test_missing_setting_returns_one(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_zero_means_no_limit(self):
        self.assertEqual(get_pages_per_type(), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=None)
    def test_none_returns_one(self):
        self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_returns_configured_value(self):
        self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=5)
    def test_returns_higher_value(self):
        self.assertEqual(get_pages_per_type(), 5)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="2")
    def test_numeric_string_is_coerced(self):
        self.assertEqual(get_pages_per_type(), 2)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="0")
    def test_zero_string_is_coerced(self):
        self.assertEqual(get_pages_per_type(), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=-1)
    def test_negative_int_falls_back_to_one(self):
        self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="abc")
    def test_invalid_string_falls_back_to_one(self):
        self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1.5)
    def test_float_falls_back_to_one(self):
        self.assertEqual(get_pages_per_type(), 1)

    def test_env_var_numeric_string_is_coerced(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "3"}):
            self.assertEqual(get_pages_per_type(), 3)

    def test_env_var_zero_string_means_no_limit(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "0"}):
            self.assertEqual(get_pages_per_type(), 0)

    def test_env_var_negative_string_falls_back_to_one(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "-1"}):
            self.assertEqual(get_pages_per_type(), 1)

    def test_env_var_invalid_string_falls_back_to_one(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "abc"}):
            self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=5)
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "2"}):
            self.assertEqual(get_pages_per_type(), 2)


class TestPagesPerTypeLimit(TestCase):
    """Test that WAGTAIL_UNVEIL_PAGES_PER_TYPE limits page URLs per type."""

    def setUp(self):
        from wagtail.models import Page

        root = Page.objects.first()
        home = root.get_children().first()

        # Create multiple pages of different types using sandbox models
        from sandbox.core.models import StandardPage

        for i in range(3):
            home.add_child(
                instance=StandardPage(
                    title=f"Standard {i}",
                    slug=f"standard-{i}",
                )
            )

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

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="abc")
    def test_invalid_setting_does_not_crash_frontend_discovery(self):
        urls = get_frontend_urls()
        self.assertGreater(len(urls), 0)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=-1)
    def test_negative_setting_does_not_crash_frontend_discovery(self):
        urls = get_frontend_urls()
        self.assertGreater(len(urls), 0)


class TestGetSkipUrlPrefixes(TestCase):
    def setUp(self):
        self._orig_env = os.environ.pop("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES", None)

    def tearDown(self):
        if self._orig_env is not None:
            os.environ["WAGTAIL_UNVEIL_SKIP_URL_PREFIXES"] = self._orig_env

    def test_missing_setting_returns_empty_list(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            self.assertEqual(get_skip_url_prefixes(), [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=None)
    def test_none_returns_empty_list(self):
        self.assertEqual(get_skip_url_prefixes(), [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=[])
    def test_empty_list_returns_empty_list(self):
        self.assertEqual(get_skip_url_prefixes(), [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["__debug__/", "silk/"])
    def test_list_of_strings_returned(self):
        self.assertEqual(get_skip_url_prefixes(), ["__debug__/", "silk/"])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["/__debug__/"])
    def test_leading_slash_is_stripped(self):
        self.assertEqual(get_skip_url_prefixes(), ["__debug__/"])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES="__debug__/")
    def test_non_list_value_returns_empty_list(self):
        self.assertEqual(get_skip_url_prefixes(), [])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=[123, None, "__debug__/"])
    def test_non_string_items_are_dropped(self):
        self.assertEqual(get_skip_url_prefixes(), ["__debug__/"])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["valid/", 42, None, "/also-valid/"])
    def test_mixed_valid_and_invalid_items(self):
        self.assertEqual(get_skip_url_prefixes(), ["valid/", "also-valid/"])

    def test_env_var_comma_separated_string(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": "search/,admin/images/"}):
            self.assertEqual(get_skip_url_prefixes(), ["search/", "admin/images/"])

    def test_env_var_empty_string_returns_empty_list(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": ""}):
            self.assertEqual(get_skip_url_prefixes(), [])

    def test_env_var_strips_whitespace_and_leading_slash(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": "  /search/ , silk/ "}):
            self.assertEqual(get_skip_url_prefixes(), ["search/", "silk/"])

    @override_settings(WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=["django-setting/"])
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": "env-prefix/"}):
            self.assertEqual(get_skip_url_prefixes(), ["env-prefix/"])


class TestGetApiKey(TestCase):
    def test_missing_env_and_missing_setting_returns_empty_string(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(get_api_key(), "")

    def test_env_var_non_empty_string_returned(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "mysecretkey"}):
            self.assertEqual(get_api_key(), "mysecretkey")

    def test_env_var_strips_whitespace(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "  mykey  "}):
            self.assertEqual(get_api_key(), "mykey")

    def test_env_var_empty_string_returns_empty_string(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": ""}):
                self.assertEqual(get_api_key(), "")

    @override_settings(WAGTAIL_UNVEIL_API_KEY="django-setting-key")
    def test_django_setting_fallback_when_env_var_absent(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_api_key(), "django-setting-key")

    @override_settings(WAGTAIL_UNVEIL_API_KEY=None)
    def test_django_setting_none_returns_empty_string(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_api_key(), "")

    @override_settings(WAGTAIL_UNVEIL_API_KEY=True)
    def test_django_setting_bool_returns_empty_string(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_api_key(), "")

    @override_settings(WAGTAIL_UNVEIL_API_KEY=42)
    def test_django_setting_int_returns_empty_string(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_api_key(), "")

    @override_settings(WAGTAIL_UNVEIL_API_KEY="django-key")
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "env-key"}):
            self.assertEqual(get_api_key(), "env-key")


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
