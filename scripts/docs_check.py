#!/usr/bin/env python3
"""Lightweight documentation drift checks for contributor commands."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAKEFILE_PATH = ROOT / "Makefile"
README_PATH = ROOT / "README.md"
AGENTS_PATH = ROOT / "AGENTS.md"

REQUIRED_TARGETS = [
    "setup",
    "runserver",
    "test",
    "test-js",
    "build-assets",
    "lint-assets",
    "lint-assets-fix",
    "tox",
    "tox-smoke",
    "lint",
    "lint-fix",
    "coverage",
    "coverage-html",
    "docs-check",
    "pre-commit",
]


def _extract_phony_targets(makefile_text: str) -> set[str]:
    match = re.search(r"^\.PHONY:\s+(.+)$", makefile_text, flags=re.MULTILINE)
    if not match:
        return set()
    return set(match.group(1).split())


def _extract_readme_development_section(readme_text: str) -> str:
    match = re.search(r"^## Development\n(.*?)(?:\n## |\Z)", readme_text, flags=re.DOTALL | re.MULTILINE)
    return match.group(1) if match else ""


def _missing_command_mentions(text: str, targets: list[str]) -> list[str]:
    return [target for target in targets if f"make {target}" not in text]


def main() -> int:
    errors: list[str] = []

    makefile_text = MAKEFILE_PATH.read_text(encoding="utf-8")
    readme_text = README_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")
    readme_dev_section = _extract_readme_development_section(readme_text)

    phony_targets = _extract_phony_targets(makefile_text)
    if not phony_targets:
        errors.append("Makefile check: could not find .PHONY target list.")

    for target in REQUIRED_TARGETS:
        if target not in phony_targets:
            errors.append(f"Makefile check: required target '{target}' is missing from .PHONY.")
        if re.search(rf"^{re.escape(target)}:", makefile_text, flags=re.MULTILINE) is None:
            errors.append(f"Makefile check: required target '{target}' has no target definition.")

    readme_missing = _missing_command_mentions(readme_dev_section, REQUIRED_TARGETS)
    if readme_missing:
        errors.append(
            "README check: missing make command mentions in Development section: "
            + ", ".join(f"'make {target}'" for target in readme_missing)
            + ".",
        )

    agents_missing = _missing_command_mentions(agents_text, REQUIRED_TARGETS)
    if agents_missing:
        errors.append(
            "AGENTS check: missing make command mentions: "
            + ", ".join(f"'make {target}'" for target in agents_missing)
            + ".",
        )

    if re.search(r"make setup[^\n]*superuser", readme_dev_section, flags=re.IGNORECASE):
        errors.append("README check: stale setup comment found; 'make setup' must not claim it creates a superuser.")

    if errors:
        for error in errors:
            print(error)
        return 1

    print("docs-check passed: Makefile, README, and AGENTS command docs are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
