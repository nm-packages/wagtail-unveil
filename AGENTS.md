# AGENTS.md

Agent-agnostic guidance for working in this repository.

## Scope

- Reusable package: `wagtail_unveil/`
- Example project for development/testing: `sandbox/`
- Tests: `tests/` (root-level, not part of distributable package)

## Project Summary

`wagtail-unveil` discovers URLs in Wagtail projects (admin + frontend), then exposes them via:
- management commands
- JSON API endpoints
- HTML reports in Wagtail admin

## Critical Boundaries

- Keep `wagtail_unveil/` reusable and independent of `sandbox/`.
- Use `sandbox/` only as a fixture project to exercise discovery behavior.

## Development Workflow

Preferred commands:

```bash
make setup
make runserver
make test
make lint
```

Equivalent direct commands use `uv`, e.g.:

```bash
uv run --env-file .env django-admin test tests
```

## Key Configuration Semantics

- `WAGTAIL_UNVEIL_PAGES_PER_TYPE`:
  - omitted -> default `1` page per type
  - `0` -> no limit
  - positive int -> limit per page type
  - invalid/negative values -> fallback `1`
- `WAGTAIL_UNVEIL_API_KEY`:
  - used for API Bearer auth
  - environment variable takes precedence over Django settings

## Reference Docs

- Repository-level details: `CLAUDE.md`
- Package-level details: `wagtail_unveil/CLAUDE.md`
- Sandbox details: `sandbox/CLAUDE.md`
- Coding conventions: `CONVENTIONS.md`
