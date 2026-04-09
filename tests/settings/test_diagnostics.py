from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from wagtail_unveil.settings import get_setting_diagnostics


class TestSettingDiagnostics(TestCase):
    def _get_diagnostic(self, name):
        diagnostics = {item.name: item for item in get_setting_diagnostics()}
        return diagnostics[name]

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=5)
    def test_pages_per_type_diagnostics_prefer_env_source(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "2"}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_PAGES_PER_TYPE")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.raw_value, "2")
        self.assertEqual(diagnostic.effective_value, 2)

    def test_api_key_diagnostics_use_default_source_when_unset(self):
        with patch("wagtail_unveil.settings.settings", SimpleNamespace()):
            with patch.dict("os.environ", {}, clear=True):
                diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "default")
        self.assertEqual(diagnostic.raw_display, "Not set")
        self.assertEqual(diagnostic.effective_value, "")

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE="abc")
    def test_invalid_pages_per_type_value_falls_back_to_one(self):
        with patch.dict("os.environ", {}, clear=True):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_PAGES_PER_TYPE")

        self.assertEqual(diagnostic.source, "django")
        self.assertEqual(diagnostic.raw_value, "abc")
        self.assertEqual(diagnostic.effective_value, 1)
        self.assertIn("normalized", diagnostic.notes)

    def test_blank_env_pages_per_type_value_is_ignored(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": ""}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_PAGES_PER_TYPE")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.raw_value, "")
        self.assertEqual(diagnostic.effective_value, 1)
        self.assertIn("Blank environment values are ignored.", diagnostic.notes)

    def test_whitespace_only_env_pages_per_type_value_is_ignored(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "   "}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_PAGES_PER_TYPE")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.raw_value, "   ")
        self.assertEqual(diagnostic.effective_value, 1)
        self.assertIn("Blank environment values are ignored.", diagnostic.notes)

    def test_zero_pages_per_type_value_is_reported_as_no_limit(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_PAGES_PER_TYPE": "0"}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_PAGES_PER_TYPE")

        self.assertEqual(diagnostic.effective_value, 0)
        self.assertIn("0 means no limit.", diagnostic.notes)

    def test_skip_prefix_diagnostics_show_normalized_effective_value(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": "  /search/ , silk/ "}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.raw_value, "  /search/ , silk/ ")
        self.assertEqual(diagnostic.effective_value, ["search/", "silk/"])
        self.assertIn("strip leading slashes", diagnostic.notes)

    def test_blank_skip_prefix_env_value_clears_exclusions(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": ""}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.effective_value, [])
        self.assertIn("clear all exclusions", diagnostic.notes)

    def test_whitespace_only_skip_prefix_env_value_clears_exclusions(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_SKIP_URL_PREFIXES": "   "}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.raw_value, "   ")
        self.assertEqual(diagnostic.effective_value, [])
        self.assertIn("clear all exclusions", diagnostic.notes)

    def test_api_key_diagnostics_mask_secret_values(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "super-secret"}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.effective_value, "super-secret")
        self.assertEqual(diagnostic.raw_display, "Configured (12 chars)")
        self.assertEqual(diagnostic.effective_display, "Configured (12 chars)")

    def test_blank_api_key_env_value_is_ignored(self):
        with patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": ""}):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "env")
        self.assertEqual(diagnostic.effective_value, "")
        self.assertIn("Blank environment values are ignored.", diagnostic.notes)

    @override_settings(WAGTAIL_UNVEIL_API_KEY=True)
    def test_non_string_api_key_value_is_reported_as_invalid(self):
        with patch.dict("os.environ", {}, clear=True):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "django")
        self.assertEqual(diagnostic.raw_value, True)
        self.assertEqual(diagnostic.effective_value, "")
        self.assertIn("Non-string values are ignored.", diagnostic.notes)

    @override_settings(WAGTAIL_UNVEIL_API_KEY="  padded-key  ")
    def test_api_key_diagnostics_note_whitespace_stripping(self):
        with patch.dict("os.environ", {}, clear=True):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "django")
        self.assertEqual(diagnostic.effective_value, "padded-key")
        self.assertIn("whitespace is stripped", diagnostic.notes)

    @override_settings(WAGTAIL_UNVEIL_API_KEY="   ")
    def test_blank_string_api_key_is_reported_as_unconfigured(self):
        with patch.dict("os.environ", {}, clear=True):
            diagnostic = self._get_diagnostic("WAGTAIL_UNVEIL_API_KEY")

        self.assertEqual(diagnostic.source, "django")
        self.assertEqual(diagnostic.effective_value, "")
        self.assertIn("leave Bearer authentication unconfigured", diagnostic.notes)
