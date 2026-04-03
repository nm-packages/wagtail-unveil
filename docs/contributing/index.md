# Contributing

Guidance for contributors and maintainers working in this repository.

## Start Here

Read the [Development Guide](development.md) first if you are setting up the repo or looking for the standard contributor workflow.

## Choose The Right Page

- [Development Guide](development.md) — Read this if you need the canonical contributor workflow: local setup, validation commands, and CI-aligned day-to-day development.
- [API Versioning](api-versioning.md) — Read this if you are changing JSON API behavior and need the canonical lifecycle and version-bump policy.
- [Discovery Architecture](discovery-architecture.md) — Read this if you need the canonical reference for discovery, normalization, classification, and parameter resolution behavior.
- [Discovery Workflow Visual Reference](discovery-workflows.md) — Read this if you want a visual companion to the discovery architecture document before or while reading the authoritative rules.
- [Frontend Assets](frontend-assets.md) — Read this if you are changing report JavaScript or CSS and need the canonical asset workflow and CI expectations.
- [Releasing](releasing.md) — Read this if you are preparing or publishing a package release and need the canonical maintainer runbook.

## Quick Reference

```bash
make setup          # env, install, migrate, sample data
make test           # run tests
make lint           # ruff check
make coverage       # run tests with coverage
```

## Related

- [AGENTS.md](../../AGENTS.md) — Agent-facing project guidance
- [CONVENTIONS.md](../../CONVENTIONS.md) — Coding standards and patterns
- [Documentation Hub](../index.md) — Canonical top-level documentation entry point
