from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from wagtail_unveil.api_contract import get_api_contract

V1_CONTRACT = get_api_contract("v1")
API_URL = f"/unveil/{V1_CONTRACT.platform_url_path}"


@override_settings(DEBUG=True)
@patch.dict("os.environ", {"WAGTAIL_UNVEIL_API_KEY": "test-secret"})
class TestPlatformAPIView(TestCase):
    def _write_manifest(self, content: str, filename: str = "requirements.txt") -> tuple[TemporaryDirectory, Path]:
        tempdir = TemporaryDirectory()
        manifest_path = Path(tempdir.name) / filename
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(content, encoding="utf-8")
        return tempdir, manifest_path

    def test_returns_platform_payload(self):
        tempdir, manifest_path = self._write_manifest("Django>=5.2\nwagtail==7.0\n")
        self.addCleanup(tempdir.cleanup)

        with self.settings(
            BASE_DIR=tempdir.name,
            WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
        ):
            with patch(
                "wagtail_unveil.platform_data.version",
                side_effect=lambda name: {"Django": "5.2.1", "wagtail": "7.0.2"}[name],
            ):
                response = self.client.get(
                    API_URL,
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("platform", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["platform"]["python_dependencies"]["source"]["path"], "requirements.txt")
        self.assertEqual(data["platform"]["python_dependencies"]["source"]["format"], "requirements.txt")
        self.assertEqual(
            [package["name"] for package in data["platform"]["python_dependencies"]["packages"]],
            ["Django", "wagtail"],
        )
        self.assertEqual(data["platform"]["warnings"], [])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertIn("Authorization", response["Vary"])
        self.assertIn("Cookie", response["Vary"])

    @patch("wagtail_unveil.views._get_package_version", return_value="9.9.9")
    @patch("wagtail_unveil.views.timezone.now")
    def test_returns_metadata(self, mock_now, _mock_version):
        mock_now.return_value = datetime(2026, 3, 2, 12, 34, 56, tzinfo=timezone.utc)

        tempdir, manifest_path = self._write_manifest("Django>=5.2\n")
        self.addCleanup(tempdir.cleanup)

        with self.settings(
            BASE_DIR=tempdir.name,
            WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
        ):
            with patch("wagtail_unveil.platform_data.version", return_value="5.2.1"):
                response = self.client.get(
                    API_URL,
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )

        metadata = response.json()["metadata"]
        self.assertEqual(metadata["api_version"], "v1")
        self.assertEqual(metadata["api_lifecycle"]["status"], "stable")
        self.assertEqual(metadata["generated_at"], "2026-03-02T12:34:56+00:00")
        self.assertEqual(metadata["package_version"], "9.9.9")
        self.assertEqual(response.json()["platform"]["warnings"], [])
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)

    def test_requires_api_key(self):
        response = self.client.get(API_URL)
        self.assertEqual(response.status_code, 403)

    def test_rejects_wrong_key(self):
        response = self.client.get(
            API_URL,
            HTTP_AUTHORIZATION="Bearer wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_500_when_no_api_key_is_configured(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY=""):
                response = self.client.get(
                    API_URL,
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )

        self.assertEqual(response.status_code, 500)

    def test_uses_settings_fallback_when_env_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.settings(WAGTAIL_UNVEIL_API_KEY="test-from-settings"):
                response = self.client.get(
                    API_URL,
                    HTTP_AUTHORIZATION="Bearer test-from-settings",
                )

        self.assertEqual(response.status_code, 200)

    def test_superuser_session_fallback_is_not_allowed_for_platform_endpoint(self):
        User.objects.create_superuser(username="admin", password="password")
        self.client.login(username="admin", password="password")

        response = self.client.get(API_URL)

        self.assertEqual(response.status_code, 403)

    def test_response_returns_manifest_basename_only(self):
        tempdir, manifest_path = self._write_manifest("Django>=5.2\n", filename="requirements/base.txt")
        self.addCleanup(tempdir.cleanup)

        with self.settings(
            BASE_DIR=tempdir.name,
            WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
        ):
            with patch("wagtail_unveil.platform_data.version", return_value="5.2.1"):
                response = self.client.get(
                    API_URL,
                    HTTP_AUTHORIZATION="Bearer test-secret",
                )

        self.assertEqual(response.json()["platform"]["python_dependencies"]["source"]["path"], "base.txt")
        self.assertNotIn(str(manifest_path), response.content.decode())

    def test_returns_warning_when_no_manifest_is_configured(self):
        with self.settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=""):
            response = self.client.get(
                API_URL,
                HTTP_AUTHORIZATION="Bearer test-secret",
            )

        data = response.json()
        self.assertEqual(data["platform"]["python_dependencies"]["source"]["path"], "")
        self.assertIsNone(data["platform"]["python_dependencies"]["source"]["format"])
        self.assertEqual(data["platform"]["python_dependencies"]["packages"], [])
        self.assertEqual(data["platform"]["warnings"], ["No dependency manifest is configured."])

    @patch("wagtail_unveil.views.get_api_contract")
    def test_response_sets_deprecation_headers_for_deprecated_contract(self, mock_get_api_contract):
        deprecated_contract = replace(
            V1_CONTRACT,
            status="deprecated",
            deprecated_on=date(2026, 1, 1),
            sunset_on=date(2026, 12, 31),
        )
        mock_get_api_contract.return_value = deprecated_contract

        response = self.client.get(
            API_URL,
            HTTP_AUTHORIZATION="Bearer test-secret",
        )

        self.assertEqual(response["Deprecation"], "true")
        self.assertIn("Sunset", response)
        self.assertEqual(response.json()["metadata"]["api_lifecycle"]["status"], "deprecated")
