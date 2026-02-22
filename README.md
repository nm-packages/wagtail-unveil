# wagtail-unveil

A reusable Wagtail package that discovers all URLs in a Wagtail site — both frontend and backend (admin) URLs. Useful for verifying that all routes return expected response codes.

## Features

### Management Command

List all admin URLs in the terminal:

```bash
# All admin URLs
python manage.py show_admin_urls

# Static URLs only (no path parameters)
python manage.py show_admin_urls --static

# Parameterized URLs only
python manage.py show_admin_urls --parameterized
```

### JSON API Endpoint

Query admin URLs programmatically from a running site — useful for external testing tools and monitoring.

**Setup:**

1. Add the API URLs to your project's `urls.py`:

```python
urlpatterns = [
    # ... your other URLs ...
    path("unveil-api/", include("wagtail_unveil.api_urls")),
]
```

2. Set the `WAGTAIL_UNVEIL_API_KEY` environment variable:

```bash
export WAGTAIL_UNVEIL_API_KEY=your-secret-key
```

**Usage:**

```bash
# All admin URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil-api/admin-urls/

# Static URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil-api/admin-urls/?filter=static"

# Parameterized URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil-api/admin-urls/?filter=parameterized"
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
  "count": 190
}
```

**Authentication:**

The endpoint requires a Bearer token matching the `WAGTAIL_UNVEIL_API_KEY` environment variable. Requests without a valid key receive a `403` response. If the environment variable is not set, the endpoint returns `500`.

### HTML Report Page

An interactive browser-based report showing all admin URLs in a table. Click "Test" on static URLs to check their HTTP status codes using your existing Wagtail session.

**Setup:**

1. Add the report URLs to your project's `urls.py`:

```python
urlpatterns = [
    # ... your other URLs ...
    path("unveil-report/", include("wagtail_unveil.report_urls")),
]
```

2. Visit `http://localhost:8000/unveil-report/admin-urls/` while logged into the Wagtail admin.

**Features:**

- Defaults to showing only static (testable) URLs — parameterized URLs are hidden until you click "All"
- Filter URLs by All / Static / Parameterized
- One-click testing of static URLs with colour-coded status codes (green=2xx, yellow=3xx, red=4xx/5xx)
- **Snippet URL resolution** — parameterized snippet URLs (edit, delete, copy, etc.) are automatically resolved using real database instances, making them testable via the report
- **Test All** button — runs all testable (static and resolved) URLs sequentially with a progress indicator and pass/fail summary
- Self-contained — no external CSS or JS dependencies
- **Superuser-only** — requires Wagtail superuser login; non-superusers are redirected to the login page
- **DEBUG-only** — returns 404 when `DEBUG=False`
- **Dashboard widget** — a panel on the Wagtail admin home page links directly to the report (superuser + DEBUG only)

## Future Features

- **Expanded parameterized URL testing** — Resolve more parameterized URL types beyond snippets (e.g. page URLs like `admin/pages/<int:pk>/edit/`).

## Development

```bash
# Install dependencies
uv sync

# Run the sandbox dev server
uv run python manage.py runserver

# Run tests
uv run python manage.py test wagtail_unveil

# Lint
uv run ruff check .
```
