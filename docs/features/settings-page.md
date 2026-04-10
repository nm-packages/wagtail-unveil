# Settings Page

The settings page is a server-rendered diagnostic view showing the effective wagtail-unveil configuration and related runtime information.

## Access

Visit `/unveil/report/settings/` while logged in as a superuser with `DEBUG=True`, or enable `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS` for production access.

![Settings Page](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/settings_pane.jpg)

You can also reach it from the Wagtail admin dashboard panel.

## What It Shows

**Configuration values** — the current raw and effective values for:

- `WAGTAIL_UNVEIL_API_KEY` — shown in masked form so the secret is never rendered in full
- `WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS`
- `WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE`
- `WAGTAIL_UNVEIL_PAGES_PER_TYPE`
- `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

Each value also shows its source: environment variable, Django settings, or package default.

**Runtime diagnostics:**

- `DEBUG` status
- HTML report access
- Superuser session API access
- Bearer API auth

**Package information:**

- Package version and Python/Django/Wagtail runtime versions
- Resolved Unveil API and report URLs as registered in the URL config, including the platform runtime API

## Related

- [Backend URLs Report](backend-urls-report.md) — Test admin URLs
- [Frontend URLs Report](frontend-urls-report.md) — Test frontend URLs
- [Configuration](../configuration/settings-reference.md) — Change the effective settings
- [Features Index](index.md) — Back to section overview
