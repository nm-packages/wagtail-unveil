# API Reference

wagtail-unveil exposes a versioned JSON API for querying discovered URLs programmatically.

## In This Section

- [Endpoints](endpoints.md) — Authentication, endpoint URLs, filters, and response shape

## Quick Reference

```bash
# Backend (admin) URLs
curl -H "Authorization: Bearer your-key" http://localhost:8000/unveil/api/v1/backend-urls/

# Frontend URLs
curl -H "Authorization: Bearer your-key" http://localhost:8000/unveil/api/v1/frontend-urls/

# Platform runtime and dependency inventory
curl -H "Authorization: Bearer your-key" http://localhost:8000/unveil/api/v1/platform/
```

## Related

- [Getting Started](../getting-started/installation.md) — Set up the API key
- [Configuration](../configuration/settings-reference.md#wagtail_unveil_api_key) — API key settings
- [Features](../features/index.md) — HTML report counterparts, including the platform report
- [Documentation Index](../index.md) — Back to overview
