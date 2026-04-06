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
Report pages also require `DEBUG=True`.

```bash
make superuser
```

Run the sandbox server:

```bash
make runserver
make run
```

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

When making notable user-visible, contributor-visible, or maintainer-relevant changes that are not yet released:

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
