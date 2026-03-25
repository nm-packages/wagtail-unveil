# wagtail-unveil 0.1.0a4

Fourth public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Highlights

- resolve more GET-safe Wagtail admin routes, including compatible page admin views and workflow task URLs
- expose and reorganize resolution helpers for custom admin resolver extensions and patch-based testing
- expand automated coverage across discovery, settings, and report/API views while tightening contributor workflow docs

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Install

```bash
pip install wagtail-unveil==0.1.0a4
```
