# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## sandbox — Example Wagtail Site

This is a standard Wagtail project used for developing and testing the `wagtail_unveil` package. It represents a typical site that has the package installed.

### Structure

- `settings/base.py` — Shared settings; `wagtail_unveil` is included in INSTALLED_APPS
- `settings/dev.py` — Development overrides (DEBUG=True, SQLite)
- `settings/production.py` — Production settings template
- `home/` — Default Wagtail home app with a blank `HomePage` model
- `search/` — Wagtail search view
- `urls.py` — URL config: Django admin at `/django-admin/`, Wagtail admin at `/admin/`, unveil API at `/unveil-api/`, Wagtail pages at `/`
- `templates/` — Site-level templates
- `static/` — Site-level static files

### Notes

- Default settings module: `sandbox.settings.dev` (set in `manage.py`)
- Add example pages, routes, and content here to exercise the `wagtail_unveil` URL discovery features
