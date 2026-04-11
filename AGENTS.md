# AGENTS.md

This file is the canonical guidance for coding agents working in this repository.

## Project Overview

**wagtail-unveil** is a reusable Wagtail package that discovers frontend and Wagtail admin URLs in a site. It exposes that functionality through JSON endpoints, HTML reports, and a Wagtail dashboard panel so developers can inspect URLs and test whether they return expected response codes.

## Repository Structure

- `wagtail_unveil/` — The distributable package published to PyPI
- `sandbox/` — Example Wagtail project used for development and testing
- `tests/` — Root-level test package for the reusable package
- `.env.example` — Template for local development environment variables

## Docs Map

- `README.md` — user-facing package overview and minimal quickstart
- `docs/index.md` — canonical documentation hub for users, contributors, and maintainers
- `docs/contributing/development.md` — canonical contributor command, validation, and CI-aligned workflow guide
- `CONVENTIONS.md` — canonical coding, testing, and documentation conventions
- `AGENTS.md` files — canonical agent-facing guidance and documentation contract

## Issue Startup Workflow

When starting work from a GitHub issue, pull the issue context first and confirm whether GitHub already has a linked branch for that issue. When starting a new piece of scoped work from the current local branch state, check whether you are on `main` before implementation begins.

Required startup sequence for issue work:

1. Fetch and read the issue before making local changes.
2. Check whether the issue already has a linked branch.
3. Fetch remote refs and switch to the linked branch locally before editing files.
4. If no linked branch exists, create and link a branch for the issue, then switch to that branch before making changes.

Required PR linkage for issue-scoped work:

1. When opening a new PR for work that came from a GitHub issue, mention the issue in the PR body.
2. Prefer a closing keyword such as `Closes #123` when the PR is intended to fully resolve the issue; otherwise include a plain issue reference so the relationship is still visible.
3. Verify that the issue reference is present before finalizing the PR creation flow.

Required startup sequence for new scoped work begun outside an existing issue branch:

1. Check the current local branch before making changes.
2. If you are already on a suitable non-`main` working branch, continue there only if it clearly matches the new task.
3. If you are on `main`, pause before implementation and ask the user whether a new branch should be created.
4. When asking, suggest a suitable branch title instead of asking an open-ended branch question.

Required PR-metadata check when working on an existing branch:

1. If the current branch has an open PR, review whether the PR title and summary still match the actual scope of the branch.
2. If the PR metadata has drifted from the work now on the branch, tell the user that the current title and summary appear outdated.
3. Offer a short set of concrete replacement PR title suggestions for the user to choose from.
4. Treat the PR summary/body as needing the same drift check and update discussion, not just the title.

Required agent self-review before handoff:

1. After completing a code change, review the patch before final handoff or PR creation.
2. Use the existing repo guidance as the review baseline, including `CONVENTIONS.md`, relevant nested `AGENTS.md` files, contributor validation workflow, and any task-specific architecture docs.
3. Check for maintainability, unnecessary complexity, duplicated logic, duplicated or overly fragmented tests that could be sensibly combined or refactored, missing or weak tests, documentation drift, scope creep, and obvious security or safety regressions that follow from the touched code.
4. Run the relevant validation steps already required by repo guidance when feasible, and incorporate the results into that review.
5. If the review finds worthwhile follow-up improvements that are not clearly required to finish the task, call them out explicitly and get approval before broadening the patch.
6. If the review finds a required fix for correctness, safety, or repo-policy compliance, address it before considering the work complete.

Safety rule: do not start implementation for issue-scoped work on `main` when the issue is expected to have its own branch. Do not start newly scoped work on `main` without first checking whether the user wants a branch created and proposing a suitable branch title. When working on a branch with an open PR, do not ignore title/summary drift if the branch scope has materially changed.

For contributor commands, validation loops, and release-adjacent workflow, use `docs/contributing/development.md` as the canonical reference. For coding, testing, and documentation conventions, use `CONVENTIONS.md`.
When changing code, treat local simplification of touched duplication or unnecessary indirection as part of completing the work, not optional polish; keep the canonical thresholds and scope limits in `CONVENTIONS.md`.

