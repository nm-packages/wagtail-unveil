# wagtail-unveil

> Currently in active development. You should consider this package could be unstable and subject to breaking changes.

> Discover and test every URL in your Wagtail site - frontend and admin.

[![PyPI version](https://img.shields.io/pypi/v/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Python versions](https://img.shields.io/pypi/pyversions/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Wagtail versions](https://img.shields.io/badge/wagtail-7.0--7.3-teal.svg)](https://pypi.org/project/wagtail-unveil/)
[![License](https://img.shields.io/pypi/l/wagtail-unveil.svg)](https://github.com/nm-packages/wagtail-unveil/blob/main/LICENSE)

![Frontend URLs Report](docs/frontend-urls-report.png)

## Why?

Wagtail sites can accumulate many URLs across the admin site and frontend. Broken routes can hide until a user hits an error. **wagtail-unveil** discovers your URLs and helps you verify responses for your apps routes.

It exposes discovery through:
- JSON API endpoints (Bearer token auth)
- interactive HTML reports in Wagtail admin (superuser + `DEBUG=True`)
- a dedicated settings and diagnostics page in Wagtail admin (superuser + `DEBUG=True`)
- a dashboard panel linking to all three pages

## Quick Start

```bash
pip install wagtail-unveil
```

> This package is currently in development and not yet released on PyPI. To install the latest development version, use:

```bash
pip install git+https://github.com/nm-packages/wagtail-unveil.git
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "wagtail_unveil",
    # ...
]
```

Include package URLs:

```python
urlpatterns = [
    # ...
    path("unveil/", include("wagtail_unveil.urls")),
]
```

Try the reports (HTML admin views; requires superuser session and `DEBUG=True`):
- `/unveil/report/backend-urls/`
- `/unveil/report/frontend-urls/`
- `/unveil/report/settings/`

You can open all three pages from links in the Wagtail admin dashboard panel.

The settings page shows the current effective `wagtail-unveil` configuration and related runtime diagnostics.
Because it is intended for local debugging, it also shows the full `WAGTAIL_UNVEIL_API_KEY` value to superusers while `DEBUG=True`.

Try the API:

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/frontend-urls/
```

## Configuration

### `WAGTAIL_UNVEIL_PAGES_PER_TYPE`

Controls how many page instances per page type are included in frontend URL discovery.

```python
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 1  # default behavior
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 3  # test up to 3 pages per type
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 0  # no limit
```

Defaults to `1` when omitted. Invalid/negative values fall back to `1`.

### `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

Excludes URL path prefixes from discovery.

```python
WAGTAIL_UNVEIL_SKIP_URL_PREFIXES = ["__debug__/", "/silk/"]
```

Defaults to `[]`. Leading slashes are normalized.

## Compatibility

| Python                        | Django              | Wagtail    |
|-------------------------------|---------------------|------------|
| 3.10, 3.11, 3.12, 3.13, 3.14 | 4.2, 5.1, 5.2, 6.0 | 7.0 - 7.3 |

## Documentation

- Full usage reference: [docs/usage.md](docs/usage.md)
- Contributor/developer guide: [docs/development.md](docs/development.md)
- Coding conventions: [CONVENTIONS.md](CONVENTIONS.md)
- API versioning policy: [docs/api-versioning.md](docs/api-versioning.md)
- Discovery internals: [docs/discovery-architecture.md](docs/discovery-architecture.md)
- Frontend asset workflow: [docs/frontend-assets.md](docs/frontend-assets.md)
- Release runbook: [docs/releasing.md](docs/releasing.md)
- Agent-facing project guidance: [AGENTS.md](AGENTS.md)

## License

[MIT](LICENSE)
