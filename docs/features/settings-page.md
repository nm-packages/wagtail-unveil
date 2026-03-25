# Settings Page

The settings page is a server-rendered diagnostic view showing the effective wagtail-unveil configuration and related runtime information.

## Access

Visit `/unveil/report/settings/` while logged in as a superuser with `DEBUG=True`.

![Settings Page](https://raw.githubusercontent.com/nm-packages/wagtail-unveil/main/docs/features/settings_pane.jpg)

You can also reach it from the Wagtail admin dashboard panel.

## What It Shows

**Configuration values** — the current raw and effective values for:

- `WAGTAIL_UNVEIL_API_KEY` — displayed in full for superusers while `DEBUG=True`, to support local debugging
- `WAGTAIL_UNVEIL_PAGES_PER_TYPE`
- `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`

Each value also shows its source: environment variable, Django settings, or package default.

**Runtime diagnostics:**

- `DEBUG` status
- HTML report access (superuser + DEBUG check)
- Session API access
- Bearer auth configuration

**Package information:**

- Package version and Python/Django/Wagtail runtime versions
- Resolved Unveil API and report URLs as registered in the URL config

## Related

- [Backend URLs Report](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/backend-urls-report.md) — Test admin URLs
- [Frontend URLs Report](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/frontend-urls-report.md) — Test frontend URLs
- [Configuration](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/configuration/settings-reference.md) — Change the effective settings
- [Features Index](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/index.md) — Back to section overview
