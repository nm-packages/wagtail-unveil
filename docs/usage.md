# Usage Reference

Detailed reference documentation for wagtail-unveil. For a quick overview, see the [README](../README.md).

## JSON API

### Setup

1. Add the URLs to your project's `urls.py`:

```python
urlpatterns = [
    # ... your other URLs ...
    path("unveil/", include("wagtail_unveil.urls")),
]
```

2. Set `WAGTAIL_UNVEIL_API_KEY` (environment variable recommended):

```bash
export WAGTAIL_UNVEIL_API_KEY=your-secret-key
```

   Alternatively, set it in Django settings:

```python
WAGTAIL_UNVEIL_API_KEY = "your-secret-key"
```

   If both are set, the environment variable takes precedence.

### Configuration Notes

`WAGTAIL_UNVEIL_PAGES_PER_TYPE` defaults to `1` when omitted.
Values are normalized to a non-negative integer. Invalid or negative values default to `1`.
Use `0` explicitly for no limit.

`WAGTAIL_UNVEIL_SKIP_URL_PREFIXES` defaults to `[]` (no exclusions) when omitted.
Applies to both frontend resolver and admin URL discovery. Leading slashes are stripped,
so `"/__debug__/"` and `"__debug__/"` are equivalent. Invalid values are silently ignored.

### Admin URLs API

```bash
# All admin URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/backend-urls/

# Static URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/backend-urls/?filter=static"

# Parameterized URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/backend-urls/?filter=parameterized"
```

**Response:**

```json
{
  "urls": [
    {
      "route": "admin/",
      "name": "wagtailadmin_home",
      "namespace": "wagtailadmin",
      "has_parameters": false,
      "view_name": "wagtail.admin.views.home.HomeView"
    }
  ],
  "count": 190,
  "metadata": {
    "generated_at": "2026-03-02T12:34:56+00:00",
    "applied_filter": null,
    "total_count": 190,
    "testable_count": 150,
    "untestable_count": 40,
    "package_version": "0.1.0"
  }
}
```

### Frontend URLs API

```bash
# All frontend URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/frontend-urls/

# Page URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/frontend-urls/?filter=pages"

# Resolver URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/frontend-urls/?filter=resolver"
```

### Authentication

The API accepts a Bearer token matching `WAGTAIL_UNVEIL_API_KEY` (from environment or Django settings).
If both are set, environment is used. Requests with an invalid key receive a `403` response.
If no key is configured in either place, Bearer-authenticated requests return `500`.

When `DEBUG=True`, the built-in HTML reports fetch the same endpoints using the current logged-in superuser session.
That session-based access is accepted when the request is not attempting Bearer-token auth.

### Metadata

Both JSON endpoints include a `metadata` object alongside the existing top-level `urls` and `count` fields.

- `generated_at` — ISO 8601 timestamp for when the response was generated
- `applied_filter` — the recognised `filter` value that was applied, or `null`
- `total_count` — total URLs returned in the response
- `testable_count` — number of URLs marked testable
- `untestable_count` — number of URLs marked untestable
- `package_version` — installed `wagtail-unveil` package version

## HTML Reports

### Setup

The report URLs are included automatically when you add `wagtail_unveil.urls` (see JSON API → Setup above).

Reports require **superuser login** and **`DEBUG=True`**.
The HTML page then fetches its data from the matching JSON endpoint using the current session.
JavaScript is required, and the report stays behind a full-screen loading state until the data and UI controls are ready.

### Admin URLs Report

Visit `/unveil/report/backend-urls/` while logged into the Wagtail admin.

**Features:**

- Automatically discovers all admin URLs including custom admin views registered via `register_admin_viewset` or `register_admin_urls` hooks
- Shows all discovered URLs with testable/untestable counts in the summary
- One-click testing of static URLs with colour-coded status codes (green=2xx, yellow=3xx, red=4xx/5xx)
- **Parameterised URL resolution** — admin URLs with parameters (snippets, redirects, images, documents, users, groups) are automatically resolved using real database instances, making them testable via the report
- **Test All** button — runs all testable (static and resolved) URLs sequentially with a progress indicator and pass/fail summary
- **Hide Untestable** toggle — hides non-testable rows (parameterized, POST-only, regex) to focus on testable URLs; preference is saved in a cookie across sessions
- Self-contained — no external CSS or JS dependencies

### Frontend URLs Report

Visit `/unveil/report/frontend-urls/` while logged into the Wagtail admin.

**Features:**

- **Two URL sources:** Wagtail page URLs (from `Page.objects.live().specific()`) and Django resolver URLs (non-admin routes)
- **RoutablePageMixin support** — automatically discovers `@path()` sub-routes on routable pages (static sub-routes are testable, parameterized sub-routes are marked non-testable)
- **Configurable page limit** — limit how many page instances per type are tested (see [Configuration](../README.md#configuration))
- One-click testing with colour-coded status codes
- **Test All** button with progress indicator and pass/fail summary
- **Hide Untestable** toggle — hides non-testable rows; preference saved in a cookie
- Searchable and sortable columns (URL, Source, Page Type, Title, Name)
- Self-contained — no external CSS or JS dependencies

## Dashboard Widget

A panel on the Wagtail admin home page links directly to both reports. Only visible to superusers when `DEBUG=True`.
