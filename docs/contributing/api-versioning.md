# API Versioning and Lifecycle Guide

## Read This If...

Read this page if you are changing JSON API behavior and need the canonical policy for deciding whether a new API version is required.

This is the canonical contributor guide for JSON API versioning and lifecycle policy in `wagtail-unveil`.
Use this document when deciding whether a change requires a new API version and when implementing/deprecating versions.

## Purpose And Scope

Audience:

- maintainers and contributors changing JSON API behavior
- reviewers validating whether changes are backward-compatible

Scope:

- JSON API contract versioning only (`/unveil/api/vN/...`)
- lifecycle states and timelines for active/deprecated versions
- implementation workflow for introducing new versions

Out of scope:

- package release versioning (`package_version`)
- discovery internals (see [discovery-architecture.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/discovery-architecture.md))

## Why Explicit Versioning

The package serves API clients that may not upgrade in lockstep with package releases.
Explicit API versions let us:

- preserve existing client behavior under stable endpoints
- ship breaking improvements in parallel under a new version
- provide predictable deprecation windows before removal

This policy prioritizes contract stability over "silent replacement" of behavior.

## Core Concepts

- `stable`: supported default contract; no scheduled removal date
- `deprecated`: still served, but scheduled for retirement with communicated dates
- `sunset`: date after which the deprecated version may be removed
- `removed`: endpoint/version no longer served

Contract version vs package version:

- `metadata.api_version` identifies the API contract (`v1`, `v2`, ...)
- `metadata.package_version` identifies the installed `wagtail-unveil` release

Breaking change (for this project):

- any change that can make a compliant client fail, mis-parse, or change behavior unexpectedly without client code changes

## Default Lifecycle Policy

Default policy is normative unless an exception is documented.

- Deprecation window: **180 days** from deprecation notice date
- A version can be removed only when:
  - a successor version is already available, and
  - the deprecation window has elapsed
  - removal is optional after the window

Exception policy (urgent/security):

- maintainers may shorten the window only with explicit rationale
- rationale must be recorded in release notes/changelog
- replacement guidance for clients must be included in the same release communication

## Decision Matrix: Do We Need a New API Version?

| Change type | Example | Breaking? | New version required? | Notes |
|---|---|---:|---:|---|
| Add optional response field | Add `metadata.request_id` | No | No | Existing clients can ignore unknown fields. |
| Add optional metadata object | Add `metadata.api_lifecycle` | No | No | Must be additive and optional. |
| Rename response field | `name` -> `url_name` | Yes | Yes | Breaks clients expecting old key. |
| Remove response field | Remove `skip_reason` | Yes | Yes | Breaks clients relying on field presence. |
| Change field type/format | `count` int -> string, date format changes | Yes | Yes | Parser/validation breaks. |
| Change semantics of existing field | `source` value meaning changes | Yes | Yes | Behavior changes without schema change are still breaking. |
| Change auth requirements/status semantics | Previously 403 now 401/redirect | Yes | Yes | Client auth/error handling can break. |
| Add new endpoint | Add `api/v1/health/` | No* | No* | *No version bump unless existing contract behavior changes. |
| Reorder arrays where order is meaningful | Stable sorted output -> unsorted | Yes | Yes | Treat order as contract when documented or relied on. |

If unsure, treat the change as breaking and open a versioning review in PR notes.

## Version Bump Workflow

When a new version is required (for example `v2`):

1. Add contract entry in `wagtail_unveil/api_contract.py`
- Add `APIVersionContract` entry to `API_VERSION_REGISTRY` with:
  - `version`
  - `status`
  - `deprecated_on`
  - `sunset_on`
  - versioned backend/frontend path and URL names
- Keep old versions in registry during deprecation window.

2. Confirm dynamic routing in `wagtail_unveil/urls.py`
- Ensure both backend and frontend routes are generated for new version.
- Confirm old version routes still resolve.

3. Implement version-specific behavior in `wagtail_unveil/views.py`
- Extend version dispatch/serializer logic for the new version.
- Keep previous version behavior intact.
- Ensure metadata includes correct `api_version` + `api_lifecycle`.

4. Validate report target behavior
- Reports should point to `get_latest_stable_api_contract()` target.
- Confirm this matches desired default version policy.

5. Validate lifecycle headers
- Deprecated versions must emit:
  - `Deprecation: true`
  - `Sunset` header when sunset date exists.

6. Keep previous version live
- Do not remove previous version endpoints until deprecation window has elapsed and communication is complete.

## Testing Requirements For New Versions

Required coverage when adding/changing versions:

- registry validation and latest stable selection
- route resolution for new version names/paths
- metadata shape and values:
  - `api_version`
  - `api_lifecycle`
- deprecation header behavior (`Deprecation`, `Sunset`)
- report `data-api-url` targets latest stable version
- backward compatibility tests for previous version

Verification commands:

```bash
make lint
make coverage
```

## Release And Communication Checklist

For every version introduction/deprecation update:

1. Update:
- `README.md`
- `docs/index.md`
- `AGENTS.md`
- `wagtail_unveil/AGENTS.md`

2. Release notes/changelog:
- deprecation date
- sunset date
- target replacement version
- migration guidance

3. Migration note template:

```md
### API Deprecation Notice

- Deprecated version: `vN`
- Deprecated on: `YYYY-MM-DD`
- Sunset on: `YYYY-MM-DD`
- Replacement: `vN+1`

#### Required Client Actions

1. Switch endpoint paths from `/unveil/api/vN/...` to `/unveil/api/vN+1/...`.
2. Update response parsing for renamed/removed/changed fields.
3. Verify error/auth handling against `vN+1` semantics.
```

## Worked Examples

### Example A: Additive Metadata Field (No New Version)

Change:

- add `metadata.request_id` for traceability

Decision:

- additive optional field, no change to existing keys/types/semantics
- **no new API version required**

Implementation:

- update existing version serializer/metadata builder
- add tests confirming old fields unchanged and new field present

### Example B: Rename Response Key (New Version Required)

Change:

- rename `resolved_route` to `resolved_url`

Decision:

- key rename is breaking
- **new API version required** (for example `v2`)

Implementation outline:

1. Add `v2` entry in `API_VERSION_REGISTRY`.
2. Keep `v1` active and mark `v1` as `deprecated` with dates.
3. Implement `v2` serializer with renamed key.
4. Keep `v1` serializer unchanged.
5. Add tests for coexistence (`v1` old key, `v2` new key).
6. Publish deprecation and sunset dates in release notes.
