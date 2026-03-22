# Installation

## Requirements

| Python | Django | Wagtail |
|---|---|---|
| 3.10, 3.11, 3.12, 3.13, 3.14 | 4.2, 5.1, 5.2, 6.0 | 7.0 – 7.3 |

## Install the Package

```bash
pip install wagtail-unveil==0.1.0a2
```

> `0.1.0a2` is the current public alpha release. It is intended for early adopters and real-world testing, and breaking changes may still happen before a stable release.
> To try the latest unreleased changes from GitHub instead:
>
> ```bash
> pip install git+https://github.com/nm-packages/wagtail-unveil.git
> ```

## Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    "wagtail_unveil",
    # ...
]
```

## Include Package URLs

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("unveil/", include("wagtail_unveil.urls")),
]
```

## Set the API Key

Set `WAGTAIL_UNVEIL_API_KEY` as an environment variable (recommended):

```bash
export WAGTAIL_UNVEIL_API_KEY=your-secret-key
```

Or set it in Django settings:

```python
WAGTAIL_UNVEIL_API_KEY = "your-secret-key"
```

If both are set, the environment variable takes precedence.

## Try the Reports

HTML reports require a **superuser login** and **`DEBUG=True`**:

- `/unveil/report/backend-urls/` — admin URL discovery report
- `/unveil/report/frontend-urls/` — frontend URL discovery report
- `/unveil/report/settings/` — settings diagnostic page

You can also open these pages from links in the Wagtail admin dashboard panel.

## Try the API

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/frontend-urls/
```

## Related

- [Configuration](../configuration/settings-reference.md) — Customise page limits and URL exclusions
- [Features](../features/index.md) — Explore what the reports can do
- [API Reference](../api/endpoints.md) — Full API endpoint documentation
- [Getting Started Index](index.md) — Back to section overview
