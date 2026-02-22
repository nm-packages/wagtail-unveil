# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## wagtail_unveil — The Reusable Package

This is the distributable Wagtail package. Code here must not depend on the sandbox app — it should work when installed into any Wagtail project.

### Purpose

Discover all URLs in a Wagtail site (hardcoded routes, Wagtail page URLs, admin URLs) and present them in admin listing pages. Developers can then test these URLs to verify they return expected response codes (primarily 200 OK).

### Key Files

- `apps.py` — Django app config (`WagtailUnveilConfig`)
- `models.py` — Package models
- `urls.py` — URL discovery logic (`get_admin_urls()` returns list of `AdminURL` dataclasses); `_resolve_parameterised_url()` generically resolves parameterised admin URLs (snippets, redirects, images, documents, users, groups) by extracting the model from view callbacks and using real DB instances, populating `AdminURL.resolved_route`
- `views.py` — Views (`admin_urls_json` — JSON endpoint; `admin_urls_report` — HTML report page, requires superuser + DEBUG=True)
- `api_urls.py` — API URL configuration (`app_name = "wagtail_unveil_api"`)
- `report_urls.py` — Report URL configuration (`app_name = "wagtail_unveil_report"`)
- `templates/wagtail_unveil/admin_urls_report.html` — HTML report template
- `static/wagtail_unveil/css/admin_urls_report.css` — Report page styles
- `static/wagtail_unveil/js/admin_urls_report.js` — Report page JavaScript (filtering, test buttons, move-failed-to-top)
- `wagtail_hooks.py` — Wagtail hooks (dashboard panel linking to the HTML report, superuser + DEBUG only)
- `admin.py` — Wagtail admin integration
- `tests.py` — Package tests (run with `uv run python manage.py test wagtail_unveil`)
- `management/commands/show_admin_urls.py` — Management command to list admin URLs

### Conventions

- This app is registered as `"wagtail_unveil"` in INSTALLED_APPS
- Migrations live in `migrations/` and are created via `uv run python manage.py makemigrations wagtail_unveil`
- API endpoints are authenticated via `WAGTAIL_UNVEIL_API_KEY` environment variable (Bearer token)
- API URL config is in `api_urls.py` — consuming projects include it in their own `urls.py`
- Report URL config is in `report_urls.py` — HTML report requires superuser login and `DEBUG=True`
