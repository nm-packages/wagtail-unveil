# Changelog

All notable changes to `wagtail-unveil` are documented in this file.

## 0.1.0a2 - 2026-03-22

Second public alpha release.

This alpha continues to target early adopters and real-world testing. Package behavior and documentation should still be treated as provisional before the first stable release.

### Highlights

- improved frontend URL discovery for `RoutablePageMixin` sub-routes, including better concrete URL resolution and clearer handling for regex-backed routes
- surfaced query-driven Wagtail API `find/` routes in frontend discovery without treating them as directly testable GET URLs
- made Wagtail admin API detail URLs testable when a representative object can be resolved
- marked POST-only reorder routes as visible but untestable in backend discovery
- refreshed documentation and package presentation for the current alpha release

## 0.1.0a1 - 2026-03-02

First public alpha release.

This alpha introduced the initial public package surface for early adopters and feedback.

### Highlights

- discovered frontend and Wagtail admin URLs from a single reusable package
- exposed authenticated JSON API endpoints for inspecting discovered URLs
- added Wagtail admin reports for backend URLs, frontend URLs, and effective settings
- included a dashboard panel for quick access to the available diagnostics
