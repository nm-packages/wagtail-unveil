# Frontend URLs Report

The frontend URLs report discovers and displays all frontend URLs in your project — from live Wagtail pages and from the Django URL resolver.

## Access

Visit `/unveil/report/frontend-urls/` while logged in as a superuser with `DEBUG=True`.

![Frontend URLs Report](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/frontend_report.jpg)

You can also reach it from the Wagtail admin dashboard panel.

## Features

- **Two URL sources** — Wagtail page URLs (from `Page.objects.live().specific()`) and Django resolver URLs (non-admin routes)
- **RoutablePageMixin support** — automatically discovers `@path()` and regex `@route()` sub-routes on routable pages; static sub-routes are testable, supported single-parameter path sub-routes use inferred concrete URLs for testing, and regex literal patterns remain visible but non-testable
- **Resolver detail-route testing** — supported resolver detail routes such as Wagtail API object endpoints stay visible with their canonical parameterised path while the Test/Open actions use inferred concrete URLs
- **Configurable page limit** — control how many page instances per type are included via [`WAGTAIL_UNVEIL_PAGES_PER_TYPE`](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/configuration/settings-reference.md#wagtail_unveil_pages_per_type)
- **One-click URL testing** — colour-coded status codes (green=2xx, yellow=3xx, red=4xx/5xx)
- **Test All** button — runs all testable URLs sequentially with a progress indicator and pass/fail summary
- **Hide Untestable toggle** — hides non-testable rows; preference saved in a cookie across sessions
- **Searchable and sortable columns** — sort by URL, Source, Page Type, Title, or Name
- **Self-contained** — no external CSS or JS dependencies

## URL Sources

### Wagtail Page URLs

Discovered from `Page.objects.live().specific()`. Includes:

- Base page URL for each live page
- Form landing page URLs for pages using `FormMixin`
- Sub-route URLs for pages using `RoutablePageMixin`

### Django Resolver URLs

Discovered by walking the root URL resolver. Excludes:

- Routes under `admin/`
- Routes in the `wagtail_unveil` namespace
- Any prefixes configured in `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

## Untestable URLs

Some frontend URLs cannot be tested directly:

- Parameterised routes (e.g. `<slug:slug>`)
- Routes with regex patterns, including regex-based `RoutablePageMixin` sub-routes
- Pages belonging to non-default Wagtail sites
- Form landing pages (POST-only)
- Query-driven routes such as Wagtail API `find/` endpoints

When a routable page path parameter can be resolved safely, the row stays visible with its canonical pattern while the Test/Open actions use the inferred concrete URL. Supported Wagtail API detail routes behave similarly. Query-driven Wagtail API `find/` routes remain visible for inspection but are not treated as directly testable report targets. URLs that still cannot be resolved remain visible in the report with a reason.

## Related

- [Backend URLs Report](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/backend-urls-report.md) — Test Wagtail admin URLs
- [Configuration](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/configuration/settings-reference.md) — Control page limits and URL exclusions
- [API Reference](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/api/endpoints.md) — Query frontend URLs via the JSON API
- [Features Index](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/index.md) — Back to section overview
