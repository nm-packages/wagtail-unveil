# Platform Report

The platform report displays runtime versions, dependency-manifest details, Python dependency inventory, warnings, and response metadata from the platform endpoint in a browser-friendly table layout.

## Access

Visit `/unveil/report/platform/` while logged in as a superuser with `DEBUG=True`.

You can also reach it from the Wagtail admin dashboard panel.

## Features

- **Runtime overview** — shows Python, Django, and Wagtail versions for the current process
- **Dependency manifest diagnostics** — shows the configured manifest path and detected format
- **Warnings section** — surfaces manifest parsing, access, or configuration warnings without failing the page
- **Dependency inventory table** — lists declared Python packages with specifier, installed version, installed state, source kind, and source name
- **Sortable dependency columns** — sort dependency rows by Name, Source Kind, and Source Name
- **Response metadata** — shows API version, lifecycle status, generation timestamp, and package version
- **Uses the live platform endpoint** — the page fetches the same versioned platform JSON used for API clients, using the configured Bearer token behind the report page

## Notes

- The underlying platform endpoint remains Bearer-token only, even in local `DEBUG=True` development.
- The report is intended for local or trusted superuser debugging, and is only available when `DEBUG=True`.
- To include dependency inventory data, set [`WAGTAIL_UNVEIL_PLATFORM_DEPENDENCY_FILE`](../configuration/settings-reference.md#wagtail_unveil_platform_dependency_file).

## Related

- [Settings Page](settings-page.md) — View the effective platform-related settings and resolved report/API URLs
- [API Reference](../api/endpoints.md#platform-runtime-endpoint) — Query the same platform payload directly as JSON
- [Dashboard Panel](dashboard-panel.md) — Open the report from the Wagtail admin home page
- [Features Index](index.md) — Back to section overview
