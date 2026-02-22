# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## sandbox — Example Wagtail Site

This is a standard Wagtail project used for developing and testing the `wagtail_unveil` package. It represents a typical site that has the package installed.

### Structure

- `settings/base.py` — Shared settings; `wagtail_unveil` is included in INSTALLED_APPS
- `settings/dev.py` — Development overrides (DEBUG=True, SQLite)
- `settings/production.py` — Production settings template
- `home/` — Default Wagtail home app with a blank `HomePage` model; also hosts management commands (e.g. `create_sample_data`)
- `core/` — `ListingPage` and `StandardPage` models providing a realistic page hierarchy (`HomePage > ListingPage > StandardPage`)
- `search/` — Wagtail search view
- `taxonomy/` — Snippet models (`Category` via `@register_snippet` decorator, `Colour` via `SnippetViewSet`) and a `Person` model registered via `wagtail-modeladmin` (`PersonModelAdmin`) to exercise parameterised admin URL discovery
- `urls.py` — URL config: Django admin at `/django-admin/`, Wagtail admin at `/admin/`, unveil API at `/unveil-api/`, unveil report at `/unveil-report/`, Wagtail pages at `/`
- `templates/` — Site-level templates
- `static/` — Site-level static files

### Management Commands

- `create_sample_data` — Creates sample instances of Images, Documents, Redirects, Search Promotions, an Editor user, child Pages, Collections, and People. Idempotent by default; use `--clear` to remove and recreate all sample data. Sample data is identified by the `[Sample]` title/name prefix.

### Notes

- Default settings module: `sandbox.settings.dev` (set in `manage.py`)
- Add example pages, routes, and content here to exercise the `wagtail_unveil` URL discovery features
