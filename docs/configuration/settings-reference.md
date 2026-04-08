# Settings Reference

All `WAGTAIL_UNVEIL_*` settings can be set as environment variables or in Django settings. Environment variables generally take precedence when both are set, subject to each setting's normalization rules.

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
- When `DEBUG=False`, session-based JSON access remains bearer-token-only unless a request carries a valid signed report access token issued from the built-in report UI

## `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS`

Explicitly allows superusers to open the backend report, frontend report, settings page, and dashboard links when `DEBUG=False`.

```bash
export WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=true
```

```python
WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS = True
```

**Notes:**

- Defaults to `False`
- Non-blank environment variables take precedence over Django settings
- Blank environment values are ignored and fall back to the Django setting or default
- Intended as an explicit production opt-in for HTML report access
- Does not make the JSON API broadly session-authenticated in production
- The report UI uses a short-lived signed token for its own JSON requests; the API key is still never exposed to the browser

## `WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE`

The dependency manifest used by `/unveil/api/v1/platform/` to report declared Python dependencies and their installed versions.

```bash
export WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=pyproject.toml
export WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE=requirements/base.txt
```

```python
WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE = "pyproject.toml"
```

**Notes:**

- If both are set, the environment variable is used
- Blank or non-string values are treated as unset
- Relative paths are resolved from Django `BASE_DIR` and must stay within that directory
- Absolute paths are used directly
- Supported formats in v1 are `pyproject.toml` and requirements-style text files
- If the setting is unset, unreadable, missing, or unsupported, the platform endpoint still returns runtime data and adds a warning instead of failing the whole response

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
- [API Endpoints](../api/endpoints.md) — Platform runtime and URL discovery API payloads
- [Frontend URLs Report](../features/frontend-urls-report.md) — How page limits affect the report
- [Settings Page](../features/settings-page.md) — View effective values at runtime
- [Configuration Index](index.md) — Back to section overview
