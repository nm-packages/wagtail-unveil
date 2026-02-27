# wagtail-unveil

> Discover and test every URL in your Wagtail site — frontend and admin.

[![PyPI version](https://img.shields.io/pypi/v/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Python versions](https://img.shields.io/pypi/pyversions/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Wagtail versions](https://img.shields.io/badge/wagtail-7.0--7.3-teal.svg)](https://pypi.org/project/wagtail-unveil/)
[![License](https://img.shields.io/pypi/l/wagtail-unveil.svg)](https://github.com/nickmoreton/wagtail-unveil/blob/main/LICENSE)

![Frontend URLs Report](docs/frontend-urls-report.png)

## Why?

Wagtail sites accumulate hundreds of URLs — admin views, page routes, routable sub-paths, API endpoints. Broken routes hide in plain sight until a user hits a 500 error. **wagtail-unveil** automatically discovers every URL in your site and lets you verify they all return 200 OK.

## Features

- **Full URL discovery** — walks Django's URL resolver tree and Wagtail's page tree to find every admin and frontend route, including `RoutablePageMixin` sub-paths
- **Smart parameterized URL resolution** — automatically resolves URLs with parameters (snippets, images, documents, users) using real database instances so they become testable
- **Interactive HTML reports** — browser-based tables with one-click testing, Test All with progress tracking, search, sort, and a Hide Untestable toggle
- **Management commands** — `show_admin_urls` and `show_frontend_urls` for terminal output with filtering options
- **JSON API** — bearer-token-authenticated endpoints for CI/CD integration and external monitoring tools
- **Dashboard widget** — links to both reports directly from the Wagtail admin home page

## Quick Start

```bash
pip install wagtail-unveil
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "wagtail_unveil",
    # ...
]
```

Run migrations:

```bash
python manage.py migrate
```

Discover your URLs:

```bash
# List all admin URLs
python manage.py show_admin_urls

# List all frontend URLs
python manage.py show_frontend_urls
```

Or add the HTML reports to your `urls.py` and browse them interactively:

```python
urlpatterns = [
    # ...
    path("unveil-report/", include("wagtail_unveil.report_urls")),
]
```

Then visit `/unveil-report/admin-urls/` or `/unveil-report/frontend-urls/` while logged in as a superuser (requires `DEBUG=True`).

## Usage

### Management Commands

```bash
# Admin URLs — all, static only, or parameterized only
python manage.py show_admin_urls
python manage.py show_admin_urls --static
python manage.py show_admin_urls --parameterized

# Frontend URLs — all, pages only, or resolver only
python manage.py show_frontend_urls
python manage.py show_frontend_urls --pages
python manage.py show_frontend_urls --resolver
```

### HTML Reports

Interactive browser-based reports with one-click URL testing. Requires superuser login and `DEBUG=True`.

- **Admin URLs Report** — `/unveil-report/admin-urls/`
- **Frontend URLs Report** — `/unveil-report/frontend-urls/`

### JSON API

Add the API endpoints to your `urls.py`:

```python
urlpatterns = [
    # ...
    path("unveil-api/", include("wagtail_unveil.api_urls")),
]
```

Set `WAGTAIL_UNVEIL_API_KEY` via environment variable (recommended) or Django settings, then query with a Bearer token.
If both are set, the environment variable takes precedence.

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil-api/admin-urls/
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil-api/frontend-urls/
```

Filter with `?filter=static`, `?filter=parameterized`, `?filter=pages`, or `?filter=resolver`.

For full API response examples and detailed feature documentation, see [docs/usage.md](docs/usage.md).

### Dashboard Widget

A panel on the Wagtail admin home page links directly to both reports (superuser + `DEBUG` only).

## Configuration

### `WAGTAIL_UNVEIL_PAGES_PER_TYPE`

Controls how many page instances per page type are included in the frontend URL report. Useful for sites with many pages of the same type where testing every one is unnecessary.

```python
# settings.py

# Test only 1 page per type (e.g., 1 HomePage, 1 BlogPage, 1 StandardPage)
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 1

# Test up to 3 pages per type
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 3

# Test all pages (no limit)
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 0
```

Default behavior is `1` page per type when the setting is omitted.
Values are normalized to a non-negative integer. Invalid or negative values default to `1`.
Use `0` explicitly for no limit.

### `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

A list of URL path prefixes to exclude from URL discovery. Useful when third-party packages register routes (e.g. `django-debug-toolbar`, `django-silk`) that you don't want to appear in the reports.

```python
# settings.py

# Exclude django-debug-toolbar routes
WAGTAIL_UNVEIL_SKIP_URL_PREFIXES = ["__debug__/"]

# Leading slashes are also accepted
WAGTAIL_UNVEIL_SKIP_URL_PREFIXES = ["/__debug__/", "/silk/"]
```

The setting applies to both the frontend resolver source and the admin URL discovery. Leading slashes are stripped internally, so `"/__debug__/"` and `"__debug__/"` are equivalent. Default is `[]` (no exclusions). Invalid values (non-list, non-string items) are silently ignored.

## Compatibility

| Python                        | Django              | Wagtail    |
|-------------------------------|---------------------|------------|
| 3.10, 3.11, 3.12, 3.13, 3.14 | 4.2, 5.1, 5.2, 6.0 | 7.0 – 7.3 |

## Development

```bash
make setup      # Full dev setup: env, install, migrate, superuser, sample data
make runserver  # Start the sandbox dev server
make test       # Run package tests
make tox        # Run tests across all Python/Django/Wagtail versions
make lint       # Lint with ruff
make coverage   # Run tests with coverage report
make pre-commit # Run pre-commit hooks on all files
```

See [CLAUDE.md](CLAUDE.md) for the full list of development commands.

## License

[MIT](LICENSE)
