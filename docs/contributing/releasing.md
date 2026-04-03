# Releasing wagtail-unveil

## Read This If...

Read this page if you are preparing or publishing a release and need the canonical maintainer runbook for the GitHub Release to PyPI workflow.

This is the maintainer runbook for publishing package releases to PyPI via GitHub Actions.

## Release Workflow

- Workflow file: `.github/workflows/release.yml`
- Trigger: GitHub Release event `published`
- Authentication: PyPI Trusted Publisher (OIDC), no API token secret

The release workflow:

1. validates GitHub release tag (`vX.Y.Z` or pre-release like `vX.Y.Zrc1`) matches `project.version` in `pyproject.toml`
2. validates the tagged commit is contained in `origin/main`
3. builds `sdist` + `wheel` with `uv build`
4. runs `twine check` on built artifacts
5. publishes artifacts to PyPI using `pypa/gh-action-pypi-publish`

## One-Time Setup (PyPI Trusted Publisher)

In the PyPI project settings for `wagtail-unveil`, add a Trusted Publisher with:

- Owner or organization: `nm-packages`
- Repository: `wagtail-unveil`
- Workflow: `release.yml`
- Environment: unset (unless intentionally adding GitHub Environments later)

The GitHub repository and workflow identity must match exactly, or publish will fail.

## Maintainer Release Steps

1. Update `version` in `pyproject.toml` to the intended release version.
2. Update `CHANGELOG.md` with a concise entry for the new release and any migration or alpha-status notes worth calling out.
3. Merge the release-prep changes to `main`.
4. Ensure normal CI on `main` is green (`CI` workflow).
5. Create a GitHub Release with a tag that matches the package version with `v` prefix.
6. Use the matching `.github/release-*.md` file or the `CHANGELOG.md` entry as the GitHub Release body.
7. Publish the GitHub Release.
8. Confirm `.github/workflows/release.yml` succeeds and the version appears on PyPI.

For local sandbox/test command workflows before a release, use:
- [`development.md`](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/development.md) for canonical developer workflow and quickstart commands
- [`../../AGENTS.md`](https://github.com/nm-packages/wagtail-unveil/blob/main/AGENTS.md) for canonical contributor command/reference guidance

Examples:

- `pyproject.toml` version `0.3.0` => GitHub tag `v0.3.0`, release title `0.3.0` (or `Release 0.3.0`)
- `pyproject.toml` version `0.4.0rc1` => GitHub tag `v0.4.0rc1`, release title `0.4.0rc1` (or `Release 0.4.0rc1`)

## Local Preflight (Optional but Recommended)

Run these before creating the GitHub Release:

```bash
uv build --sdist --wheel --out-dir /tmp/wagtail-unveil-dist-check
uvx twine check /tmp/wagtail-unveil-dist-check/*
```

## Failure Modes and Troubleshooting

- Tag/version mismatch:
  - Symptom: workflow fails in "Validate release tag matches package version"
  - Fix: align GitHub tag with `pyproject.toml` version and republish release
- Tag commit not on main:
  - Symptom: workflow fails in "Validate release commit is on main"
  - Fix: retag a commit that is on `main`
- Trusted Publisher identity mismatch:
  - Symptom: PyPI publish step reports authorization/trust failure
  - Fix: verify owner/repo/workflow values in PyPI Trusted Publisher settings
- Duplicate version:
  - Symptom: publish step fails because version already exists on PyPI
  - Fix: bump `pyproject.toml` version and publish a new tag/release