## Architecture Summary

### URL Discovery

The core discovery logic lives in `wagtail_unveil/discovery/`.

- `discovery/backend.py` — `BackendURL` dataclass and `get_admin_urls()`
- `discovery/backend_resolution.py` — admin parameter resolution helpers
- `discovery/extensions.py` — hookable admin instance resolver extensions for installed Wagtail packages
- `discovery/frontend.py` — `FrontendURL` dataclass and `get_frontend_urls()`
- `discovery/frontend_resolution.py` — frontend routable and API URL resolution helpers
- `discovery/utils.py` — shared resolver walking and route normalization helpers
- `docs/contributing/discovery-architecture.md` — canonical contributor-facing explanation of discovery, normalization, parameter resolution, and testability rules

Admin discovery walks the Django resolver tree, filters to admin routes, and resolves supported parameterized URLs against real objects where possible. Frontend discovery combines live page URLs, page-derived URLs, and non-admin resolver routes. Use `docs/contributing/discovery-architecture.md` for the full discovery rules instead of duplicating them here.

### Delivery Layer

The package exposes a single URL config in `wagtail_unveil/urls.py` with `app_name = "wagtail_unveil"`.

Included by a consuming project as:

```python
path("unveil/", include("wagtail_unveil.urls"))
```

Routes provided:

- `api/v1/backend-urls/` → `wagtail_unveil:api_v1_backend_urls`
- `api/v1/frontend-urls/` → `wagtail_unveil:api_v1_frontend_urls`
- `api/v1/platform/` → `wagtail_unveil:api_v1_platform`
- `report/backend-urls/` → `wagtail_unveil:report_backend_urls`
- `report/frontend-urls/` → `wagtail_unveil:report_frontend_urls`
- `report/settings/` → `wagtail_unveil:report_settings`

Versioned API paths, URL names, and lifecycle metadata are derived from `wagtail_unveil.api_contract.API_VERSION_REGISTRY`. Use `docs/contributing/api-versioning.md` for versioning policy and workflow.

JSON endpoints use Bearer token auth via `WAGTAIL_UNVEIL_API_KEY`. HTML report views require a superuser and either `DEBUG=True` or `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True`.

### Sandbox

The sandbox project mounts the package at `/unveil/`, exposes Wagtail API v2 routes at `/api/v2/`, and serves Wagtail pages from `/`.

## Directory-Specific Guidance

More focused guidance lives in:

- [wagtail_unveil/AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/wagtail_unveil/AGENTS.md) — package-specific architecture and constraints
- [sandbox/AGENTS.md](https://github.com/nm-packages/wagtail-unveil/blob/main/sandbox/AGENTS.md) — sandbox-specific structure and sample-data notes

## Documentation Contract

- `AGENTS.md` files are the canonical agent-facing project guidance
- Root `AGENTS.md` owns repo-wide agent workflow, repo orientation, and doc routing
- Nested `AGENTS.md` files own only directory-local agent guidance
- `CONVENTIONS.md` is the canonical reference for coding, testing, and documentation conventions
- `docs/contributing/development.md` is the canonical contributor workflow guide for commands, validation loops, and CI-oriented development
- `docs/contributing/discovery-architecture.md` is the canonical contributor-facing reference for discovery and resolution behavior; AGENTS files should point to it rather than duplicating detailed flow logic
- `docs/contributing/frontend-assets.md` is the canonical contributor-facing reference for frontend asset source, build/test workflow, and CI expectations
- `docs/contributing/api-versioning.md` is the canonical contributor-facing reference for API version lifecycle policy and version-bump workflow
- `docs/contributing/releasing.md` is the canonical contributor-facing reference for release workflow, PyPI Trusted Publisher setup, and maintainer release troubleshooting
- `README.md` should stay focused on package overview and quickstart, linking out to canonical contributor docs instead of duplicating workflow detail
