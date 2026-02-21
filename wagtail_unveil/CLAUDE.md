# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## wagtail_unveil — The Reusable Package

This is the distributable Wagtail package. Code here must not depend on the sandbox app — it should work when installed into any Wagtail project.

### Purpose

Discover all URLs in a Wagtail site (hardcoded routes, Wagtail page URLs, admin URLs) and present them in admin listing pages. Developers can then test these URLs to verify they return expected response codes (primarily 200 OK).

### Key Files

- `apps.py` — Django app config (`WagtailUnveilConfig`)
- `models.py` — Package models
- `views.py` — Package views
- `admin.py` — Wagtail admin integration
- `tests.py` — Package tests (run with `uv run python manage.py test wagtail_unveil`)

### Conventions

- This app is registered as `"wagtail_unveil"` in INSTALLED_APPS
- Migrations live in `migrations/` and are created via `uv run python manage.py makemigrations wagtail_unveil`
