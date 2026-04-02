# wagtail-unveil 0.1.0a5

Fifth public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Full Change Summary

- surface concrete backend page-admin routes per discovered page type so more page-specific admin URLs are visible and testable
- cache page-type admin expansion work per discovery run to avoid repeating the same compatibility checks
- normalize frontend skip prefixes for django-admin routes so exclusions apply more consistently during discovery
- remove redundant `wagtailadmin_pages` hook resolvers after the page-type route expansion work
- add discovery workflow reference documentation to explain the backend and frontend pipelines more clearly
- clarify the discovery docs and tidy supporting report helpers

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Since 0.1.0a4

### Admin Discovery

- backend discovery now emits compatible page-admin routes for each concrete page type present in the database instead of only listing generic patterns
- repeated page-type expansion work is cached inside a discovery run, which keeps the broader route surface practical to compute
- redundant hook-based page resolver logic was removed now that page-type expansion covers the supported cases directly

### Frontend Discovery

- skip-prefix handling is stricter about normalizing django-admin-style prefixes before matching, which makes exclusions more predictable

### Documentation And Maintenance

- new workflow diagrams document the backend and frontend discovery pipeline for contributors
- supporting docs and helper cleanup keep the codebase aligned with the project’s flow-first conventions

## Install

```bash
pip install wagtail-unveil==0.1.0a5
```
