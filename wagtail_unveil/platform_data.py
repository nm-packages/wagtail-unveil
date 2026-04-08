from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import wagtail
from django import get_version as get_django_version
from django.conf import settings

from wagtail_unveil.settings import get_platform_dependency_file

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib


@dataclass(frozen=True)
class PlatformRuntime:
    python_version: str
    python_implementation: str
    django_version: str
    wagtail_version: str


@dataclass(frozen=True)
class PlatformDependency:
    name: str
    specifier: str
    installed_version: str
    is_installed: bool
    source_kind: str
    source_name: str | None


@dataclass(frozen=True)
class PlatformDependencySource:
    path: str
    format: str | None


@dataclass(frozen=True)
class PlatformSnapshot:
    runtime: PlatformRuntime
    dependency_source: PlatformDependencySource
    python_dependencies: list[PlatformDependency]
    warnings: list[str]


def get_platform_snapshot() -> PlatformSnapshot:
    """Return runtime and dependency inventory for the current site."""
    runtime = PlatformRuntime(
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        django_version=get_django_version(),
        wagtail_version=wagtail.__version__,
    )

    configured_path = get_platform_dependency_file()
    if not configured_path:
        return PlatformSnapshot(
            runtime=runtime,
            dependency_source=PlatformDependencySource(path="", format=None),
            python_dependencies=[],
            warnings=["No dependency manifest is configured."],
        )

    manifest_path = _resolve_dependency_path(configured_path)
    if not manifest_path.exists():
        return PlatformSnapshot(
            runtime=runtime,
            dependency_source=PlatformDependencySource(path=str(manifest_path), format=None),
            python_dependencies=[],
            warnings=[f"Dependency manifest does not exist: {manifest_path}"],
        )

    dependency_format = _guess_dependency_format_from_name(manifest_path)

    try:
        dependency_format = _detect_dependency_format(manifest_path)
        if dependency_format == "unknown":
            return PlatformSnapshot(
                runtime=runtime,
                dependency_source=PlatformDependencySource(path=str(manifest_path), format="unknown"),
                python_dependencies=[],
                warnings=[f"Unsupported dependency manifest format: {manifest_path.name}"],
            )

        if dependency_format in {"pyproject.toml", "poetry-pyproject"}:
            dependencies, warnings = _parse_pyproject_dependencies(manifest_path)
        else:
            dependencies, warnings = _parse_requirements_file(manifest_path)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return PlatformSnapshot(
            runtime=runtime,
            dependency_source=PlatformDependencySource(path=str(manifest_path), format=dependency_format),
            python_dependencies=[],
            warnings=[f"Could not read dependency manifest {manifest_path}: {error}"],
        )

    dependencies = sorted(
        dependencies,
        key=lambda dependency: (
            dependency.name.lower(),
            dependency.source_kind,
            dependency.source_name or "",
            dependency.specifier,
        ),
    )
    return PlatformSnapshot(
        runtime=runtime,
        dependency_source=PlatformDependencySource(path=str(manifest_path), format=dependency_format),
        python_dependencies=dependencies,
        warnings=warnings,
    )


def _resolve_dependency_path(configured_path: str) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path
    base_dir = getattr(settings, "BASE_DIR", Path.cwd())
    return Path(base_dir) / path


def _detect_dependency_format(path: Path) -> str:
    if path.name == "pyproject.toml":
        return _detect_pyproject_format(path)
    return _guess_dependency_format_from_name(path)


def _guess_dependency_format_from_name(path: Path) -> str | None:
    if path.name == "pyproject.toml":
        return "pyproject.toml"
    if path.suffix in {".txt", ".in", ".pip"} or "requirements" in path.name.lower():
        return "requirements.txt"
    return "unknown"


def _detect_pyproject_format(path: Path) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    tool_data = data.get("tool", {})
    poetry_data = tool_data.get("poetry", {})
    if poetry_data.get("dependencies") or poetry_data.get("group") or poetry_data.get("extras"):
        return "poetry-pyproject"
    return "pyproject.toml"


