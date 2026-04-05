# Settings Reference

All `WAGTAIL_UNVEIL_*` settings can be set as environment variables or in Django settings. Environment variables take precedence when both are set.

## `WAGTAIL_UNVEIL_API_KEY`

The Bearer token used to authenticate JSON API requests.

```bash
# Environment variable (recommended)
export WAGTAIL_UNVEIL_API_KEY=your-secret-key
```

```python
# Django settings
WAGTAIL_UNVEIL_API_KEY = "your-secret-key"
```

**Notes:**

- If both are set, the environment variable is used
- Requests with an invalid key receive a `403` response
- If no key is configured, Bearer-authenticated requests return `500`
- When `DEBUG=True`, the HTML reports also accept superuser session auth (no Bearer token needed for report use)

## `WAGTAIL_UNVEIL_PAGES_PER_TYPE`

Controls how many page instances per page type are included in frontend URL discovery.

```bash
export WAGTAIL_UNVEIL_PAGES_PER_TYPE=3
export WAGTAIL_UNVEIL_PAGES_PER_TYPE=0
```

```python
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 1   # default: one page per type
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 3   # include up to 3 pages per type
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 0   # no limit
```

**Notes:**

- Defaults to `1` when omitted
- Invalid or negative values fall back to `1`
- Use `0` explicitly for no limit
- Environment variables are parsed as numeric strings
- Applies to page-derived URLs only; resolver-derived URLs are not affected

## `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

Excludes URL path prefixes from both frontend and admin URL discovery.

```bash
export WAGTAIL_UNVEIL_SKIP_URL_PREFIXES=__debug__/,/silk/
export WAGTAIL_UNVEIL_SKIP_URL_PREFIXES="  /search/ , admin/images/ "
```

```python
WAGTAIL_UNVEIL_SKIP_URL_PREFIXES = ["__debug__/", "/silk/"]
```

**Notes:**

- Defaults to `[]` (no exclusions)
- Environment variables use a comma-separated string
- Whitespace around comma-separated env values is ignored
- Leading slashes are normalized: `"/__debug__/"` and `"__debug__/"` are equivalent
- Applies to frontend page URLs, frontend resolver URLs, and admin URLs
- Invalid values are silently ignored

## Related

- [Getting Started](../getting-started/installation.md) — Initial setup and API key configuration
- [Frontend URLs Report](../features/frontend-urls-report.md) — How page limits affect the report
- [Settings Page](../features/settings-page.md) — View effective values at runtime
- [Configuration Index](index.md) — Back to section overview
