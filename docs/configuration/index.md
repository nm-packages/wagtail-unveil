# Configuration

wagtail-unveil is configured via Django settings or environment variables.

## In This Section

- [Settings Reference](settings-reference.md) — All `WAGTAIL_UNVEIL_*` settings with defaults and examples

## Quick Reference

| Setting | Default | Purpose |
|---|---|---|
| `WAGTAIL_UNVEIL_API_KEY` | — | Bearer token for JSON API authentication |
| `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS` | `False` | Explicit opt-in for superuser HTML report access when `DEBUG=False` |
| `WAGTAIL_UNVEIL_PAGES_PER_TYPE` | `1` | Max page instances per type in frontend discovery |
| `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES` | `[]` | URL prefixes to exclude from discovery |

## Related

- [Getting Started](../getting-started/installation.md) — Set up the API key
- [Features](../features/index.md) — See how configuration affects reports
- [API Reference](../api/endpoints.md) — API authentication details
- [Documentation Index](../index.md) — Back to overview
