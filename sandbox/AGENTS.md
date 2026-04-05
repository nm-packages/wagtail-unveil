# AGENTS.md

This file contains sandbox-specific guidance for the local Wagtail integration project used during contributor development and testing.

## Purpose

`sandbox/` is the local integration environment for `wagtail_unveil`. It exists to exercise the package against a realistic Wagtail installation during feature development, debugging, and fixture-backed verification.

Sandbox-only helpers, including management commands such as `create_sample_data`, are fixture and developer tooling for this project. They are not part of the distributable `wagtail_unveil` package interface.

## Structure

- `settings.py` — sandbox settings
- `urls.py` — project URL config
- `home/` — home app and management commands such as `create_sample_data`
- `core/` — general page types and Wagtail settings models
- `search/` — search view
- `taxonomy/` — snippets, modeladmin examples, and the sample `wagtail_unveil` discovery extension hook
- `calendar/` — custom Wagtail admin viewsets
- `forms/` — form builder pages
- `inventory/` — `ModelViewSet`, grouped admin views, chooser views
- `events/` — routable page examples

## URL Layout

The sandbox mounts:

- Django admin at `/django-admin/`
- Wagtail admin at `/admin/`
- Wagtail API v2 at `/api/v2/`
- documents at `/documents/`
- images at `/images/`
- search at `/search/`
- `wagtail_unveil` at `/unveil/`
- Wagtail page serving at `/`

## Sample Data

`create_sample_data` creates representative objects used by URL discovery tests, including pages, images, documents, redirects, snippets, settings, chooser-backed models, form pages, and routable event pages.

Use sandbox apps, sample data, and local-only routes to exercise package behavior and reproduce issues in a live Wagtail site. Do not move reusable package logic into the sandbox.
