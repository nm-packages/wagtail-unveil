# Development Guide

This guide is for contributors working in this repository (sandbox + tests). It is not part of the public package interface.

## Read This If...

Read this page first if you are setting up the repo, running the sandbox, or looking for the canonical contributor workflow and CI-aligned commands.

## Local Setup

```bash
make setup
```

Optional: create a superuser for report UI access.
Report pages also require `DEBUG=True`.

```bash
make superuser
```

Run the sandbox server:

```bash
make runserver
```

## Day-to-Day Workflow

Run the standard validation loop while developing:

```bash
make test
make test-js
make lint
make coverage
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

Other useful targets:

```bash
make lint-fix
make coverage-html
make pre-commit
```

## CI Expectations

- Pull requests run lint, JS checks, coverage, and smoke tox jobs.
- The full tox matrix runs on pushes to `main`, manual dispatch, and the weekly scheduled CI run.

See `.github/workflows/ci.yml` for exact job definitions.

## Documentation Maintenance

When changing contributor commands or Make targets:

1. Update `Makefile`.
2. Update command docs in `AGENTS.md` and this file.
3. Keep `README.md` focused and linked to this file.
4. Keep those command-doc updates in the same PR as the Makefile/command change.

## Related Docs

- User-facing package overview: [../../README.md](../../README.md)
- Coding conventions: [../../CONVENTIONS.md](../../CONVENTIONS.md)
- Agent project guidance: [../../AGENTS.md](../../AGENTS.md)
- Documentation hub: [../index.md](../index.md)
- Frontend assets: [frontend-assets.md](frontend-assets.md)
- API lifecycle/versioning: [api-versioning.md](api-versioning.md)
- Discovery internals: [discovery-architecture.md](discovery-architecture.md)
- Discovery workflow diagrams: [discovery-workflows.md](discovery-workflows.md)
- Release runbook: [releasing.md](releasing.md)
