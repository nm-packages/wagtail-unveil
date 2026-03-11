# API Endpoints

## Setup

Add the URLs to your project's `urls.py` (see [Installation](../getting-started/installation.md)):

```python
path("unveil/", include("wagtail_unveil.urls")),
```

Then set `WAGTAIL_UNVEIL_API_KEY` (see [Settings Reference](../configuration/settings-reference.md#wagtail_unveil_api_key)).

## Authentication

The API accepts a Bearer token matching `WAGTAIL_UNVEIL_API_KEY`:

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/
```

| Scenario | Response |
|---|---|
| Valid Bearer token | `200` with data |
| Invalid Bearer token | `403` |
| No key configured | `500` |
| Superuser session + `DEBUG=True` | `200` (session auth accepted when not attempting Bearer auth) |

## Backend URLs Endpoint

Returns all discovered Wagtail admin URLs.

```
GET /unveil/api/v1/backend-urls/
```

**Filters** (`?filter=`):

| Value | Returns |
|---|---|
| _(omitted)_ | All backend URLs |
| `static` | Only URLs without parameters |
| `parameterized` | Only URLs with parameters |

**Examples:**

```bash
# All backend URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/

# Static URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/v1/backend-urls/?filter=static"

# Parameterized URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/v1/backend-urls/?filter=parameterized"
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
    "api_version": "v1",
    "api_lifecycle": {
      "status": "stable",
      "deprecated_on": null,
      "sunset_on": null
    },
    "generated_at": "2026-03-02T12:34:56+00:00",
    "applied_filter": null,
    "total_count": 190,
    "testable_count": 150,
    "untestable_count": 40,
    "package_version": "0.2.0"
  }
}
```

## Frontend URLs Endpoint

Returns all discovered frontend URLs (Wagtail pages and resolver routes).

```
GET /unveil/api/v1/frontend-urls/
```

**Filters** (`?filter=`):

| Value | Returns |
|---|---|
| _(omitted)_ | All frontend URLs |
| `pages` | Only Wagtail page URLs |
| `resolver` | Only Django resolver URLs |

**Examples:**

```bash
# All frontend URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/frontend-urls/

# Page URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/v1/frontend-urls/?filter=pages"

# Resolver URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil/api/v1/frontend-urls/?filter=resolver"
```

## Metadata

Both endpoints include a `metadata` object alongside the top-level `urls` and `count` fields:

| Field | Description |
|---|---|
| `api_version` | Response contract version (`v1`, `v2`, ...) |
| `api_lifecycle` | Lifecycle status (`stable` or `deprecated`) with optional `deprecated_on` / `sunset_on` dates |
| `generated_at` | ISO 8601 timestamp for when the response was generated |
| `applied_filter` | The recognised filter value that was applied, or `null` |
| `total_count` | Total URLs in the response |
| `testable_count` | Number of URLs marked testable |
| `untestable_count` | Number of URLs marked untestable |
| `package_version` | Installed `wagtail-unveil` package version (not the API version) |

## Deprecation Headers

Deprecated API versions return additional response headers:

- `Deprecation: true`
- `Sunset: <RFC 1123 datetime>` when a sunset date is configured for that version

## API Versioning

Versioned endpoints are explicit and can run in parallel (for example `v1` and `v2`). The built-in HTML reports always call the latest stable version.

For the full lifecycle policy, breaking-change criteria, and version bump workflow, see [contributing/api-versioning.md](../contributing/api-versioning.md).

## Related

- [Configuration](../configuration/settings-reference.md) — API key and discovery settings
- [Features](../features/index.md) — HTML report counterparts
- [API Reference Index](index.md) — Back to section overview
