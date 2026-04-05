# wagtail-unveil

> Currently in active development. You should consider this package could be unstable and subject to breaking changes.

[![PyPI version](https://img.shields.io/pypi/v/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Python versions](https://img.shields.io/pypi/pyversions/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Wagtail versions](https://img.shields.io/badge/wagtail-7.0--7.3-teal.svg)](https://pypi.org/project/wagtail-unveil/)
[![License](https://img.shields.io/pypi/l/wagtail-unveil.svg)](https://github.com/nm-packages/wagtail-unveil/blob/main/LICENSE)

> Discover and test every URL in your Wagtail site - frontend and admin.

![Frontend URLs Report](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/frontend_report.jpg)

## Overview

Wagtail sites can accumulate many URLs across the admin site and frontend. Broken routes can hide until a user hits an error. **wagtail-unveil** discovers your URLs and helps you verify responses for your apps routes.

It exposes discovery through:
- JSON API endpoints (Bearer token auth)
- interactive HTML reports in Wagtail admin (superuser + `DEBUG=True`)
- a dedicated settings and diagnostics page in Wagtail admin (superuser + `DEBUG=True`)
- a dashboard panel linking to the admin report, frontend report, and settings page

## Quick Start

Canonical documentation hub: [wagtail-unveil documentation](https://nm-packages.github.io/wagtail-unveil/)

```bash
pip install wagtail-unveil==0.1.0a5
```

> `0.1.0a5` is the current public alpha release. It is intended for early adopters and real-world testing, and breaking changes may still happen before a stable release.
> To track unreleased changes from GitHub instead, use:

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

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/frontend-urls/
```

For installation details, configuration, API usage, reports, and extension recipes, use the [documentation hub](https://nm-packages.github.io/wagtail-unveil/).

## Compatibility

| Python                        | Django              | Wagtail    |
|-------------------------------|---------------------|------------|
| 3.10, 3.11, 3.12, 3.13, 3.14 | 4.2, 5.1, 5.2, 6.0 | 7.0 - 7.3 |

## Documentation

- Documentation hub: [wagtail-unveil docs](https://nm-packages.github.io/wagtail-unveil/)
- Installation and setup: [Getting Started](https://nm-packages.github.io/wagtail-unveil/getting-started/installation/)
- Settings and API key configuration: [Settings Reference](https://nm-packages.github.io/wagtail-unveil/configuration/settings-reference/)
- Feature guides: [Features](https://nm-packages.github.io/wagtail-unveil/features/)
- JSON API reference: [API Reference](https://nm-packages.github.io/wagtail-unveil/api/endpoints/)
- Recipes: [Recipes](https://nm-packages.github.io/wagtail-unveil/recipes/)
- Contributor docs: [Contributing](https://nm-packages.github.io/wagtail-unveil/contributing/)
- Sandbox contributor workflow: [Development Guide](https://nm-packages.github.io/wagtail-unveil/contributing/development/)

## License

[MIT](https://github.com/nm-packages/wagtail-unveil/blob/main/LICENSE)
