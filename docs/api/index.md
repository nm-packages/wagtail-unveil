# API Reference

wagtail-unveil exposes a versioned JSON API for querying discovered URLs programmatically.

## In This Section

- [Endpoints](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/api/endpoints.md) — Authentication, endpoint URLs, filters, and response shape

## Quick Reference

```bash
# Backend (admin) URLs
curl -H "Authorization: Bearer your-key" http://localhost:8000/unveil/api/v1/backend-urls/

# Frontend URLs
curl -H "Authorization: Bearer your-key" http://localhost:8000/unveil/api/v1/frontend-urls/
```

## Related

- [Getting Started](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/getting-started/installation.md) — Set up the API key
- [Configuration](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/configuration/settings-reference.md#wagtail_unveil_api_key) — API key settings
- [Features](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/features/index.md) — HTML report counterparts
- [Documentation Index](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/index.md) — Back to overview
