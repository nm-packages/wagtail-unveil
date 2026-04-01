# Development Guide

This guide is for contributors working in this repository (sandbox + tests). It is not part of the public package interface.

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

- User-facing package overview: [../../README.md](https://github.com/nm-packages/wagtail-unveil/blob/main/README.md)
- Coding conventions: [../../CONVENTIONS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/CONVENTIONS.md)
- Agent project guidance: [../../AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/AGENTS.md)
- Documentation index: [../index.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/index.md)
- Frontend assets: [frontend-assets.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/frontend-assets.md)
- API lifecycle/versioning: [api-versioning.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/api-versioning.md)
- Discovery internals: [discovery-architecture.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/discovery-architecture.md)
- Discovery workflow diagrams: [discovery-workflows.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/discovery-workflows.md)
- Release runbook: [releasing.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/releasing.md)
