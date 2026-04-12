# wagtail-unveil 0.1.0a7

Seventh public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Full Change Summary

- add inline Markdown export and copy support to the platform HTML report so the current runtime and dependency inventory can be shared from the admin UI
- teach the platform dependency inventory to follow relative `-r other-file.txt` includes in requirements-style manifests
- include shared or base requirements files in `/unveil/api/v1/platform/` output when a discovered manifest references them via `-r`

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Since 0.1.0a6

### Platform Report

- the platform HTML report can now render a raw Markdown summary of the current runtime and dependency inventory
- the generated Markdown can be copied directly from the report UI, and it includes latest-version comparison data when those browser-side PyPI lookups are available

### Platform Dependency Inventory

- requirements-style manifests can now pull in relative include files through `-r other-file.txt`
- dependency inventory output now reflects shared/base requirement files referenced from the primary manifest, which makes `/unveil/api/v1/platform/` more representative of real project dependency layouts

## Install

```bash
pip install wagtail-unveil==0.1.0a7
```