def _parse_pyproject_dependencies(path: Path) -> tuple[list[PlatformDependency], list[str]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    dependencies: list[PlatformDependency] = []
    warnings: list[str] = []

    project_data = data.get("project", {})
    dependencies.extend(
        _build_string_dependencies(
            project_data.get("dependencies", []),
            source_kind="runtime",
            source_name=None,
        ),
    )

    optional_dependencies = project_data.get("optional-dependencies", {})
    if isinstance(optional_dependencies, dict):
        for extra_name, entries in optional_dependencies.items():
            dependencies.extend(
                _build_string_dependencies(
                    entries,
                    source_kind="optional",
                    source_name=str(extra_name),
                ),
            )

    dependency_groups = data.get("dependency-groups", {})
    if isinstance(dependency_groups, dict):
        for group_name, entries in dependency_groups.items():
            flattened_entries, group_warnings = _flatten_dependency_group_entries(
                dependency_groups,
                group_name=str(group_name),
                entries=entries,
            )
            dependencies.extend(
                _build_string_dependencies(
                    flattened_entries,
                    source_kind="group",
                    source_name=str(group_name),
                ),
            )
            warnings.extend(group_warnings)

    poetry_data = data.get("tool", {}).get("poetry", {})
    poetry_dependencies = poetry_data.get("dependencies", {})
    if isinstance(poetry_dependencies, dict):
        dependencies.extend(_build_poetry_runtime_dependencies(poetry_dependencies))

        extras = poetry_data.get("extras", {})
        if isinstance(extras, dict):
            dependencies.extend(_build_poetry_extra_dependencies(poetry_dependencies, extras, warnings))

    poetry_groups = poetry_data.get("group", {})
    if isinstance(poetry_groups, dict):
        dependencies.extend(_build_poetry_group_dependencies(poetry_groups))

    return dependencies, warnings


def _parse_requirements_file(path: Path) -> tuple[list[PlatformDependency], list[str]]:
    dependencies: list[PlatformDependency] = []
    warnings: list[str] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if line.startswith("-"):
            warnings.append(f"Skipped unsupported requirements directive on line {line_number}.")
            continue

        dependency = _build_dependency_from_requirement(
            line,
            source_kind="runtime",
            source_name=None,
        )
        if dependency is None:
            warnings.append(f"Skipped unparseable requirement on line {line_number}.")
            continue

        dependencies.append(dependency)

    return dependencies, warnings


def _flatten_dependency_group_entries(
    all_groups: dict,
    *,
    group_name: str,
    entries,
    seen: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    if seen is None:
        seen = set()

    if group_name in seen:
        return [], [f"Skipped recursive dependency group reference for {group_name!r}."]

    seen = seen | {group_name}
    flattened_entries: list[str] = []
    warnings: list[str] = []

    if not isinstance(entries, list):
        return [], [f"Skipped unsupported dependency group definition for {group_name!r}."]

    for entry in entries:
        if isinstance(entry, str):
            flattened_entries.append(entry)
            continue

        if isinstance(entry, dict) and isinstance(entry.get("include-group"), str):
            included_group_name = entry["include-group"]
            nested_entries, nested_warnings = _flatten_dependency_group_entries(
                all_groups,
                group_name=included_group_name,
                entries=all_groups.get(included_group_name, []),
                seen=seen,
            )
            flattened_entries.extend(nested_entries)
            warnings.extend(nested_warnings)
            continue

        warnings.append(f"Skipped unsupported dependency group entry in {group_name!r}.")

    return flattened_entries, warnings


def _build_string_dependencies(entries, *, source_kind: str, source_name: str | None) -> list[PlatformDependency]:
    if not isinstance(entries, list):
        return []

    dependencies: list[PlatformDependency] = []
    for entry in entries:
        if not isinstance(entry, str):
            continue
        dependency = _build_dependency_from_requirement(entry, source_kind=source_kind, source_name=source_name)
        if dependency is not None:
            dependencies.append(dependency)

    return dependencies


def _build_poetry_runtime_dependencies(poetry_dependencies: dict) -> list[PlatformDependency]:
    dependencies: list[PlatformDependency] = []
    for dependency_name, definition in poetry_dependencies.items():
        if dependency_name == "python":
            continue
        if _is_poetry_optional_dependency(definition):
            continue

        dependency = _build_poetry_dependency(
            dependency_name=str(dependency_name),
            definition=definition,
            source_kind="runtime",
            source_name=None,
        )
        if dependency is not None:
            dependencies.append(dependency)

    return dependencies


def _build_poetry_extra_dependencies(
    poetry_dependencies: dict,
    extras: dict,
    warnings: list[str],
) -> list[PlatformDependency]:
    dependencies: list[PlatformDependency] = []
    for extra_name, extra_entries in extras.items():
        if not isinstance(extra_entries, list):
            continue

        for extra_dependency_name in extra_entries:
            dependency_name = str(extra_dependency_name)
            definition = poetry_dependencies.get(dependency_name)
            if definition is None:
                warnings.append(f"Poetry extra {extra_name!r} references unknown dependency {dependency_name!r}.")
                continue

            dependency = _build_poetry_dependency(
                dependency_name=dependency_name,
                definition=definition,
                source_kind="optional",
                source_name=str(extra_name),
            )
            if dependency is not None:
                dependencies.append(dependency)

    return dependencies


def _build_poetry_group_dependencies(poetry_groups: dict) -> list[PlatformDependency]:
    dependencies: list[PlatformDependency] = []
    for group_name, group_definition in poetry_groups.items():
        if not isinstance(group_definition, dict):
            continue

        group_dependencies = group_definition.get("dependencies", {})
        if not isinstance(group_dependencies, dict):
            continue

        for dependency_name, definition in group_dependencies.items():
            if dependency_name == "python":
                continue

            dependency = _build_poetry_dependency(
                dependency_name=str(dependency_name),
                definition=definition,
                source_kind="group",
                source_name=str(group_name),
            )
            if dependency is not None:
                dependencies.append(dependency)

    return dependencies


def _is_poetry_optional_dependency(definition) -> bool:
    return isinstance(definition, dict) and bool(definition.get("optional"))


def _build_poetry_dependency(
    *,
    dependency_name: str,
    definition,
    source_kind: str,
    source_name: str | None,
) -> PlatformDependency | None:
    specifier = _poetry_dependency_specifier(definition)
    return _build_dependency(
        name=dependency_name,
        specifier=specifier,
        source_kind=source_kind,
        source_name=source_name,
    )


def _poetry_dependency_specifier(definition) -> str:
    if isinstance(definition, str):
        return definition

    if isinstance(definition, dict):
        version_specifier = definition.get("version")
        if isinstance(version_specifier, str):
            return version_specifier

        detail_parts = []
        for key in ("git", "path", "url", "file", "rev", "branch", "tag"):
            value = definition.get(key)
            if isinstance(value, str):
                detail_parts.append(f"{key}={value}")
        if detail_parts:
            return ", ".join(detail_parts)

    return ""


def _build_dependency_from_requirement(
    requirement: str,
    *,
    source_kind: str,
    source_name: str | None,
) -> PlatformDependency | None:
    parsed_requirement = _parse_requirement(requirement)
    if parsed_requirement is None:
        return None

    name, specifier = parsed_requirement
    return _build_dependency(
        name=name,
        specifier=specifier,
        source_kind=source_kind,
        source_name=source_name,
    )


def _build_dependency(*, name: str, specifier: str, source_kind: str, source_name: str | None) -> PlatformDependency:
    installed_version = _get_installed_version(name)
    return PlatformDependency(
        name=name,
        specifier=specifier,
        installed_version=installed_version or "",
        is_installed=installed_version is not None,
        source_kind=source_kind,
        source_name=source_name,
    )


def _get_installed_version(package_name: str) -> str | None:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def _parse_requirement(requirement: str) -> tuple[str, str] | None:
    match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    if not match:
        return None

    name = match.group(1)
    specifier = requirement[match.end() :].strip()
    return name, specifier
