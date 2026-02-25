# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**wagtail-unveil** is a reusable Wagtail package that discovers all URLs (hardcoded and generated) in a Wagtail site — both frontend and backend (Wagtail admin) URLs. It provides admin listing pages where developers can inspect and test URLs, primarily to verify they return 200 OK rather than error codes. The package is intended for distribution via PyPI.

## Repository Structure

- `wagtail_unveil/` — The reusable package (installable from PyPI)
- `sandbox/` — An example Wagtail site with the package installed, used for development and testing
- `tests/` — Root-level test package, split by feature area (not inside the distributable package)
- `.env.example` — Template for `.env`; copy to `.env` before developing (`cp .env.example .env`)

## Makefile

A `Makefile` provides shortcuts for common development tasks:

```bash
make setup          # Full dev setup: env, install, migrate, superuser, sample-data
make runserver      # Start the sandbox dev server (alias: make run)
make test           # Run package tests
make tox            # Run tests across all Python/Django/Wagtail versions
make lint           # Run ruff check
make lint-fix       # Run ruff check --fix
make pre-commit     # Run pre-commit hooks on all files
make coverage       # Run tests with coverage and show terminal report
make coverage-html  # Generate HTML coverage report and open it
make makemigrations # Create package migrations
make sample-data    # Create sample data
make clean          # Remove db.sqlite3 and .env
```

## Development Commands

The full commands (also used by the Makefile):

```bash
# Install dependencies (uses uv)
uv sync

# Run the sandbox dev server
uv run --env-file .env django-admin runserver

# Run migrations
uv run --env-file .env django-admin migrate

# Create migrations for the package
uv run --env-file .env django-admin makemigrations wagtail_unveil

# Run all tests
uv run --env-file .env django-admin test

# Run tests for the package only
uv run --env-file .env django-admin test tests

# Run a single test module
uv run --env-file .env django-admin test tests.test_admin_urls

# Run a single test class
uv run --env-file .env django-admin test tests.test_admin_urls.TestGetAdminUrls

# Run a single test method
uv run --env-file .env django-admin test tests.test_admin_urls.TestGetAdminUrls.test_returns_list_of_admin_url_objects

# Lint
uv run ruff check .

# Lint and fix
uv run ruff check --fix .

# Create sample data (images, documents, redirects, etc.) in the sandbox
uv run --env-file .env django-admin create_sample_data

# Clear and recreate sample data
uv run --env-file .env django-admin create_sample_data --clear

# Run tests with coverage
uv run --env-file .env coverage run -m django test tests
uv run --env-file .env coverage report

# Generate HTML coverage report
uv run --env-file .env coverage html

# Run tox (all Python/Django/Wagtail versions)
uv run tox

# Run tox for a single environment
uv run tox -e py313-django52-wagtail70

# Run tox with specific test args
uv run tox -- tests.test_admin_urls
```

## Architecture

### URL Discovery Engine (`wagtail_unveil/urls.py`)

The core of the package. Two parallel discovery systems that produce dataclass instances (no database models):

**Admin URLs** — `get_admin_urls()` walks Django's URL resolver tree via `_walk_patterns()`, filtering to `admin/` routes. Each URL is classified as static or parameterized. Parameterized URLs go through a multi-tier model extraction fallback:
1. View `initkwargs` (ModelViewSet pattern)
2. Class `model` attribute
3. Cached property `model` attribute
4. Name-based parsing for modeladmin-style URLs

Once a model is found, the first real DB instance is fetched and the URL is reversed with its PK to make it testable.

**Frontend URLs** — `get_frontend_urls()` combines two sources:
- **Page source:** `Page.objects.live().specific()` → `.url` → path-only. Special handling for `FormMixin` (adds POST landing page entry) and `RoutablePageMixin` (discovers `@path()` sub-routes via `_get_routable_sub_urls()`)
- **Resolver source:** Non-admin Django routes via `_walk_patterns()`, excluding `admin/`, `django-admin/`, and unveil's own namespaces

### Delivery Layer

- **Management commands** (`show_admin_urls`, `show_frontend_urls`) — terminal output
  - `show_admin_urls --static` / `--parameterized` — filter to static or parameterized routes only
  - `show_frontend_urls --pages` / `--resolver` — filter to page-source or resolver-source URLs only
- **JSON API** (`wagtail_unveil/api_urls.py`, namespace `wagtail_unveil_api`) — bearer token auth via `WAGTAIL_UNVEIL_API_KEY` env var; `?filter=static|parameterized` / `?filter=pages|resolver` query params supported
- **HTML reports** (`wagtail_unveil/report_urls.py`, namespace `wagtail_unveil_report`) — superuser + `DEBUG=True` only; client-side fetch testing with search, sort, Test All, and Hide Untestable (cookie-persisted)
- **Dashboard widget** (`wagtail_hooks.py`) — registers panel linking to both reports, superuser + `DEBUG=True` only

### Frontend (JS/CSS)

Single `admin_urls_report.js` shared by both report templates. Uses `data-sort-col` attributes for generic column matching across admin and frontend tables. Features: search, sort, fetch-based URL testing, Test All with pause/cancel, "Hide Untestable" toggle with cookie persistence.

### Configuration

- `WAGTAIL_UNVEIL_PAGES_PER_TYPE` Django setting (default `0` = all pages; positive int = limit per page type)
- `WAGTAIL_UNVEIL_API_KEY` env var for API authentication (absent → 500; invalid → 403)

### Consuming Project Setup

Add to `INSTALLED_APPS`: `"wagtail_unveil"`. Then include both URL configs in `urls.py`:

```python
path("unveil-api/", include("wagtail_unveil.api_urls")),
path("unveil-report/", include("wagtail_unveil.report_urls")),
```

### Sandbox Apps

Each sandbox app exists to exercise a specific discovery scenario:
- `calendar/` — custom ViewSet admin pages
- `inventory/` — `ModelViewSet` + `ModelViewSetGroup` + chooser
- `taxonomy/` — snippets + modeladmin (parameterized URL resolution)
- `forms/` — `AbstractEmailForm` (form page discovery)
- `events/` — `RoutablePageMixin` with static and parameterized sub-routes
- `core/` — page types + wagtail.contrib.settings

### Test Structure

Tests in `tests/` mirror the delivery layer:
- `test_admin_urls.py` / `test_frontend_urls.py` — discovery logic
- `test_admin_views.py` / `test_frontend_views.py` — API + report endpoints
- `test_settings.py` — configuration behaviour

## Conventions

See [CONVENTIONS.md](CONVENTIONS.md) for all coding conventions. Follow these strictly.

## Tech Stack

- Python 3.10+, Wagtail 7.0–7.3, Django 4.2/5.1/5.2/6.0
- `uv` for dependency management (pyproject.toml + uv.lock)
- SQLite for local development
- Django test runner for tests, ruff for linting (line length 120), pre-commit for git hooks
