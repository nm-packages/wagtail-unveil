import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from wagtail_unveil.settings import (
    get_api_key,
    get_enable_production_reports,
    get_pages_per_type,
    get_platform_dependency_file,
    get_skip_url_prefixes,
    is_report_ui_enabled,
)


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

class TestGetEnableProductionReports(TestCase):
    def test_missing_setting_defaults_to_false(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {}, clear=True):
                self.assertFalse(get_enable_production_reports())

    @override_settings(WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True)
    def test_django_setting_true_is_respected(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(get_enable_production_reports())

    @override_settings(WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS="yes")
    def test_django_setting_string_is_normalized(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(get_enable_production_reports())

    @override_settings(WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS="invalid")
    def test_invalid_django_setting_falls_back_to_false(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(get_enable_production_reports())

    def test_env_var_true_is_respected(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS": "true"}):
            self.assertTrue(get_enable_production_reports())

    def test_env_var_false_is_respected(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS": "0"}):
            self.assertFalse(get_enable_production_reports())

    @override_settings(WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True)
    def test_blank_env_var_falls_back_to_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS": "   "}):
            self.assertTrue(get_enable_production_reports())

    @override_settings(WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=False)
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS": "on"}):
            self.assertTrue(get_enable_production_reports())


class TestIsReportUiEnabled(TestCase):
    @override_settings(DEBUG=True, WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=False)
    def test_debug_enables_report_ui(self):
        self.assertTrue(is_report_ui_enabled())

    @override_settings(DEBUG=False, WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True)
    def test_production_opt_in_enables_report_ui(self):
        self.assertTrue(is_report_ui_enabled())

    @override_settings(DEBUG=False, WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=False)
    def test_disabled_when_debug_and_opt_in_are_false(self):
        self.assertFalse(is_report_ui_enabled())


class TestGetPlatformDependencyFile(TestCase):
    def test_missing_env_and_missing_setting_returns_empty_string(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(get_platform_dependency_file(), "")

    def test_env_var_non_empty_string_returned(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE": "requirements/base.txt"}):
            self.assertEqual(get_platform_dependency_file(), "requirements/base.txt")

    def test_env_var_strips_whitespace(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE": "  pyproject.toml  "}):
            self.assertEqual(get_platform_dependency_file(), "pyproject.toml")

    def test_env_var_empty_string_returns_empty_string(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE": ""}):
                self.assertEqual(get_platform_dependency_file(), "")

    @override_settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE="requirements/dev.txt")
    def test_django_setting_fallback_when_env_var_absent(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_platform_dependency_file(), "requirements/dev.txt")

    @override_settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=None)
    def test_django_setting_none_returns_empty_string(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_platform_dependency_file(), "")

    @override_settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=True)
    def test_django_setting_bool_returns_empty_string(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_platform_dependency_file(), "")

    @override_settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE="requirements/base.txt")
    def test_env_var_wins_over_django_setting(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE": "pyproject.toml"}):
            self.assertEqual(get_platform_dependency_file(), "pyproject.toml")
