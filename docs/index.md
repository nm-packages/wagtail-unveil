# wagtail-unveil Documentation

Discover and test every URL in your Wagtail site — frontend and admin.

This is the canonical documentation hub for `wagtail-unveil`.

## Common Tasks

| I need to... | Go to |
|---|---|
| Install and set up `wagtail-unveil` | [Getting Started](getting-started/installation.md) |
| Configure the API key and settings | [Settings Reference](configuration/settings-reference.md) |
| Learn what the reports and dashboard do | [Features](features/index.md) |
| Use the JSON API | [API Reference](api/endpoints.md) |
| Add custom admin URL resolvers | [Add Custom Admin URL Resolvers](recipes/custom-admin-url-resolvers.md) |
| Understand discovery internals | [Discovery Architecture](contributing/discovery-architecture.md) |
| Work on the project locally | [Development Guide](contributing/development.md) |
| Release the package | [Releasing](contributing/releasing.md) |

## Use wagtail-unveil

- [Getting Started](getting-started/index.md) — Canonical starting point for installation, quick start, and first-time setup.
- [Features](features/index.md) — Canonical user-facing guide to reports, the settings page, and the dashboard panel.
- [Configuration](configuration/index.md) — Canonical reference for package settings and API key configuration.
- [API Reference](api/index.md) — Canonical reference for versioned JSON API endpoints, auth, and response shape.
- [Recipes](recipes/index.md) — Task-focused guides for extending `wagtail-unveil` in your own project.

## Contribute / maintain

- [Contributing](contributing/index.md) — Canonical contributor routing page for development, architecture, assets, API lifecycle, and release workflow.
- [Development Guide](contributing/development.md) — Contributor workflow entry point for local setup, validation, and day-to-day commands.
- [Discovery Architecture](contributing/discovery-architecture.md) — Canonical deep reference for discovery and resolution behavior.
- [Releasing](contributing/releasing.md) — Canonical maintainer runbook for package releases.

## Reference Map

- `README.md` is a thin package overview and quick-start entry point for repository visitors.
- `docs/index.md` is the canonical navigation hub for all documentation.
- Section index pages under `docs/` route readers to the right reference area without duplicating deep content.
- Contributor docs distinguish canonical references from companion material:
  - `development.md` is the workflow entry point
  - `discovery-architecture.md` is authoritative for discovery rules
  - `discovery-workflows.md` is a visual companion to that architecture guide
