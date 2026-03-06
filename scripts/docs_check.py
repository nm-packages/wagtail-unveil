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
DEVELOPMENT_DOC_PATH = ROOT / "docs/development.md"

# This list is the single source of truth for contributor-facing Makefile
# targets that must be discoverable in both AGENTS.md and docs/development.md.
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

README_GUIDE_LINK_RE = re.compile(
    r"Contributor/developer guide:\s*\[docs/development\.md\]\(docs/development\.md\)",
    re.IGNORECASE,
)
SETUP_SUPERUSER_LINE_RE = re.compile(r"make\s+setup[^\n]*superuser", re.IGNORECASE)
SETUP_SUPERUSER_NEGATION_RE = re.compile(
    r"\b(doesn't|does not|do not|did not|never)\b",
    re.IGNORECASE,
)


def _extract_phony_targets(makefile_text: str) -> set[str]:
    match = re.search(r"^\.PHONY:\s+(.+)$", makefile_text, flags=re.MULTILINE)
    if not match:
        return set()
    return set(match.group(1).split())


def _missing_command_mentions(text: str, targets: list[str]) -> list[str]:
    return [target for target in targets if f"make {target}" not in text]


def main() -> int:
    errors: list[str] = []

    makefile_text = MAKEFILE_PATH.read_text(encoding="utf-8")
    readme_text = README_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")
    development_doc_text = DEVELOPMENT_DOC_PATH.read_text(encoding="utf-8")

    phony_targets = _extract_phony_targets(makefile_text)
    if not phony_targets:
        errors.append("Makefile check: could not find .PHONY target list.")

    for target in REQUIRED_TARGETS:
        if target not in phony_targets:
            errors.append(f"Makefile check: required target '{target}' is missing from .PHONY.")
        if re.search(rf"^{re.escape(target)}:", makefile_text, flags=re.MULTILINE) is None:
            errors.append(f"Makefile check: required target '{target}' has no target definition.")

    if README_GUIDE_LINK_RE.search(readme_text) is None:
        errors.append(
            "README check: missing required 'Contributor/developer guide' link to docs/development.md.",
        )

    agents_missing = _missing_command_mentions(agents_text, REQUIRED_TARGETS)
    if agents_missing:
        errors.append(
            "AGENTS check: missing make command mentions: "
            + ", ".join(f"'make {target}'" for target in agents_missing)
            + ".",
        )

    development_missing = _missing_command_mentions(development_doc_text, REQUIRED_TARGETS)
    if development_missing:
        errors.append(
            "Development docs check: missing make command mentions in docs/development.md: "
            + ", ".join(f"'make {target}'" for target in development_missing)
            + ".",
        )

    setup_claim_terms = (
        "create",
        "creates",
        "creating",
        "require",
        "requires",
        "includes",
        "included",
        "adding",
        "adds",
        "add",
        "made",
    )
    for line in development_doc_text.splitlines():
        lower_line = line.lower()
        if SETUP_SUPERUSER_LINE_RE.search(line) is None:
            continue
        if SETUP_SUPERUSER_NEGATION_RE.search(lower_line):
            continue
        if any(term in lower_line for term in setup_claim_terms):
            errors.append(
                "Development docs check: stale setup comment found; this doc must not claim "
                "that `make setup` creates superuser access.",
            )
            break

    if errors:
        for error in errors:
            print(error)
        return 1

    print("docs-check passed: Makefile, README, AGENTS, and docs/development.md are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
