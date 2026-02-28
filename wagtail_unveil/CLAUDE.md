# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## wagtail_unveil — The Reusable Package

This is the distributable Wagtail package. Code here must not depend on the sandbox app — it should work when installed into any Wagtail project.

### Purpose

Discover all URLs in a Wagtail site (hardcoded routes, Wagtail page URLs, admin URLs) and present them in admin listing pages. Developers can then test these URLs to verify they return expected response codes (primarily 200 OK).

### Key Files

- `apps.py` — Django app config (`WagtailUnveilConfig`)
- `models.py` — Package models
- `settings.py` — Settings helpers; `get_pages_per_type()` reads `WAGTAIL_UNVEIL_PAGES_PER_TYPE` (default `1` page per type when omitted; positive int = limit per page type; `0` = no limit; invalid/negative values fall back to `1`); `get_skip_url_prefixes()` reads `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES` (default `[]`; list of URL path prefixes to exclude from discovery; leading slashes stripped); `get_api_key()` reads `WAGTAIL_UNVEIL_API_KEY` from env var first then Django setting fallback, returns `''` if absent, non-string, or empty — used by both JSON view endpoints for Bearer token auth
- `urls.py` — URL discovery logic:
  - `get_admin_urls()` returns list of `AdminURL` dataclasses; `_resolve_parameterised_url()` generically resolves parameterised admin URLs (snippets, redirects, images, documents, users, groups, modeladmin, wagtailforms) by extracting the model from view callbacks and using real DB instances, populating `AdminURL.resolved_route`. For `wagtailforms` namespace URLs (form submissions), falls back to `_get_form_page_instance()` which finds a live `FormMixin` page since the plain-function views don't expose a model attribute. `wagtailsettings` namespace URLs (`admin/settings/...`) are resolved via `_resolve_settings_url()` which iterates registered setting models from `wagtail.contrib.settings.registry` and reverses with kwargs (app_name, model_name, pk)
  - `_clean_regex_route()` strips regex anchors (`^`, `$`) and converts named groups (`(?P<name>...)`) to path-style `<name>` — applied to all routes so `re_path()` patterns (e.g. from wagtail-modeladmin) are handled correctly
  - `_get_model_from_name()` parses modeladmin-style URL names (`{app}_{model}_modeladmin_{action}`) to extract the model class — used as a fallback when the view callback doesn't expose a model directly
  - `get_frontend_urls()` returns list of `FrontendURL` dataclasses; combines page URLs (`_get_page_urls()` via `Page.objects.live().specific()`) and resolver URLs (`_get_resolver_frontend_urls()` — non-admin routes from Django's URL resolver)
  - `_get_page_urls()` respects `WAGTAIL_UNVEIL_PAGES_PER_TYPE` — when set to a positive int, groups page URLs by page and takes up to N pages per type (preserving all URL entries for each selected page). Form pages (`FormMixin` subclasses) also emit a second non-testable entry with `name="landing_page"` for the POST landing page (guarded with try/except so `wagtail.contrib.forms` is optional). `RoutablePageMixin` pages emit additional entries for each `@path()` sub-route — static sub-routes are testable, parameterized sub-routes are marked non-testable
  - `_get_routable_sub_urls()` inspects a `RoutablePageMixin` page class's `get_subpage_urls()` to find `@path()` decorated routes, skips the index route (empty pattern), and builds `FrontendURL` entries for each sub-route
- `views.py` — Views:
  - `admin_urls_json` / `admin_urls_report` — Admin URL endpoints
  - `frontend_urls_json` / `frontend_urls_report` — Frontend URL endpoints
  - All report views require superuser + DEBUG=True; JSON views require API key
- `api_urls.py` — API URL configuration (`app_name = "wagtail_unveil_api"`): `admin-urls/` and `frontend-urls/`
- `report_urls.py` — Report URL configuration (`app_name = "wagtail_unveil_report"`): `admin-urls/` and `frontend-urls/`
- `templates/wagtail_unveil/base_report.html` — Shared parent template extended by both report templates; provides common HTML structure, nav bar, filter controls, and CSS/JS loading
- `templates/wagtail_unveil/admin_urls_report.html` — Admin URLs HTML report template
- `templates/wagtail_unveil/frontend_urls_report.html` — Frontend URLs HTML report template
- `templates/wagtail_unveil/dashboard_panel.html` — Wagtail admin homepage panel template used by `UnveilReportPanel` in `wagtail_hooks.py`
- `static/wagtail_unveil/css/admin_urls_report.css` — Shared report page styles
- `static/wagtail_unveil/js/admin_urls_report.js` — Shared report page JavaScript (search, sort, test buttons, move-failed-to-top, hide/show untestable toggle with cookie persistence)
- `wagtail_hooks.py` — Wagtail hooks (dashboard panel linking to both reports, superuser + DEBUG only)
- `admin.py` — Wagtail admin integration
- Tests live in the root-level `tests/` package (run with `uv run --env-file .env django-admin test tests`)
- `management/commands/show_admin_urls.py` — Management command to list admin URLs
- `management/commands/show_frontend_urls.py` — Management command to list frontend URLs (`--pages` / `--resolver` filters)

### Conventions

- This app is registered as `"wagtail_unveil"` in INSTALLED_APPS
- Migrations live in `migrations/` and are created via `uv run --env-file .env django-admin makemigrations wagtail_unveil`
- API endpoints are authenticated via `WAGTAIL_UNVEIL_API_KEY` environment variable (Bearer token)
- API URL config is in `api_urls.py` — consuming projects include it in their own `urls.py`
- Report URL config is in `report_urls.py` — HTML report requires superuser login and `DEBUG=True`
