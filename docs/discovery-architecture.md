# Discovery and Resolution Architecture

## Purpose

This document explains how `wagtail_unveil` discovers URLs, normalizes route strings, resolves parameterized admin routes, and classifies URLs as testable or untestable. It is intended for contributors and coding agents working on discovery behavior.

Primary implementation files:

- `wagtail_unveil/discovery/backend.py`
- `wagtail_unveil/discovery/frontend.py`
- `wagtail_unveil/discovery/utils.py`
- `wagtail_unveil/settings.py`

## Shared Discovery Building Blocks

Two helpers underpin both admin and frontend discovery:

- `walk_patterns(patterns, prefix="", namespace="")` recursively walks Django `URLResolver` and `URLPattern` objects and yields `(route, name, namespace, callback)` tuples.
- `clean_regex_route(route)` removes `^` and `$` anchors and converts named regex groups such as `(?P<pk>...)` into path-style placeholders such as `<pk>`.

Normalization is intentionally partial. Some routes still contain regex constructs after cleanup, which means they may be discovered but remain untestable, or in the admin case may be skipped entirely if they still look unsafe for direct testing.

## Admin Discovery Flow

`get_admin_urls()` in `wagtail_unveil/discovery/backend.py` follows this sequence:

1. Walk the root URL resolver with `walk_patterns()`.
2. Keep only routes whose raw route string starts with `admin/`.
3. Normalize the route with `clean_regex_route()`.
4. Drop routes that still contain problematic regex metacharacters after cleanup, such as catch-all patterns.
5. Apply `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`.
6. Mark whether the route still has path parameters by checking for `<...>` placeholders.
7. Apply hard-coded non-testable name rules.
8. Check whether related serve URLs are registered for document and image URLs that depend on them.
9. Attempt to resolve parameterized URLs to a concrete path.
10. Emit a `BackendURL` dataclass with discovery and testability metadata.

Current hard-coded non-testable names:

- `wagtailadmin_logout` -> `POST-only view`
- `wagtailadmin_block_preview` -> `POST-only view`
- `process_import` -> `POST-only view`
- `lock` -> `POST-only view`
- `unlock` -> `POST-only view`
- `wagtailadmin_error_test` -> `Intentional error endpoint`
- `find` -> `Requires query parameters`

There are also namespace-specific readiness checks:

- document admin URLs in `wagtaildocs`, `wagtaildocs_chooser`, and `wagtailadmin_api:documents` are marked untestable if `wagtaildocs_serve` is not registered
- image URL generator endpoints in `wagtailimages` are marked untestable if `wagtailimages_serve` is not registered

## Parameter Resolution Strategy

`_resolve_parameterized_url()` attempts to turn a parameterized admin route into a real path that can be tested. It now follows an explicit strategy pipeline:

1. If the namespace is `wagtailsettings`, delegate to `_resolve_settings_url()` and stop there.
2. Try to infer a model from callback metadata via `_get_model_from_callback()`.
3. If a callback model is found, select a representative instance with `_get_instance_for_model()`.
4. If no callback-backed instance is available, fall back to parsing modeladmin-style URL names such as `{app}_{model}_modeladmin_{action}` and again select an instance with `_get_instance_for_model()`.
5. Apply namespace-specific instance rules from `_get_namespace_specific_instance()`:
   - `wagtailforms` falls back to the first live form page instance when no earlier instance exists
   - `wagtailadmin_workflows` usage views override earlier model-derived instances with the first `Workflow` instance, and fail closed if no workflow exists
6. Reverse the URL with `_reverse_with_instance()` using the selected instance.
7. If no instance can be selected, keep the route visible but untestable.

`_get_model_from_callback()` still checks callback init kwargs first, then `view_class.model`, then cached-property and MRO-based variants of `model`. For treebeard-backed models, `_get_instance_for_model()` excludes the root node (`depth=1`) before selecting the first instance.

Internal resolution returns a `_ParameterizedURLResolution` object with `resolved_route`, `resolved`, `method`, `detail`, and `attempts`. This metadata is internal only. It exists to make the fallback order and failure path easier to debug and test. Public JSON responses still expose only the existing `BackendURL` fields.

Resolved URLs are stored in `resolved_route` on `BackendURL`. If reversal fails or no suitable instance exists, the parameterized URL remains in the results but is marked untestable with `URL requires parameters`. Namespace-specific overrides can invalidate an earlier candidate instance when the route requires a different model type.

### Settings Resolution Nuances

`_resolve_settings_url()` handles `wagtailsettings` routes separately because those routes use keyword arguments instead of positional arguments.

- It iterates over registered settings models from the Wagtail settings registry.
- It fills `app_name` and `model_name` from model metadata.
- For routes containing `<int:pk>`:
  - `BaseSiteSetting` URLs use `instance.site_id`
  - `BaseGenericSetting` URLs use `instance.pk`
- `preview_on_edit` is only considered when previewable settings support is available and the model subclasses `PreviewableMixin`.
- It records whether resolution failed because no settings instances existed or because reversal failed for every registered model.

