# wagtail-unveil

> Currently in active development. You should consider this package could be unstable and subject to breaking changes.

[![PyPI version](https://img.shields.io/pypi/v/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Python versions](https://img.shields.io/pypi/pyversions/wagtail-unveil.svg)](https://pypi.org/project/wagtail-unveil/)
[![Wagtail versions](https://img.shields.io/badge/wagtail-7.0--7.3-teal.svg)](https://pypi.org/project/wagtail-unveil/)
[![License](https://img.shields.io/pypi/l/wagtail-unveil.svg)](https://github.com/nm-packages/wagtail-unveil/blob/main/LICENSE)

> Discover and test every URL in your Wagtail site - frontend and admin.

![Frontend URLs Report](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/frontend_report.jpg)

## Why?

Wagtail sites can accumulate many URLs across the admin site and frontend. Broken routes can hide until a user hits an error. **wagtail-unveil** discovers your URLs and helps you verify responses for your apps routes.

It exposes discovery through:
- JSON API endpoints (Bearer token auth)
- interactive HTML reports in Wagtail admin (superuser + `DEBUG=True`)
- a dedicated settings and diagnostics page in Wagtail admin (superuser + `DEBUG=True`)
- a dashboard panel linking to the admin report, frontend report, and settings page

## Quick Start

Detailed setup docs: [docs/getting-started/installation.md](docs/getting-started/installation.md)

```bash
pip install wagtail-unveil==0.1.0a2
```

> `0.1.0a2` is the current public alpha release. It is intended for early adopters and real-world testing, and breaking changes may still happen before a stable release.
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

Try the reports (HTML admin views; requires superuser session and `DEBUG=True`):
- `/unveil/report/backend-urls/` — [Backend URLs Report docs](docs/features/backend-urls-report.md)
- `/unveil/report/frontend-urls/` — [Frontend URLs Report docs](docs/features/frontend-urls-report.md)
- `/unveil/report/settings/` — [Settings Page docs](docs/features/settings-page.md)

You can open the report and settings pages from links in the Wagtail admin [dashboard panel](docs/features/dashboard-panel.md).

The settings page shows the current effective `wagtail-unveil` configuration and related runtime diagnostics.
Because it is intended for local debugging, it also shows the full `WAGTAIL_UNVEIL_API_KEY` value to superusers while `DEBUG=True`.

Try the API. Detailed endpoint docs: [docs/api/endpoints.md](docs/api/endpoints.md)

```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/backend-urls/
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/unveil/api/v1/frontend-urls/
```

The frontend API keeps canonical paths in the `url` field and, when needed, adds optional `resolved_url` or `query_params` data so the report UI can test parameterised and query-driven routes without rewriting the discovered URL itself.

Projects can also extend admin URL parameter resolution for developer-installed Wagtail packages by registering the `register_unveil_admin_instance_resolvers` Wagtail hook and returning `AdminInstanceResolver` objects from `wagtail_unveil.discovery.extensions`. `matches` and `resolver` must both be callables. If a third-party hook raises, returns an invalid shape, or provides a malformed resolver, `wagtail-unveil` logs a warning and skips only that broken contribution so the rest of admin discovery can continue. This is the intended way to support third-party admin packages such as `wagtail-modeladmin` in your own project. For a worked example and the general hook pattern, see [Add Custom Admin URL Resolvers](docs/recipes/custom-admin-url-resolvers.md).

## Key Configuration

Most projects only need `WAGTAIL_UNVEIL_API_KEY` from the quickstart to use the JSON API.

- `WAGTAIL_UNVEIL_PAGES_PER_TYPE` — controls how many page instances per type are included in frontend URL discovery; defaults to `1`
- `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES` — excludes matching URL prefixes from frontend and admin discovery; defaults to `[]`

For full setting details, including environment variable usage, normalization rules, and edge cases, see [docs/configuration/settings-reference.md](docs/configuration/settings-reference.md).

## Compatibility

| Python                        | Django              | Wagtail    |
|-------------------------------|---------------------|------------|
| 3.10, 3.11, 3.12, 3.13, 3.14 | 4.2, 5.1, 5.2, 6.0 | 7.0 - 7.3 |

## Documentation

- Documentation index: [docs/index.md](docs/index.md)
- Installation guide: [docs/getting-started/installation.md](docs/getting-started/installation.md)
- Settings reference: [docs/configuration/settings-reference.md](docs/configuration/settings-reference.md)
- Recipes: [docs/recipes/index.md](docs/recipes/index.md)
- API endpoints: [docs/api/endpoints.md](docs/api/endpoints.md)
- Report features: [docs/features/index.md](docs/features/index.md)
- Contributor/developer guide: [docs/contributing/development.md](docs/contributing/development.md)
- Coding conventions: [CONVENTIONS.md](CONVENTIONS.md)
- API versioning policy: [docs/contributing/api-versioning.md](docs/contributing/api-versioning.md)
- Discovery internals: [docs/contributing/discovery-architecture.md](docs/contributing/discovery-architecture.md)
- Frontend asset workflow: [docs/contributing/frontend-assets.md](docs/contributing/frontend-assets.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Release runbook: [docs/contributing/releasing.md](docs/contributing/releasing.md)
- Agent-facing project guidance: [AGENTS.md](AGENTS.md)

## License

[MIT](LICENSE)
