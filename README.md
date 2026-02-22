# wagtail-unveil

A reusable Wagtail package that discovers all URLs in a Wagtail site — both frontend and backend (admin) URLs. Useful for verifying that all routes return expected response codes.

## Features

### Management Commands

List all admin URLs in the terminal:

```bash
# All admin URLs
python manage.py show_admin_urls

# Static URLs only (no path parameters)
python manage.py show_admin_urls --static

# Parameterized URLs only
python manage.py show_admin_urls --parameterized
```

List all frontend URLs (pages and resolver routes):

```bash
# All frontend URLs
python manage.py show_frontend_urls

# Page URLs only
python manage.py show_frontend_urls --pages

# Resolver URLs only
python manage.py show_frontend_urls --resolver
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

#### Frontend URLs API

```bash
# All frontend URLs
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil-api/frontend-urls/

# Page URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil-api/frontend-urls/?filter=pages"

# Resolver URLs only
curl -H "Authorization: Bearer your-secret-key" "http://localhost:8000/unveil-api/frontend-urls/?filter=resolver"
```

### HTML Report Pages

#### Admin URLs Report

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

- Shows all discovered URLs with testable/untestable counts in the summary
- One-click testing of static URLs with colour-coded status codes (green=2xx, yellow=3xx, red=4xx/5xx)
- **Parameterised URL resolution** — admin URLs with parameters (snippets, redirects, images, documents, users, groups) are automatically resolved using real database instances, making them testable via the report
- **Test All** button — runs all testable (static and resolved) URLs sequentially with a progress indicator and pass/fail summary
- **Hide Untestable** toggle — hides non-testable rows (parameterized, POST-only, regex) to focus on testable URLs; preference is saved in a cookie across sessions
- Self-contained — no external CSS or JS dependencies
- **Superuser-only** — requires Wagtail superuser login; non-superusers are redirected to the login page
- **DEBUG-only** — returns 404 when `DEBUG=False`
- **Dashboard widget** — a panel on the Wagtail admin home page links directly to both reports (superuser + DEBUG only)

#### Frontend URLs Report

An interactive browser-based report showing all frontend URLs — both Wagtail page URLs and Django resolver URLs.

Visit `http://localhost:8000/unveil-report/frontend-urls/` while logged into the Wagtail admin.

**Features:**

- **Two URL sources:** Wagtail page URLs (from `Page.objects.live().specific()`) and Django resolver URLs (non-admin routes)
- **Configurable page limit** — limit how many page instances per type are tested (see [Configuration](#configuration))
- One-click testing with colour-coded status codes
- **Test All** button with progress indicator and pass/fail summary
- **Hide Untestable** toggle — hides non-testable rows; preference saved in a cookie
- Searchable and sortable columns (URL, Source, Page Type, Title, Name)
- Self-contained — no external CSS or JS dependencies
- **Superuser-only** and **DEBUG-only**

## Configuration

### `WAGTAIL_UNVEIL_PAGES_PER_TYPE`

Controls how many page instances per page type are included in the frontend URL report. Useful for sites with many pages of the same type (e.g., hundreds of blog posts) where testing every single one is unnecessary.

```python
# settings.py

# Test only 1 page per type (e.g., 1 HomePage, 1 BlogPage, 1 StandardPage)
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 1

# Test up to 3 pages per type
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 3

# Test all pages (default behaviour)
WAGTAIL_UNVEIL_PAGES_PER_TYPE = 0
```

- **Default:** `0` (all pages — no limit)
- **Positive integer:** Limits to that many page instances per page type
- Only affects page URLs; resolver URLs are unaffected
- When active, the frontend report summary shows the limit

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
