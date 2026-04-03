# AGENTS.md

This file is the canonical guidance for coding agents working in this repository.

## Project Overview

**wagtail-unveil** is a reusable Wagtail package that discovers frontend and Wagtail admin URLs in a site. It exposes that functionality through JSON endpoints, HTML reports, and a Wagtail dashboard panel so developers can inspect URLs and test whether they return expected response codes.

## Repository Structure

- `wagtail_unveil/` — The distributable package published to PyPI
- `sandbox/` — Example Wagtail project used for development and testing
- `tests/` — Root-level test package for the reusable package
- `.env.example` — Template for local development environment variables

## Docs Map

- `README.md` — user-facing package overview and minimal quickstart
- `docs/index.md` — canonical documentation hub for users, contributors, and maintainers
- `docs/contributing/development.md` — human contributor setup, day-to-day workflow, and CI-aligned dev commands
- `AGENTS.md` files — canonical agent-facing guidance and documentation contract

## Development Commands

These commands are for contributors working in this repository's sandbox and test environment. They are not package-level interfaces exposed by `wagtail_unveil`.

Prefer the `Makefile` targets for standard workflows:

```bash
make setup           # env, install, migrate, sample data
make runserver       # start the sandbox dev server
make test            # run package tests
make test-js         # run JavaScript report tests
make build-assets    # build report frontend assets (JavaScript + CSS)
make lint-assets     # Biome frontend asset lint/format checks (JavaScript + CSS)
make lint-assets-fix # Biome frontend asset lint/format with autofix
make tox             # run the version matrix
make tox-smoke       # run the fast smoke subset used in PR CI
make lint            # ruff check
make lint-fix        # ruff check --fix
make coverage        # run tests with coverage report
make coverage-html   # generate HTML coverage report
make pre-commit      # run all configured hooks
```

Equivalent direct commands are also valid:

```bash
uv sync
uv run --env-file .env django-admin migrate
uv run --env-file .env django-admin runserver
uv run --env-file .env django-admin test tests
uv run ruff check .
uv run tox
uv run tox -m smoke
npm run lint:assets
npm run lint:assets:fix
npm run test:js
npm run build:assets
```

Release preflight commands:

```bash
uv build --sdist --wheel --out-dir /tmp/wagtail-unveil-dist-check
uvx twine check /tmp/wagtail-unveil-dist-check/*
```

Maintainer release publishing is CI-driven from GitHub Releases via `.github/workflows/release.yml`.
Use `docs/contributing/releasing.md` as the canonical release runbook.

## Architecture Summary

### URL Discovery

The core discovery logic lives in `wagtail_unveil/discovery/`.

- `discovery/backend.py` — `BackendURL` dataclass and `get_admin_urls()`
- `discovery/backend_resolution.py` — admin parameter resolution helpers
- `discovery/extensions.py` — hookable admin instance resolver extensions for installed Wagtail packages
- `discovery/frontend.py` — `FrontendURL` dataclass and `get_frontend_urls()`
- `discovery/frontend_resolution.py` — frontend routable and API URL resolution helpers
- `discovery/utils.py` — shared resolver walking and route normalization helpers
- `docs/contributing/discovery-architecture.md` — canonical contributor-facing explanation of discovery, normalization, parameter resolution, and testability rules

Admin URL discovery walks Django's resolver tree, filters to admin routes, and attempts to resolve parameterized URLs against real database objects where possible.
Developer-installed Wagtail packages can extend that parameter resolution through the `register_unveil_admin_instance_resolvers` Wagtail hook instead of adding package-specific logic directly to `wagtail_unveil`.

Frontend URL discovery combines:

- live Wagtail page URLs
- additional page-derived URLs such as form landing pages and `RoutablePageMixin` sub-routes
- non-admin Django resolver routes

### Delivery Layer

The package exposes a single URL config in `wagtail_unveil/urls.py` with `app_name = "wagtail_unveil"`.

Included by a consuming project as:

```python
path("unveil/", include("wagtail_unveil.urls"))
```

Routes provided:

- `api/v1/backend-urls/` → `wagtail_unveil:api_v1_backend_urls`
- `api/v1/frontend-urls/` → `wagtail_unveil:api_v1_frontend_urls`
- `report/backend-urls/` → `wagtail_unveil:report_backend_urls`
- `report/frontend-urls/` → `wagtail_unveil:report_frontend_urls`
- `report/settings/` → `wagtail_unveil:report_settings`

Versioned API paths, URL names, and lifecycle metadata are derived from the
internal `wagtail_unveil.api_contract.API_VERSION_REGISTRY`.
New API versions should be added in parallel and deprecate older versions over a documented window.
Additional `api/vN/...` routes may be present when newer versions are introduced.
Canonical contributor policy for versioning decisions and implementation workflow:
`docs/contributing/api-versioning.md`.

JSON endpoints use Bearer token auth via `WAGTAIL_UNVEIL_API_KEY`. HTML report views require a superuser and `DEBUG=True`.

### Sandbox

The sandbox project mounts the package at `/unveil/`, exposes Wagtail API v2 routes at `/api/v2/`, and serves Wagtail pages from `/`.

## Coding Conventions

See [CONVENTIONS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/CONVENTIONS.md) for the full project conventions. Important rules:

- Use double quotes consistently
- Sort modules using the flow-first organization guidance in `CONVENTIONS.md`
- Use `path()` and namespaced URLs
- Keep `wagtail_unveil/` independent from `sandbox/`
- Prefer Wagtail ViewSet patterns for admin integration
- Keep tests in the root `tests/` package

## Verification Expectations

After changing code in `wagtail_unveil/` or `tests/`:

1. Run `make lint`
2. Run `make coverage`
3. Inspect coverage for touched files and add tests for newly introduced uncovered lines
4. Update `README.md` and relevant agent guidance files when behavior or structure changes

## Directory-Specific Guidance

More focused guidance lives in:

- [wagtail_unveil/AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/wagtail_unveil/AGENTS.md) — package-specific architecture and constraints
- [sandbox/AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/sandbox/AGENTS.md) — sandbox-specific structure and sample-data notes

## Documentation Contract

- `AGENTS.md` files are the canonical agent-facing project guidance
- Root `AGENTS.md` owns repo-wide guidance
- Nested `AGENTS.md` files own only directory-local guidance
- `docs/contributing/discovery-architecture.md` is the canonical contributor-facing reference for discovery and resolution behavior; AGENTS files should point to it rather than duplicating detailed flow logic
- `docs/contributing/development.md` is the canonical human contributor workflow guide for local setup, validation loops, and CI-oriented dev commands
- `docs/contributing/frontend-assets.md` is the canonical contributor-facing reference for frontend asset source, build/test workflow, and CI expectations
- `docs/contributing/api-versioning.md` is the canonical contributor-facing reference for API version lifecycle policy and version-bump workflow
- `docs/contributing/releasing.md` is the canonical contributor-facing reference for release workflow, PyPI Trusted Publisher setup, and maintainer release troubleshooting
- Command-level docs must stay in sync with `Makefile`; when targets change, update `AGENTS.md` and `docs/contributing/development.md` in the same PR. `README.md` should link to this contributor workflow, not duplicate command lists.
