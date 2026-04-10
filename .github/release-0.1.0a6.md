# wagtail-unveil 0.1.0a6

Sixth public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Full Change Summary

- simplify the public docs IA so `README.md` stays focused on the GitHub/PyPI overview and the docs site carries the deeper guides
- add an MkDocs + Material documentation site with Mermaid support, CI validation, and GitHub Pages deployment
- tighten contributor workflow guidance across `make help`, contributor docs, and agent docs
- clarify branch/PR workflow expectations for issue-linked work, new work started from `main`, and PR metadata drift
- streamline admin and frontend discovery internals without changing their public discovery behavior
- harden API and report access for production use with safer auth checks, private no-store responses, and explicit production-report enablement
- exclude private Wagtail pages from frontend discovery output
- add the authenticated `/unveil/api/v1/platform/` endpoint for runtime and dependency inventory diagnostics
- add the `/unveil/report/platform/` HTML report and wire it into the dashboard and report navigation

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Since 0.1.0a5

### Documentation And Workflow

- the project now ships a fuller MkDocs documentation site and keeps the README focused on package overview and quickstart
- contributor command guidance was tightened around the sandbox workflow, grouped `make help` output, and clearer ownership between contributor docs and agent docs
- agent workflow guidance now explicitly covers branch creation from `main` and PR title/summary drift checks

### Discovery And Reports

- backend and frontend discovery internals were simplified by inlining trivial helpers while preserving public behavior
- frontend discovery excludes private Wagtail pages and related private-derived example URLs
- report runner pause and cancel behavior was tightened so long-running report sessions stop and settle more predictably

### Security And Diagnostics

- JSON API and HTML report access paths now use stricter production-safe controls, including masked settings diagnostics, constant-time bearer-key checks, and private no-store cache headers
- a new platform API endpoint exposes runtime metadata and dependency inventory with warnings instead of hard failures when manifest metadata is incomplete
- a matching platform HTML report is available in the admin UI and linked from existing diagnostics surfaces

## Install

```bash
pip install wagtail-unveil==0.1.0a6
```
