# Frontend Assets Contributor Guide

This guide covers how to work on report frontend assets in this repository.
It is contributor-focused and describes source layout, build/test workflows, and CI expectations.

## Read This If...

Read this page if you are changing report CSS or JavaScript and need the canonical contributor workflow for asset source, tests, generated files, and CI behavior.

## Source And Output Layout

- `assets_src/css/` — editable report CSS source
- `assets_src/js/` — editable JavaScript source modules for report behavior
- `scripts/report.entry.js` — ordered entry file used for bundling
- `scripts/build-report-assets.mjs` — esbuild script that generates report frontend assets
- `wagtail_unveil/static/wagtail_unveil/css/` — generated CSS artifacts:
  - `admin_urls_report.css`
  - `admin_urls_report.min.css`
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

Run frontend asset lint/format checks (Biome):

```bash
npm run lint:assets
npm run lint:assets:fix
# or
make lint-assets
make lint-assets-fix
```

Build frontend assets (JS + CSS):

```bash
npm run build:assets
# or
make build-assets
```

Watch mode while editing frontend source:

```bash
npm run build:assets:watch
```

## When To Rebuild Assets

Rebuild assets after changes to any of the following:

- files in `assets_src/css/`
- files in `assets_src/js/`
- `scripts/report.entry.js`
- `scripts/build-report-assets.mjs`

Generated asset files in `wagtail_unveil/static/wagtail_unveil/css/` and `wagtail_unveil/static/wagtail_unveil/js/` are release artifacts and should be committed with the source changes that require them.

## Report Template Contract

Reports currently load the minified bundle in:

- `wagtail_unveil/templates/wagtail_unveil/base_report.html`

Template include:

- `wagtail_unveil/css/admin_urls_report.min.css`
- `wagtail_unveil/js/report.bundle.min.js`

## Testing Strategy

- Unit and integration-style behavior checks run in Vitest/jsdom under `tests/js/`
- A bundle smoke test verifies the built bundle boots and renders expected report content

## CI Behavior And Recovery

CI includes frontend asset checks:

- `frontend-lint` runs Biome checks for contributor-owned frontend asset files
- `frontend-test` runs JavaScript tests
- `frontend-assets` runs the build and fails if generated bundle artifacts are stale

If `frontend-assets` fails:

1. Run `npm run build:assets` locally.
2. Commit updated generated assets in `wagtail_unveil/static/wagtail_unveil/css/` and `wagtail_unveil/static/wagtail_unveil/js/`.
3. Push again.

## Pre-Push Checklist

Run these before opening/updating a PR with frontend asset changes:

```bash
make lint
make coverage
npm run lint:assets
npm run test:js
npm run build:assets
```

## Formatting/Lint Scope

Biome is the canonical formatter/linter for frontend source files in this repository.

Included paths:

- `assets_src/**/*.{js,mjs,cjs}`
- `assets_src/**/*.css`
- `scripts/**/*.{js,mjs,cjs}`
- `tests/js/**/*.{js,mjs,cjs}`

Excluded generated artifacts:

- `wagtail_unveil/static/wagtail_unveil/css/admin_urls_report.css`
- `wagtail_unveil/static/wagtail_unveil/css/admin_urls_report.min.css`
- `wagtail_unveil/static/wagtail_unveil/js/report.bundle.js`
- `wagtail_unveil/static/wagtail_unveil/js/report.bundle.min.js`

Pre-commit runs `npm run lint:assets:fix` for these contributor-owned frontend files so style/lint issues are fixed before commit.
