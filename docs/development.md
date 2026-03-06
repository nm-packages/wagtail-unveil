# Development Guide

This guide is for contributors working in this repository (sandbox + tests). It is not part of the public package interface.

## Local Setup

```bash
make setup
```

Optional: create a superuser for report UI access.

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
make docs-check
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

- Pull requests run lint, docs-check, JS checks, coverage, and smoke tox jobs.
- Pushes to `main` also run the full tox matrix on CI schedule/dispatch policies.

See `.github/workflows/ci.yml` for exact job definitions.

## Documentation Maintenance

When changing contributor commands or Make targets:

1. Update `Makefile`.
2. Update command docs in `AGENTS.md` and this file.
3. Keep `README.md` focused and linked to this file.
4. Run `make docs-check` before merging.

## Related Docs

- User-facing package overview: [../README.md](../README.md)
- Agent project guidance: [../AGENTS.md](../AGENTS.md)
- Usage reference: [usage.md](usage.md)
- Frontend assets: [frontend-assets.md](frontend-assets.md)
- API lifecycle/versioning: [api-versioning.md](api-versioning.md)
- Discovery internals: [discovery-architecture.md](discovery-architecture.md)
- Release runbook: [releasing.md](releasing.md)
