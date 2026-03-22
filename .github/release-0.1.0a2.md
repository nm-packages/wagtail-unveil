# wagtail-unveil 0.1.0a2

Second public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Highlights

- improve frontend URL discovery for `RoutablePageMixin` sub-routes, including better concrete URL resolution
- surface query-driven Wagtail API `find/` routes in frontend discovery with clearer non-testable handling
- make Wagtail admin API detail URLs testable when a representative object can be resolved
- keep POST-only reorder routes visible in backend discovery while marking them untestable
- refresh docs and release metadata for the current alpha

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Install

```bash
pip install wagtail-unveil==0.1.0a2
```
