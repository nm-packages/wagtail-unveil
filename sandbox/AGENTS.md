# AGENTS.md

This file contains sandbox-specific guidance for the example Wagtail project.

## Purpose

`sandbox/` is a development and testing site for `wagtail_unveil`. It exists to exercise the package against a realistic Wagtail installation.

## Structure

- `settings.py` — sandbox settings
- `urls.py` — project URL config
- `home/` — home app and management commands such as `create_sample_data`
- `core/` — general page types and Wagtail settings models
- `search/` — search view
- `taxonomy/` — snippets and modeladmin examples
- `calendar/` — custom Wagtail admin viewsets
- `forms/` — form builder pages
- `inventory/` — `ModelViewSet`, grouped admin views, chooser views
- `events/` — routable page examples

## URL Layout

The sandbox mounts:

- Django admin at `/django-admin/`
- Wagtail admin at `/admin/`
- documents at `/documents/`
- images at `/images/`
- search at `/search/`
- `wagtail_unveil` at `/unveil/`
- Wagtail page serving at `/`

## Sample Data

`create_sample_data` creates representative objects used by URL discovery tests, including pages, images, documents, redirects, snippets, settings, chooser-backed models, form pages, and routable event pages.

Use sandbox apps to exercise package behavior. Do not move reusable package logic into the sandbox.
