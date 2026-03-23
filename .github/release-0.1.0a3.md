# wagtail-unveil 0.1.0a3

Third public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Highlights

- add hook-based admin instance resolver extensions for developer-installed Wagtail admin packages
- document the custom resolver pattern with a `wagtail-modeladmin` recipe and sandbox example
- split admin and frontend parameter resolution into dedicated modules with broader automated coverage
- harden third-party resolver extension failures so bad hook output is skipped without taking discovery down

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Install

```bash
pip install wagtail-unveil==0.1.0a3
```
