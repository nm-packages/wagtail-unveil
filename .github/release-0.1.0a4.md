# Release 0.1.0a4

Fourth public alpha release for `wagtail-unveil`.

This release is still intended for early adopters and real-world testing rather than mainstream production use. Expect ongoing refinement and some breaking changes before the first stable release.

## Full Change Summary

- resolve more GET-safe Wagtail admin routes, including a safe allowlisted subset of page admin views
- resolve `add_subpage` only when a compatible parent page instance can be identified
- resolve GET-safe workflow task routes so more workflow-backed admin URLs can be tested concretely
- expose backend resolution helpers for custom admin resolver extensions and targeted test patching
- rename and promote shared parameter-resolution helpers for cross-module reuse
- reorder backend discovery, backend resolution, frontend discovery, and settings helpers around the actual execution flow
- clarify view helper organization and unused version-parameter handling
- expand and reorganize the automated test suite into feature-based subpackages
- add broader coverage for admin discovery, frontend discovery, runtime settings, diagnostics, and report/API views
- remove the docs-check automation and tighten contributor guidance around keeping command docs aligned with `Makefile`

## Audience

- developers evaluating `wagtail-unveil` on real Wagtail projects
- teams willing to test early and share feedback on gaps, edge cases, and DX

## Known expectations for this alpha

- behavior and documentation may still change before a stable release
- package interfaces should be treated as provisional
- feedback from real projects will shape the next pre-release iterations

## Since 0.1.0a3

### Admin Discovery

- more parameterized Wagtail admin routes now resolve to concrete GET-safe URLs when representative objects can be found
- page admin route handling is stricter about only resolving routes that are safe and compatible for the discovered page instance
- workflow task routes are now included in the same resolution pipeline as other safe admin URLs

### Discovery Internals

- backend and frontend resolution helpers are easier to import and patch in tests and extension code
- helper ordering across discovery modules now follows the runtime pipeline more closely, which makes the codebase easier to navigate
- settings and views modules received the same organization cleanup to match the repo's flow-first conventions

### Tests And Maintenance

- the root test suite was reorganized into feature-based packages for API, discovery, settings, sandbox, and views coverage
- report view tests were tidied up to remove duplicate panel assertions while keeping coverage strong
- contributor guidance now points more clearly to the `Makefile` as the canonical workflow surface for command docs

## Install

```bash
pip install wagtail-unveil==0.1.0a4
```
