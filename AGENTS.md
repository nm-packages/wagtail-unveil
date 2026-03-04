# AGENTS.md

This file is the canonical guidance for coding agents working in this repository.

## Project Overview

**wagtail-unveil** is a reusable Wagtail package that discovers frontend and Wagtail admin URLs in a site. It exposes that functionality through JSON endpoints, HTML reports, and a Wagtail dashboard panel so developers can inspect URLs and test whether they return expected response codes.

## Repository Structure

- `wagtail_unveil/` — The distributable package published to PyPI
- `sandbox/` — Example Wagtail project used for development and testing
- `tests/` — Root-level test package for the reusable package
- `.env.example` — Template for local development environment variables

## Development Commands

These commands are for contributors working in this repository's sandbox and test environment. They are not package-level interfaces exposed by `wagtail_unveil`.

Prefer the `Makefile` targets for standard workflows:

```bash
make setup       # env, install, migrate, sample data
make runserver   # start the sandbox dev server
make test        # run package tests
make test-js     # run JavaScript report tests
make build-js    # build JavaScript report bundles
make tox         # run the version matrix
make lint        # ruff check
make lint-fix    # ruff check --fix
make coverage    # run tests with coverage report
make pre-commit  # run all configured hooks
```

Equivalent direct commands are also valid:

```bash
uv sync
uv run --env-file .env django-admin migrate
uv run --env-file .env django-admin runserver
uv run --env-file .env django-admin test tests
uv run ruff check .
uv run tox
npm run test:js
npm run build:js
```

## Architecture Summary

### URL Discovery

The core discovery logic lives in `wagtail_unveil/discovery/`.

- `discovery/backend.py` — `BackendURL` dataclass and `get_admin_urls()`
- `discovery/frontend.py` — `FrontendURL` dataclass and `get_frontend_urls()`
- `discovery/utils.py` — shared resolver walking and route normalization helpers
- `docs/discovery-architecture.md` — canonical contributor-facing explanation of discovery, normalization, parameter resolution, and testability rules

Admin URL discovery walks Django's resolver tree, filters to admin routes, and attempts to resolve parameterized URLs against real database objects where possible.

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

- `api/backend-urls/` → `wagtail_unveil:api_backend_urls`
- `api/frontend-urls/` → `wagtail_unveil:api_frontend_urls`
- `report/backend-urls/` → `wagtail_unveil:report_backend_urls`
- `report/frontend-urls/` → `wagtail_unveil:report_frontend_urls`

JSON endpoints use Bearer token auth via `WAGTAIL_UNVEIL_API_KEY`. HTML report views require a superuser and `DEBUG=True`.

### Sandbox

The sandbox project mounts the package at `/unveil/` and serves Wagtail pages from `/`.

## Coding Conventions

See [CONVENTIONS.md](CONVENTIONS.md) for the full project conventions. Important rules:

- Use double quotes consistently
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

- [wagtail_unveil/AGENTS.md](wagtail_unveil/AGENTS.md) — package-specific architecture and constraints
- [sandbox/AGENTS.md](sandbox/AGENTS.md) — sandbox-specific structure and sample-data notes

## Documentation Contract

- `AGENTS.md` files are the canonical agent-facing project guidance
- Root `AGENTS.md` owns repo-wide guidance
- Nested `AGENTS.md` files own only directory-local guidance
- `docs/discovery-architecture.md` is the canonical contributor-facing reference for discovery and resolution behavior; AGENTS files should point to it rather than duplicating detailed flow logic
