# Features

wagtail-unveil exposes URL discovery through interactive HTML reports in the Wagtail admin, a settings diagnostic page, a dashboard panel, and a JSON API.

## In This Section

- [Backend URLs Report](backend-urls-report.md) — Discover and test all Wagtail admin URLs
- [Frontend URLs Report](frontend-urls-report.md) — Discover and test all frontend page and resolver URLs
- [Settings Page](settings-page.md) — View effective configuration and runtime diagnostics
- [Dashboard Panel](dashboard-panel.md) — Quick-access links on the Wagtail admin home page

## Access Requirements

HTML reports and the dashboard panel require:

- Superuser login
- `DEBUG=True`, or `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True`

## Related

- [Getting Started](../getting-started/installation.md) — Add URLs and access reports for the first time
- [Configuration](../configuration/settings-reference.md) — Control page limits and URL exclusions
- [API Reference](../api/index.md) — Query discovery results programmatically
- [Documentation Index](../index.md) — Back to overview
