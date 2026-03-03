# AGENTS.md

This file contains package-specific guidance for `wagtail_unveil/`.

## Purpose

`wagtail_unveil` is the reusable package. Code in this directory must work when installed into any Wagtail project and must not depend on `sandbox/`.

The current public interface is URL-based and admin-integrated: URLconf inclusion, JSON API views, HTML report views, and the Wagtail dashboard panel. Package-level management commands are not currently provided.

## Key Files

- `apps.py` — Django app config
- `models.py` — package models
- `settings.py` — settings helpers for page limits, skip prefixes, and API key lookup
- `urls.py` — package URL config with app name `wagtail_unveil`
- `views.py` — JSON and HTML report views
- `wagtail_hooks.py` — Wagtail admin integration and dashboard panel
- `discovery/backend.py` — admin URL discovery
- `discovery/frontend.py` — frontend URL discovery
- `discovery/utils.py` — shared resolver utilities
- `templates/wagtail_unveil/` — report and dashboard templates
- `static/wagtail_unveil/css/` — shared report styles
- `static/wagtail_unveil/js/` — ordered, no-build report JavaScript modules plus bootstrap

## Package Interfaces

`wagtail_unveil` currently exposes:

- URLconf inclusion via `wagtail_unveil.urls`
- JSON API endpoints
- HTML report views
- Wagtail dashboard integration

Do not document or assume package management commands unless they are reintroduced in code.

### Settings

- `WAGTAIL_UNVEIL_PAGES_PER_TYPE`
- `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`
- `WAGTAIL_UNVEIL_API_KEY`

`get_api_key()` checks the environment first, then Django settings fallback.

### URL Names

The package exports one URL namespace:

- `wagtail_unveil:api_admin_urls`
- `wagtail_unveil:api_frontend_urls`
- `wagtail_unveil:report_admin_urls`
- `wagtail_unveil:report_frontend_urls`

Do not document or reintroduce the old split `api_urls.py` / `report_urls.py` namespace layout unless the code changes back to that design.

### JSON Response Shape

JSON API endpoints preserve top-level `urls` and `count` fields and also return a `metadata` object containing:

- `generated_at`
- `applied_filter`
- `total_count`
- `testable_count`
- `untestable_count`
- `package_version`

## Discovery Notes

### Admin URLs

`get_admin_urls()` walks Django URL patterns, filters admin routes, and resolves parameterized URLs using real objects where possible. Resolution falls back through view metadata and name-based model extraction for modeladmin-style routes.

### Frontend URLs

`get_frontend_urls()` combines:

- live Wagtail page URLs
- additional page-derived routes for forms and `RoutablePageMixin`
- non-admin resolver routes

Parameterized routable sub-routes are discovered but marked non-testable.

## Constraints

- Never import from `sandbox`
- Keep templates under `templates/wagtail_unveil/`
- Keep static assets under `static/wagtail_unveil/`
- Keep reusable logic out of ad hoc sandbox helpers

## Testing

Tests for this package live in the root `tests/` package and should be run with:

```bash
uv run --env-file .env django-admin test tests
```

Use `django.test.TestCase`, and use Wagtail test helpers only where admin behavior requires them.
