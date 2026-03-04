# Frontend Assets Contributor Guide

This guide covers how to work on report frontend assets in this repository.
It is contributor-focused and describes source layout, build/test workflows, and CI expectations.

## Source And Output Layout

- `assets_src/js/` — editable JavaScript source modules for report behavior
- `scripts/report.entry.js` — ordered entry file used for bundling
- `scripts/build-report-js.mjs` — esbuild script that generates report bundles
- `wagtail_unveil/static/wagtail_unveil/js/` — generated bundle artifacts:
  - `report.bundle.js`
  - `report.bundle.min.js`
- `tests/js/` — Vitest + jsdom frontend tests (behavior and bundle smoke checks)

## Required Workflows

Install dependencies:

```bash
npm ci
```

Run JavaScript tests:

```bash
npm run test:js
# or
make test-js
```

Run JavaScript lint/format checks (Biome):

```bash
npm run lint:js
npm run lint:js:fix
# or
make lint-js
make lint-js-fix
```

Build bundles:

```bash
npm run build:js
# or
make build-js
```

Watch mode while editing frontend source:

```bash
npm run build:js:watch
```

## When To Rebuild Bundles

Rebuild bundles after changes to any of the following:

- files in `assets_src/js/`
- `scripts/report.entry.js`
- `scripts/build-report-js.mjs`

Generated bundle files in `wagtail_unveil/static/wagtail_unveil/js/` are release artifacts and should be committed with the source changes that require them.

## Report Template Contract

Reports currently load the minified bundle in:

- `wagtail_unveil/templates/wagtail_unveil/base_report.html`

Template include:

- `wagtail_unveil/js/report.bundle.min.js`

## Testing Strategy

- Unit and integration-style behavior checks run in Vitest/jsdom under `tests/js/`
- A bundle smoke test verifies the built bundle boots and renders expected report content

## CI Behavior And Recovery

CI includes frontend asset checks:

- `js-lint` runs Biome checks for contributor-owned JS files
- `js-tests` job runs JavaScript tests
- `assets-check` runs the build and fails if generated bundle artifacts are stale

If `assets-check` fails:

1. Run `npm run build:js` locally.
2. Commit updated bundle artifacts in `wagtail_unveil/static/wagtail_unveil/js/`.
3. Push again.

## Pre-Push Checklist

Run these before opening/updating a PR with frontend asset changes:

```bash
make lint
make coverage
npm run lint:js
npm run test:js
npm run build:js
```

## Formatting/Lint Scope

Biome is the canonical formatter/linter for JavaScript in this repository.

Included paths:

- `assets_src/**/*.js`
- `scripts/**/*.js`
- `tests/js/**/*.js`

Excluded generated artifacts:

- `wagtail_unveil/static/wagtail_unveil/js/report.bundle.js`
- `wagtail_unveil/static/wagtail_unveil/js/report.bundle.min.js`

Pre-commit runs `npm run lint:js:fix` for these contributor-owned JS files so style/lint issues are fixed before commit.
