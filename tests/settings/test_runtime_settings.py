import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from wagtail_unveil.settings import get_api_key, get_pages_per_type, get_skip_url_prefixes


class TestGetPagesPerType(TestCase):
    def test_missing_setting_returns_one(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            self.assertEqual(get_pages_per_type(), 1)

    def test_valid_setting_values_return_expected_results(self):
        valid_cases = [
            (0, 0),
            (None, 1),
            (1, 1),
            (5, 5),
            ("2", 2),
            ("0", 0),
        ]

        for configured_value, expected in valid_cases:
            with self.subTest(configured_value=configured_value):
                with self.settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=configured_value):
                    self.assertEqual(get_pages_per_type(), expected)

    def test_invalid_setting_values_fall_back_to_one(self):
        for configured_value in (-1, "abc", 1.5):
            with self.subTest(configured_value=configured_value):
                with self.settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=configured_value):
                    self.assertEqual(get_pages_per_type(), 1)

    def test_valid_env_var_values_return_expected_results(self):
        valid_cases = [
            ("3", 3),
            ("0", 0),
        ]

        for env_value, expected in valid_cases:
            with self.subTest(env_value=env_value):
                with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": env_value}):
                    self.assertEqual(get_pages_per_type(), expected)

    def test_invalid_env_var_values_fall_back_to_one(self):
        for env_value in ("-1", "abc"):
            with self.subTest(env_value=env_value):
                with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": env_value}):
                    self.assertEqual(get_pages_per_type(), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=5)
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "2"}):
            self.assertEqual(get_pages_per_type(), 2)


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
