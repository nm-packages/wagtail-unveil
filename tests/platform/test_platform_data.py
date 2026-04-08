from importlib.metadata import PackageNotFoundError
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from wagtail_unveil.platform_data import get_platform_snapshot


class TestPlatformSnapshot(SimpleTestCase):
    def test_no_manifest_configured_returns_warning(self):
        with patch.dict("os.environ", {}, clear=True):
            with override_settings(WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=""):
                snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.path, "")
        self.assertIsNone(snapshot.dependency_source.format)
        self.assertEqual(snapshot.python_dependencies, [])
        self.assertEqual(snapshot.warnings, ["No dependency manifest is configured."])

    def test_relative_path_resolves_from_base_dir_for_requirements_files(self):
        with TemporaryDirectory() as tempdir:
            base_dir = Path(tempdir)
            manifest_path = base_dir / "requirements" / "base.txt"
            manifest_path.parent.mkdir()
            manifest_path.write_text("Django>=5.2\nwagtail==7.0\n", encoding="utf-8")

            with override_settings(
                BASE_DIR=base_dir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE="requirements/base.txt",
            ):
                with patch.dict("os.environ", {}, clear=True):
                    with patch(
                        "wagtail_unveil.platform_data.version",
                        side_effect=lambda name: {"Django": "5.2.1", "wagtail": "7.0.2"}[name],
                    ):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.path, str(manifest_path))
        self.assertEqual(snapshot.dependency_source.format, "requirements.txt")
        self.assertEqual(
            [dependency.name for dependency in snapshot.python_dependencies],
            ["Django", "wagtail"],
        )
        self.assertEqual(snapshot.python_dependencies[0].installed_version, "5.2.1")
        self.assertEqual(snapshot.python_dependencies[1].installed_version, "7.0.2")

    def test_env_var_wins_over_django_setting_for_manifest_path(self):
        with TemporaryDirectory() as tempdir:
            base_dir = Path(tempdir)
            env_manifest_path = base_dir / "requirements.txt"
            env_manifest_path.write_text("Django>=5.2\n", encoding="utf-8")

            with override_settings(
                BASE_DIR=base_dir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE="ignored.txt",
            ):
                with patch.dict(
                    "os.environ",
                    {"WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE": str(env_manifest_path)},
                    clear=True,
                ):
                    with patch("wagtail_unveil.platform_data.version", return_value="5.2.1"):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.path, str(env_manifest_path))
        self.assertEqual(snapshot.python_dependencies[0].name, "Django")

    def test_standard_pyproject_includes_runtime_optional_and_dependency_groups(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "pyproject.toml"
            manifest_path.write_text(
                """
[project]
name = "demo"
version = "0.1.0"
dependencies = ["wagtail>=7.0", "Django>=5.2"]

[project.optional-dependencies]
docs = ["mkdocs>=1.6"]

[dependency-groups]
dev = ["ruff>=0.9", {include-group = "docs-tools"}]
docs-tools = ["mkdocs-material>=9.6"]
""".strip(),
                encoding="utf-8",
            )

            versions = {
                "Django": "5.2.1",
                "mkdocs": "1.6.1",
                "mkdocs-material": "9.6.0",
                "ruff": "0.9.2",
                "wagtail": "7.0.2",
            }
            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("wagtail_unveil.platform_data.version", side_effect=lambda name: versions[name]):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.format, "pyproject.toml")
        self.assertEqual(
            [dependency.name for dependency in snapshot.python_dependencies],
            ["Django", "mkdocs", "mkdocs-material", "mkdocs-material", "ruff", "wagtail"],
        )
        self.assertEqual(snapshot.python_dependencies[0].source_kind, "runtime")
        self.assertEqual(snapshot.python_dependencies[1].source_kind, "optional")
        self.assertEqual(snapshot.python_dependencies[1].source_name, "docs")
        self.assertEqual(snapshot.python_dependencies[2].source_kind, "group")
        self.assertEqual(snapshot.python_dependencies[2].source_name, "dev")
        self.assertEqual(snapshot.python_dependencies[3].source_kind, "group")
        self.assertEqual(snapshot.python_dependencies[3].source_name, "docs-tools")
        self.assertEqual(snapshot.python_dependencies[4].source_kind, "group")
        self.assertEqual(snapshot.python_dependencies[4].source_name, "dev")

    def test_poetry_pyproject_includes_runtime_extra_and_group_dependencies(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "pyproject.toml"
            manifest_path.write_text(
                """
[tool.poetry]
name = "demo"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
django = "^5.2"
sentry-sdk = { version = "^2.0", optional = true }

[tool.poetry.extras]
monitoring = ["sentry-sdk"]

[tool.poetry.group.dev.dependencies]
ruff = "^0.9"
""".strip(),
                encoding="utf-8",
            )

            versions = {
                "django": "5.2.1",
                "ruff": "0.9.2",
                "sentry-sdk": "2.21.0",
            }
            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("wagtail_unveil.platform_data.version", side_effect=lambda name: versions[name]):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.format, "poetry-pyproject")
        self.assertEqual(
            [dependency.name for dependency in snapshot.python_dependencies],
            ["django", "ruff", "sentry-sdk"],
        )
        self.assertEqual(snapshot.python_dependencies[0].source_kind, "runtime")
        self.assertEqual(snapshot.python_dependencies[1].source_kind, "group")
        self.assertEqual(snapshot.python_dependencies[1].source_name, "dev")
        self.assertEqual(snapshot.python_dependencies[2].source_kind, "optional")
        self.assertEqual(snapshot.python_dependencies[2].source_name, "monitoring")

    def test_missing_installed_package_is_marked_uninstalled(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "requirements.txt"
            manifest_path.write_text("missing-package>=1.0\n", encoding="utf-8")

            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    with patch(
                        "wagtail_unveil.platform_data.version",
                        side_effect=PackageNotFoundError,
                    ):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.python_dependencies[0].installed_version, "")
        self.assertFalse(snapshot.python_dependencies[0].is_installed)

    def test_missing_manifest_returns_warning(self):
        with TemporaryDirectory() as tempdir:
            missing_path = Path(tempdir) / "missing.txt"
            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(missing_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.python_dependencies, [])
        self.assertIn("does not exist", snapshot.warnings[0])

    def test_unreadable_manifest_returns_warning(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "requirements.txt"
            manifest_path.write_text("Django>=5.2\n", encoding="utf-8")

            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("pathlib.Path.read_text", side_effect=PermissionError("denied")):
                        snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.python_dependencies, [])
        self.assertIn("Could not read dependency manifest", snapshot.warnings[0])

    def test_unparseable_pyproject_returns_warning(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "pyproject.toml"
            manifest_path.write_text("[project\nbroken = true\n", encoding="utf-8")

            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.python_dependencies, [])
        self.assertIn("Could not read dependency manifest", snapshot.warnings[0])

    def test_unsupported_manifest_returns_warning(self):
        with TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "deps.lock"
            manifest_path.write_text("{}", encoding="utf-8")

            with override_settings(
                BASE_DIR=tempdir,
                WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=str(manifest_path),
            ):
                with patch.dict("os.environ", {}, clear=True):
                    snapshot = get_platform_snapshot()

        self.assertEqual(snapshot.dependency_source.format, "unknown")
        self.assertEqual(snapshot.python_dependencies, [])
        self.assertIn("Unsupported dependency manifest format", snapshot.warnings[0])
