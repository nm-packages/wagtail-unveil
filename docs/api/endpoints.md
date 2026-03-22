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
      "view_name": "wagtail.admin.views.home.HomeView",
      "is_testable": true,
      "skip_reason": "",
      "resolved_route": ""
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
    "package_version": "0.1.0a2"
  }
}
```

**Item fields:**

| Field | Description |
|---|---|
| `route` | The discovered admin route as registered in Django/Wagtail |
| `name` | The route name |
| `namespace` | The Django namespace for the route |
| `has_parameters` | Whether the discovered route contains path parameters |
| `view_name` | The dotted Python view path when available |
| `is_testable` | Whether the route can be directly tested with a GET request |
| `skip_reason` | Empty string for testable routes, otherwise the reason the route is not directly testable |
| `resolved_route` | A concrete resolved admin path when parameter resolution succeeded, otherwise an empty string |

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

**Response:**

```json
{
  "urls": [
    {
      "url": "/contact/",
      "source": "page",
      "page_type": "forms.FormPage",
      "page_title": "Contact",
      "name": "",
      "resolved_url": "",
      "query_params": {},
      "is_testable": false,
      "skip_reason": "Requires POST submission"
    }
  ],
  "count": 42,
  "metadata": {
    "api_version": "v1",
    "api_lifecycle": {
      "status": "stable",
      "deprecated_on": null,
      "sunset_on": null
    },
    "generated_at": "2026-03-02T12:34:56+00:00",
    "applied_filter": "pages",
    "total_count": 42,
    "testable_count": 31,
    "untestable_count": 11,
    "package_version": "0.1.0a2"
  }
}
```

**Item fields:**

| Field | Description |
|---|---|
| `url` | The discovered frontend path |
| `source` | `page` for Wagtail page-derived URLs or `resolver` for Django resolver URLs |
| `page_type` | The `app_label.ModelName` for page-derived URLs, otherwise an empty string |
| `page_title` | The Wagtail page title for page-derived URLs, otherwise an empty string |
| `name` | The Django route name when available, otherwise an empty string |
| `resolved_url` | A concrete frontend path used for testing when parameter resolution succeeded, otherwise an empty string |
| `query_params` | An object of representative query parameters used for testing query-driven routes when safe values can be inferred, otherwise an empty object |
| `is_testable` | Whether the URL can be directly tested with a GET request |
| `skip_reason` | Empty string for testable URLs, otherwise the reason the URL is not directly testable |

## Metadata

Both endpoints include a `metadata` object alongside the top-level `urls` and `count` fields:

| Field | Description |
|---|---|
| `api_version` | Response contract version (`v1`, `v2`, ...) |
| `api_lifecycle` | Lifecycle status (`stable` or `deprecated`) with optional `deprecated_on` / `sunset_on` dates |
| `generated_at` | ISO 8601 timestamp for when the response was generated |
| `applied_filter` | The recognised filter value that was applied, or `null` |
| `total_count` | Total URLs in the response after filtering; this matches the top-level `count` field |
| `testable_count` | Number of URLs marked testable |
| `untestable_count` | Number of URLs marked untestable |
| `package_version` | Installed `wagtail-unveil` package version (not the API version) |

If a `filter` query parameter is unrecognised, the response is not filtered and `metadata.applied_filter` is `null`.

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
