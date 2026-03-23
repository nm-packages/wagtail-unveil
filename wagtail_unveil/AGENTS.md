# AGENTS.md

This file contains package-specific guidance for `wagtail_unveil/`.

## Purpose

`wagtail_unveil` is the reusable package. Code in this directory must work when installed into any Wagtail project and must not depend on `sandbox/`.

The current public interface is URL-based and admin-integrated: URLconf inclusion, JSON API views, HTML report views, and the Wagtail dashboard panel. Package-level management commands are not currently provided.

## Key Files

- `apps.py` — Django app config
- `api_contract.py` — internal API version registry and lifecycle metadata constants
- `models.py` — package models
- `../docs/contributing/discovery-architecture.md` — contributor reference for discovery internals, fallbacks, and limitations
- `settings.py` — settings helpers for page limits, skip prefixes, and API key lookup
- `urls.py` — package URL config with app name `wagtail_unveil`
- `views.py` — JSON and HTML report views
- `wagtail_hooks.py` — Wagtail admin integration and dashboard panel
- `discovery/backend.py` — admin URL discovery pipeline
- `discovery/backend_resolution.py` — admin parameter resolution helpers
- `discovery/extensions.py` — public discovery extension types and hook loading
- `discovery/frontend.py` — frontend URL discovery pipeline
- `discovery/frontend_resolution.py` — frontend routable and API URL resolution helpers
- `discovery/utils.py` — shared resolver utilities
- `templates/wagtail_unveil/` — report and dashboard templates
- `../assets_src/css/` — editable report CSS source
- `../assets_src/js/` — report JavaScript source modules
- `static/wagtail_unveil/css/` — generated report CSS assets (`admin_urls_report.css`, `admin_urls_report.min.css`)
- `static/wagtail_unveil/js/` — generated report JS bundle assets (`report.bundle.js`, `report.bundle.min.js`)
- `../docs/contributing/frontend-assets.md` — canonical contributor guide for frontend asset build/test workflow and CI expectations

Frontend asset formatting and linting for contributor-owned files is managed by Biome via `npm run lint:assets` and `npm run lint:assets:fix` (hooked into pre-commit and CI).

## Package Interfaces

`wagtail_unveil` currently exposes:

- URLconf inclusion via `wagtail_unveil.urls`
- JSON API endpoints
- HTML report and settings views
- Wagtail dashboard integration

Do not document or assume package management commands unless they are reintroduced in code.

### Settings

- `WAGTAIL_UNVEIL_PAGES_PER_TYPE`
- `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`
- `WAGTAIL_UNVEIL_API_KEY`

`get_api_key()` checks the environment first, then Django settings fallback.
JSON API requests also allow superuser session auth when `DEBUG=True` and the request is not attempting Bearer-token auth.

### URL Names

The package exports one URL namespace:

- `wagtail_unveil:api_v1_backend_urls`
- `wagtail_unveil:api_v1_frontend_urls`
- `wagtail_unveil:report_backend_urls`
- `wagtail_unveil:report_frontend_urls`
- `wagtail_unveil:report_settings`

Versioned API path segments, URL names, and `metadata.api_version` should be
driven by `wagtail_unveil.api_contract.API_VERSION_REGISTRY` and helper accessors.
The package should support explicit parallel versions (`v1`, `v2`, ...) with deprecation windows.
Additional `wagtail_unveil:api_vN_*` names may be present when newer versions are introduced.
Canonical contributor policy for deciding and implementing API versions:
`../docs/contributing/api-versioning.md`.

Do not document or reintroduce the old split `api_urls.py` / `report_urls.py` namespace layout unless the code changes back to that design.

### JSON Response Shape

JSON API endpoints preserve top-level `urls` and `count` fields and also return a `metadata` object containing:

- `api_version`
- `api_lifecycle`
- `generated_at`
- `applied_filter`
- `total_count`
- `testable_count`
- `untestable_count`
- `package_version`

`api_version` identifies the response contract version.
`api_lifecycle` identifies lifecycle status (`stable` or `deprecated`) and optional dates.
`package_version` identifies the installed package release and is not the API version.
Breaking API changes should use a new versioned path such as `/api/v2/...` and deprecate older versions before removal.

### New Version Checklist

When adding a new API version:

1. Add the contract entry to `API_VERSION_REGISTRY` with lifecycle dates/status
2. Confirm backend/frontend versioned routes and names are generated for the new version
3. Add/adjust tests for coexistence, lifecycle metadata, and deprecation headers
4. Update README/docs with lifecycle timeline and version-specific notes

For detailed rationale, breaking-change decision rules, lifecycle defaults, and
worked examples, see `../docs/contributing/api-versioning.md`.

The admin/frontend HTML reports are shell views that fetch this JSON on page load rather than rendering discovery results directly in the Django template. They stay hidden behind a full-screen loading state until the API data and client-side controls are ready, so JavaScript is required for report use.
The settings page is server-rendered and is intended for local diagnostics while `DEBUG=True`.
Frontend URL payloads may include `resolved_url` for path-parameter resolution and `query_params` for query-driven testing while preserving the canonical `url` field shown in reports.

## Discovery Notes

The full discovery flow, resolution fallbacks, special cases, and intentional limitations are documented in `../docs/contributing/discovery-architecture.md`. Keep that document as the canonical explanation of discovery internals and use the notes below as a brief orientation only.

### Admin URLs

`get_admin_urls()` follows explicit phases: discover admin candidates, normalize route metadata, classify testability, resolve supported parameterized URLs, then emit `BackendURL` objects.
Namespace-specific rules may replace an earlier instance choice or invalidate it entirely when the route requires a different model type, such as workflow usage URLs.
Admin parameter resolution is unified through `register_unveil_admin_instance_resolvers` hook registrations. Use that hook for both built-in package rules and developer-installed Wagtail package extensions rather than adding package-specific branches in core discovery.
Resolved admin routes are only marked testable when the callback supports GET; POST-only routes such as reorder views remain visible with a skip reason instead of being offered to the report tester.

### Frontend URLs

`get_frontend_urls()` combines:

- live Wagtail page URLs
- additional page-derived routes for forms and `RoutablePageMixin`
- non-admin resolver routes

Frontend discovery also follows explicit phases: discover candidates, normalize route metadata, classify testability, then emit `FrontendURL` objects. Routable sub-routes remain visible in output; supported path-parameter variants may carry a concrete `resolved_url` and become testable, while unresolved path-parameter variants stay non-testable and regex-backed variants stay non-testable for regex patterns. Supported Wagtail API detail routes may also carry a concrete `resolved_url`; query-driven `find/` routes stay visible but non-testable with `Requires query parameters`.

## Constraints

- Never import from `sandbox`
- Keep templates under `templates/wagtail_unveil/`
- Keep static assets under `static/wagtail_unveil/`
- Keep reusable logic out of ad hoc sandbox helpers

## Testing

Tests for this package live in the root `tests/` package and should be run with:

```bash
uv run --env-file .env django-admin test tests
npm run test:js
```

Use `django.test.TestCase`, and use Wagtail test helpers only where admin behavior requires them.
