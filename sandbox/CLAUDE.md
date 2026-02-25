# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## sandbox — Example Wagtail Site

This is a standard Wagtail project used for developing and testing the `wagtail_unveil` package. It represents a typical site that has the package installed.

### Structure

- `settings.py` — All settings; `wagtail_unveil` is included in INSTALLED_APPS
- `home/` — Default Wagtail home app with a blank `HomePage` model; also hosts management commands (e.g. `create_sample_data`)
- `core/` — `ListingPage` and `StandardPage` models providing a realistic page hierarchy (`HomePage > ListingPage > StandardPage`). Also includes `SocialMediaSettings` (`BaseSiteSetting`) and `BrandingSettings` (`BaseGenericSetting`) registered via `@register_setting` to exercise `wagtailsettings` admin URL discovery
- `search/` — Wagtail search view
- `taxonomy/` — Snippet models (`Category` via `@register_snippet` decorator, `Colour` via `SnippetViewSet`) and a `Person` model registered via `wagtail-modeladmin` (`PersonModelAdmin`) to exercise parameterised admin URL discovery
- `calendar/` — Custom admin views using the Wagtail 7.0 `ViewSet` pattern (`register_admin_viewset` hook). Provides year and month calendar views at `admin/calendar/` and `admin/calendar/month/` to exercise custom admin URL discovery
- `forms/` — Form builder page using `AbstractEmailForm` and `AbstractFormField` from `wagtail.contrib.forms`. Provides a `FormPage` with configurable form fields, discovered automatically via the page tree
- `inventory/` — Generic views using `ModelViewSet`, `ModelViewSetGroup`, and `ChooserViewSet`. Products and Suppliers are grouped under an "Inventory" menu via `InventoryViewSetGroup`. A `ProductChooserViewSet` provides a chooser modal. Exercises full CRUD URL discovery including inspect, copy, and export routes
- `events/` — `EventIndexPage` using `RoutablePageMixin` with `@path()` sub-routes (`past/`, `year/<int:year>/`) that filter child `EventPage` instances by date. Exercises routable page sub-URL discovery — static sub-routes are testable, parameterized sub-routes are marked non-testable
- `urls.py` — URL config: Django admin at `/django-admin/`, Wagtail admin at `/admin/`, documents serve URL at `/documents/`, images serve URL at `/images/`, unveil API at `/unveil-api/`, unveil report at `/unveil-report/`, Wagtail pages at `/`
- `templates/` — Site-level templates
- `static/` — Site-level static files

### Management Commands

- `create_sample_data` — Creates sample instances of Images, Documents, Redirects, Search Promotions, an Editor user, child Pages, Collections, People, Categories, Colours, Suppliers, Products, Form Pages, Event Pages (routable), and Settings (SocialMediaSettings, BrandingSettings). Idempotent by default; use `--clear` to remove and recreate all sample data. Sample data is identified by the `[Sample]` title/name prefix.

### Notes

- Default settings module: `sandbox.settings` (set in `.env` via `DJANGO_SETTINGS_MODULE`)
- Add example pages, routes, and content here to exercise the `wagtail_unveil` URL discovery features
