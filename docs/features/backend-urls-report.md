# Backend URLs Report

The backend URLs report discovers and displays all Wagtail admin URLs registered in your project.

## Access

Visit `/unveil/report/backend-urls/` while logged in as a superuser with `DEBUG=True`, or enable `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS` for explicit production access.

![Backend URLs Report](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/backend_report.jpg)

You can also reach it from the Wagtail admin dashboard panel.

## Features

- **Full admin URL discovery** — automatically discovers all admin URLs including custom admin views registered via `register_admin_viewset` or `register_admin_urls` hooks
- **Testable/untestable summary** — shows counts of testable and untestable URLs at a glance
- **One-click URL testing** — test static URLs with colour-coded status codes (green=2xx, yellow=3xx, red=4xx/5xx)
- **Parameterised URL resolution** — admin URLs with parameters (snippets, redirects, images, documents, users, groups) are automatically resolved using real database instances, making them testable via the report
- **Per-page-type page routes** — safe `wagtailadmin_pages` routes such as edit, delete, copy, move, privacy, and revisions are listed once per concrete page type present in the database
- **Test All** button — runs all testable (static and resolved) URLs sequentially with a progress indicator and pass/fail summary
- **Hide Untestable toggle** — hides non-testable rows (parameterised, POST-only, regex) to focus on testable URLs; preference is saved in a cookie across sessions
- **Self-contained** — no external CSS or JS dependencies

## Untestable URLs

Some admin URLs cannot be tested directly:

- POST-only views (logout, block preview, etc.)
- URLs requiring query parameters
- Parameterised URLs where no database instance could be resolved
- Routes with unconvertible regex patterns

These remain visible in the report with a reason. Use the Hide Untestable toggle to focus on testable URLs.

## Related

- [Frontend URLs Report](frontend-urls-report.md) — Test frontend page and resolver URLs
- [Settings Page](settings-page.md) — View resolved URL paths and diagnostics
- [Configuration](../configuration/settings-reference.md) — Exclude URL prefixes from discovery
- [API Reference](../api/endpoints.md) — Query backend URLs via the JSON API
- [Features Index](index.md) — Back to section overview
