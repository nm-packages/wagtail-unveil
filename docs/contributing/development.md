# Development Guide

This guide is for contributors working in this repository (sandbox + tests). It is the canonical contributor workflow guide and is not part of the public package interface.

## Local Setup

Setup commands:

```bash
make setup
make env
make install
make migrate
make sample-data
```

Optional: create a superuser for report UI access.
Report pages also require `DEBUG=True`, unless you explicitly enable `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS`.
That production setting only opens the built-in HTML report/settings UI for superusers; normal production JSON API access still uses `Authorization: Bearer <WAGTAIL_UNVEIL_API_KEY>`.

```bash
make superuser
```

Run the sandbox server:

```bash
make runserver
make run
```

## Using the Sandbox

`sandbox/` is the local integration environment for contributor work on `wagtail_unveil`. Use it to exercise package behavior inside a realistic Wagtail project while keeping reusable package logic inside `wagtail_unveil/`.

The boundary matters:

- `wagtail_unveil/` is the distributable package and must stay reusable across consuming projects.
- `sandbox/` is where local fixture data, example apps, and debugging helpers live so contributors can inspect behavior in a live Wagtail site.

The normal local sandbox loop is:

```bash
make setup
make runserver
make superuser      # optional, needed for report UI access
make sample-data    # optional, rerun when you want fresh representative content
```

The sandbox defaults are tuned for local development. The `.env` file created from `.env.example` sets `WAGTAIL_UNVEIL_API_KEY=dev-secret` by default so the JSON endpoints work locally with Bearer token auth, and `sandbox.settings` keeps `DEBUG=True` so report views are available to a superuser without the production opt-in path.

### What Sample Data Gives You

`make sample-data` runs the sandbox-only `create_sample_data` management command. It creates representative content and objects that make local discovery output useful instead of empty:

- Wagtail pages, including listing/detail-style content
- images and documents
- redirects and promoted search results
- snippets, chooser-backed models, and site settings
- form pages and related form submissions
- routable event pages and related page types
- an `editor` user for non-superuser/admin-role checks

This matters when you are developing discovery changes, testing parameterized admin routes, checking resolver output in the reports, or reproducing bugs that only appear when real objects exist to resolve against.

### Useful Local URLs

Once the sandbox server is running, these are the main URLs to use while developing:

- `/admin/` - Wagtail admin
- `/unveil/report/backend-urls/` - backend/admin discovery report
- `/unveil/report/frontend-urls/` - frontend discovery report
- `/unveil/report/platform/` - runtime and dependency inventory report
- `/unveil/report/settings/` - local settings and diagnostics view
- `/unveil/api/v1/backend-urls/` - backend URLs JSON endpoint
- `/unveil/api/v1/frontend-urls/` - frontend URLs JSON endpoint
- `/unveil/api/v1/platform/` - runtime metadata and dependency inventory JSON endpoint
- `/intentional-error/` - deliberate frontend 500 route for debugging failure handling

For the JSON endpoints, pass the local API key from `.env`, for example:

```bash
curl -H "Authorization: Bearer dev-secret" http://localhost:8000/unveil/api/v1/backend-urls/
curl -H "Authorization: Bearer dev-secret" http://localhost:8000/unveil/api/v1/frontend-urls/
curl -H "Authorization: Bearer dev-secret" http://localhost:8000/unveil/api/v1/platform/
```

### Common Contributor Workflows

Use the sandbox when you need to:

- verify new discovery behavior against realistic Wagtail content before or alongside adding tests
- reproduce report or API bugs in a live Wagtail app instead of reasoning from unit tests alone
- inspect whether sandbox apps and extension hooks expose the expected concrete admin/frontend URLs
- confirm parameterized/admin routes become testable once sample objects exist
- use sample data to understand current behavior before tightening tests or changing fixtures in `tests/`

## Day-to-Day Workflow

Run the standard validation loop while developing:

```bash
make test
make test-js
make lint
make coverage
```

Development-only helpers:

```bash
make makemigrations
```

## Extended Workflows

Python version matrix checks:

```bash
make tox
make tox-smoke
```

Frontend assets:

```bash
make build-assets
make lint-assets
make lint-assets-fix
```

HTML documentation site:

```bash
make docs-build
make docs-serve
```

Other validation and maintenance targets:

```bash
make lint-fix
make coverage-html
make pre-commit
make clean
```

## CI Expectations

- Pull requests run lint, JS checks, coverage, and smoke tox jobs.
- The full tox matrix runs on pushes to `main`, manual dispatch, and the weekly scheduled CI run.

See `.github/workflows/ci.yml` for exact job definitions. The HTML docs site is also validated in CI and deployed from `main` via `.github/workflows/docs.yml`.

## Documentation Maintenance

When changing contributor commands or Make targets:

1. Update `Makefile`.
2. Update command docs in this file.
3. Keep `README.md` focused and linked to this file.
4. Keep those command-doc updates in the same PR as the Makefile/command change.

`AGENTS.md` should continue to point agents at this guide for command and validation workflow, but it should not duplicate the full command catalog.

For every pull request:

1. Add a concise note under `CHANGELOG.md` -> `## Unreleased`.
2. Keep that changelog update in the same PR as the change itself.

## Related Docs

- User-facing package overview: [README.md](https://github.com/nm-packages/wagtail-unveil/blob/main/README.md)
- Coding conventions: [CONVENTIONS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/CONVENTIONS.md)
- Agent project guidance: [AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/AGENTS.md) — agent-facing repo context and startup workflow; use this page as the canonical command and validation reference.
- Documentation hub: [../index.md](../index.md)
- Frontend assets: [frontend-assets.md](frontend-assets.md)
- API lifecycle/versioning: [api-versioning.md](api-versioning.md)
- Discovery internals: [discovery-architecture.md](discovery-architecture.md)
- Discovery workflow diagrams: [discovery-workflows.md](discovery-workflows.md)
- Release runbook: [releasing.md](releasing.md)
