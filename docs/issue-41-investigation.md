# Issue #41 Investigation: Wagtail Subdomains / Multisite

Issue link: <https://github.com/nm-packages/wagtail-unveil/issues/41>

## Problem statement

`get_frontend_urls()` reads `page.url` and then keeps only `urlparse(page.url).path`.
In multisite setups, Wagtail returns absolute URLs (for example `http://sub.localhost/about/`) for pages on non-default sites.
Dropping host information means those pages can appear testable in reports even though testing runs on the current host only.

## Reproduction summary

1. Configure two Wagtail `Site` records:
   - default: `localhost`
   - non-default: `sub.localhost`
2. Add a live page under the non-default site's root page.
3. Run `get_frontend_urls()`.
4. Observe that the page is discovered as a path (`/subsite-about/`) but belongs to a different host.

## Decision and implemented scope

- Keep frontend API `url` values path-based (no breaking API/report column change).
- Continue discovering non-default-site pages.
- Mark non-default-site page candidates as untestable with:
  - `Belongs to non-default site host: <hostname>`
- Add tests that create a second site and verify discovery + testability behavior.
- Add sandbox sample data support for a non-default `sub.localhost` site fixture.

## API/report impact

- No new API fields were added.
- Existing frontend entries remain in results.
- Some page URLs that previously appeared testable are now intentionally untestable when they belong to a non-default host.