This logic exists to support the currently targeted Wagtail versions, including differences around previewable settings URLs and how the `pk` parameter is interpreted.

## Frontend Discovery Flow

`get_frontend_urls()` combines two sources:

- page-derived URLs from `_get_page_urls()`
- resolver-derived non-admin URLs from `_get_resolver_frontend_urls()`

The combined return value is a flat list of `FrontendURL` dataclass instances.

## Frontend Page Discovery

`_get_page_urls()` builds page-derived frontend entries in this order:

1. Iterate `Page.objects.live().specific()`.
2. Skip the base `Page` type.
3. Read `page.url` defensively so pages that error during URL generation do not break discovery.
4. Convert absolute page URLs to path-only values via `urlparse()`.
5. Apply `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`.
6. Emit one base page entry for the page URL.
7. If the page is a `FormMixin` subclass, add a second entry for the landing page and mark it untestable with `Requires POST submission`.
8. If the page is a `RoutablePageMixin` subclass, add sub-route entries from `_get_routable_sub_urls()`.
9. After collecting all page entries, apply `WAGTAIL_UNVEIL_PAGES_PER_TYPE` by grouping on `(page_type, page_title)` so each selected page keeps all of its related entries.

`WAGTAIL_UNVEIL_PAGES_PER_TYPE` affects page-derived URLs only. Resolver-derived frontend URLs are not limited by that setting.

## Routable Page Special Cases

`_get_routable_sub_urls()` discovers routes defined with `RoutablePageMixin.get_subpage_urls()` and handles them as follows:

- use `pattern.pattern._route` when available
- otherwise fall back to `pattern.pattern._regex` plus `clean_regex_route()`
- skip the empty index route so the base page URL is not duplicated
- construct a full URL by joining the page path and sub-route
- apply skip prefixes to the full URL
- mark routes containing `<...>` placeholders as untestable with `URL requires parameters`
- keep static sub-routes testable

This means routable pages contribute both their base page URL and any additional sub-routes, but parameterized sub-routes are represented rather than auto-resolved.

## Frontend Resolver Discovery

`_get_resolver_frontend_urls()` walks the root resolver and emits non-admin routes with these exclusions and rules:

1. Walk all URL patterns with `walk_patterns()`.
2. Exclude routes under `admin/`.
3. Exclude routes under `django-admin/`.
4. Exclude routes whose namespace is `wagtail_unveil`.
5. Apply `WAGTAIL_UNVEIL_SKIP_URL_PREFIXES`.
6. Normalize the route with `clean_regex_route()`.
7. Mark routes containing `<...>` placeholders as untestable with `URL requires parameters`.
8. Otherwise, if the normalized route still contains `(`, mark it untestable with `URL contains regex patterns`.
9. Emit a `FrontendURL`.

Resolver-derived URLs are still included when untestable so they remain visible in reports and API responses.

## Testability Classification

Discovery and testability are separate concepts in this package. A URL can be discovered successfully and still be intentionally marked untestable. Untestable URLs remain in the output with a `skip_reason` so contributors can see why they are excluded from direct GET testing.

Current skip reasons used by the discovery layer:

- `POST-only view`
- `Intentional error endpoint`
- `Requires query parameters`
- `Requires path("documents/", include(wagtaildocs_urls)) in URLconf`
- `Requires path("images/", include(wagtailimages_urls)) in URLconf`
- `URL requires parameters`
- `URL contains regex patterns`
- `Requires POST submission`

## Known Limitations and Intentional Exclusions

Current intentional boundaries:

- admin routes that still contain unsafe regex constructs after cleanup are skipped entirely
- unresolved parameterized admin URLs remain visible but untestable
- multi-parameter admin routes are usually not auto-resolvable
- frontend resolver routes with regex constructs are discovered but not directly testable
- parameterized routable sub-routes are discovered but not directly testable
- form landing pages are represented but are not GET-testable
- package routes in the `wagtail_unveil` namespace are intentionally excluded from frontend discovery
- configured skip prefixes can remove page, admin, resolver, and routable URLs from discovery output

### Where To Change This Behavior

If you need to change discovery behavior, start in these files:

- `wagtail_unveil/discovery/backend.py`
- `wagtail_unveil/discovery/frontend.py`
- `wagtail_unveil/discovery/utils.py`
- `wagtail_unveil/settings.py`

Then verify the intended behavior in:

- `tests/test_admin_urls.py`
- `tests/test_frontend_urls.py`
- `tests/test_settings.py`

## Code And Test Map

The main behavior is currently implemented in code and verified in tests:

- `wagtail_unveil/discovery/backend.py` and `tests/test_admin_urls.py`
- `wagtail_unveil/discovery/frontend.py` and `tests/test_frontend_urls.py`
- `wagtail_unveil/settings.py` and `tests/test_settings.py`

Use the tests as verification of current behavior, not as the primary contributor-facing explanation of how discovery works. This document should be the first place a contributor reads when changing discovery and resolution logic.
