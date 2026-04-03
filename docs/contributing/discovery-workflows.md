# Discovery Workflow Visual Reference

## Read This If...

Read this page if you want a visual companion to the discovery pipeline before or alongside the canonical architecture reference.

## Purpose

This document is a maintainer-facing visual companion to
[discovery-architecture.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/discovery-architecture.md).
Use this page to understand the shape of the discovery pipelines and where
classification, resolution, and final dataclass emission happen. Use the
architecture document for the authoritative rules, special cases, and
limitations behind each branch.

Primary implementation files:

- `wagtail_unveil/discovery/backend.py`
- `wagtail_unveil/discovery/backend_resolution.py`
- `wagtail_unveil/discovery/extensions.py`
- `wagtail_unveil/discovery/frontend.py`
- `wagtail_unveil/discovery/frontend_resolution.py`
- `wagtail_unveil/discovery/utils.py`
- `wagtail_unveil/settings.py`

## Shared Phase Model

Both discovery pipelines follow the same broad shape even though the concrete
sources and resolution steps differ.

```mermaid
flowchart TD
    A["Discover raw candidates"] --> B["Normalize route metadata"]
    B --> C["Classify testability and skip reason"]
    C --> D{"Needs concrete resolution?"}
    D -->|No| E["Emit final dataclass row"]
    D -->|Yes| F["Attempt safe concrete resolution"]
    F --> G{"Resolved?"}
    G -->|Yes| E
    G -->|No| H["Keep visible but mark untestable"]
    H --> E
```

Shared helper layer:

- `walk_patterns()` walks Django resolver trees and emits route metadata.
- `clean_regex_route()` converts regex-style route fragments into safer
  path-style placeholders where possible.
- `route_has_parameters()` and `route_contains_regex()` determine whether a
  route can be tested directly or needs later handling.
- `get_skip_url_prefixes()` can remove candidates before they become public
  output.

## Backend Workflow

`get_admin_urls()` in `wagtail_unveil/discovery/backend.py` orchestrates
admin URL discovery.

```mermaid
flowchart TD
    A["Root resolver URL patterns"] --> B["_discover_admin_routes()<br/>keep only admin/ routes"]
    B --> C["_normalize_admin_route()<br/>clean regex, drop unsafe regex, apply skip prefixes"]
    C --> D{"Normalized route kept?"}
    D -->|No| Z["Drop route from output"]
    D -->|Yes| E["_classify_admin_route()<br/>hard-coded non-testable names,<br/>docs/images readiness checks,<br/>mark parameterized routes for resolution"]
    E --> F["_iter_page_backed_admin_urls()<br/>expand safe wagtailadmin_pages routes<br/>into one row per concrete page type"]
    F --> G{"Page-backed rows emitted?"}
    G -->|Yes| H["resolve_parameterized_url_with_instance()<br/>per selected page instance"]
    H --> I{"Resolved and GET-compatible?"}
    I -->|Yes| J["Emit BackendURL<br/>testable, with resolved_route and page_type"]
    I -->|No| K["Emit BackendURL<br/>visible but untestable"]
    G -->|No| L{"Classification says<br/>should_resolve?"}
    L -->|No| M["_finalize_admin_route()"]
    L -->|Yes| N["resolve_parameterized_url()<br/>settings special-case, callback model inference,<br/>hook resolvers, reverse()"]
    N --> O{"Resolved?"}
    O -->|No| P["Mark skip_reason = URL requires parameters"]
    O -->|Yes| M
    P --> M
    M --> Q{"GET supported by callback?"}
    Q -->|No| R["Mark skip_reason = POST-only view<br/>or GET not supported"]
    Q -->|Yes| S["Keep testable state"]
    R --> T["Emit BackendURL"]
    S --> T
```

### Backend Resolution Branches

The generic parameter-resolution path in
`wagtail_unveil/discovery/backend_resolution.py` is itself a short strategy
pipeline:

```mermaid
flowchart TD
    A["Parameterized admin route"] --> B{"Namespace is wagtailsettings?"}
    B -->|Yes| C["_resolve_settings_url()"]
    B -->|No| D["_get_model_from_callback()"]
    D --> E{"Model inferred?"}
    E -->|Yes| F["_get_instance_for_model()"]
    E -->|No| G["No model-derived instance"]
    F --> H["AdminInstanceResolver hook pipeline"]
    G --> H
    H --> I{"Resolver selected instance<br/>or fail-closed outcome?"}
    I -->|Instance available| J["_reverse_with_instance()"]
    I -->|No instance| K["Resolution fails open<br/>route stays visible"]
    C --> L{"Resolved?"}
    J --> L
    L -->|Yes| M["resolved_route returned"]
    L -->|No| K
```

Maintainer-specific branches to keep in mind:

- Safe `wagtailadmin_pages` routes do not use the generic callback-model path
  first. They are expanded by page type through `_iter_page_backed_admin_urls()`.
- `add_subpage` uses compatible parent pages only, via
  `get_add_subpage_parent_page_instances_by_type()`.
- Hook resolvers from `get_registered_admin_instance_resolvers()` can either
  supply a fallback instance or override an earlier choice.
- Failed resolution does not remove the row. It only changes the emitted
  `BackendURL` to an untestable one with `skip_reason`.

## Frontend Workflow

`get_frontend_urls()` in `wagtail_unveil/discovery/frontend.py` merges
page-derived and resolver-derived candidates before classification.

```mermaid
flowchart TD
    A["get_frontend_urls()"] --> B["_discover_page_candidates()"]
    A --> C["_discover_resolver_candidates()"]

    B --> D["Iterate live specific pages"]
    D --> E{"Concrete non-base Page<br/>with usable page.url?"}
    E -->|No| X["Skip page candidate"]
    E -->|Yes| F["Convert absolute URL to path,<br/>apply skip prefixes,<br/>record site/default-site state"]
    F --> G["Emit base page candidate"]
    G --> H{"FormMixin?"}
    H -->|Yes| I["Add landing_page candidate<br/>requires POST"]
    H -->|No| J["Continue"]
    I --> J
    J --> K{"RoutablePageMixin?"}
    K -->|Yes| L["_discover_routable_page_candidates()"]
    K -->|No| M["Page candidate set complete"]
    L --> N["Join page path + sub-route,<br/>record has_parameters / contains_regex,<br/>attempt resolve_routable_page_url()"]
    N --> M

    C --> O["walk_patterns() over root resolver"]
    O --> P["clean_regex_route()"]
    P --> Q["Exclude admin/, wagtail_unveil namespace,<br/>skip prefixes on normalized route"]
    Q --> R["Detect supported Wagtail API find/detail routes"]
    R --> S["Optionally derive concrete resolved_url<br/>for supported detail endpoints"]

    M --> T["Candidate list combined"]
    S --> T
    T --> U["_classify_frontend_candidate()"]
    U --> V{"Cross-site page URL?"}
    V -->|Yes| W["Mark untestable:<br/>Belongs to non-default site host"]
    V -->|No| Y{"Requires POST?"}
    Y -->|Yes| AA["Mark untestable:<br/>Requires POST submission"]
    Y -->|No| AB{"Requires query params<br/>without defaults?"}
    AB -->|Yes| AC["Mark untestable:<br/>Requires query parameters"]
    AB -->|No| AD{"Has parameters<br/>without resolved_url?"}
    AD -->|Yes| AE["Mark untestable:<br/>URL requires parameters"]
    AD -->|No| AF{"Contains regex?"}
    AF -->|Yes| AG["Mark untestable:<br/>URL contains regex patterns"]
    AF -->|No| AH["Remain testable"]
    W --> AI["_build_frontend_url()"]
    AA --> AI
    AC --> AI
    AE --> AI
    AG --> AI
    AH --> AI
    AI --> AJ["Emit FrontendURL"]
```

### Frontend Resolution Notes

- Page-derived candidates can produce multiple rows for a single page:
  base page, form landing page, and routable sub-routes.
- `WAGTAIL_UNVEIL_PAGES_PER_TYPE` limits page-derived selection inline during
  `_discover_page_candidates()` but does not affect resolver-derived URLs.
- `resolve_routable_page_url()` only resolves a narrow safe subset of
  single-parameter path-style routable sub-routes.
- `get_wagtail_api_detail_resolved_url()` only resolves supported Wagtail API
  detail endpoints when a representative object exists.
- Frontend discovery keeps many untestable URLs visible by design so reports
  still show the full reachable surface area.

## Decision Points That Make URLs Untestable

Discovery and testability are intentionally separate in this package. The main
reasons a discovered URL stays visible but is not directly testable are:

- backend hard-coded non-testable admin names such as logout or import actions
- backend serve-readiness checks for document and image endpoints
- backend parameterized routes that cannot produce a concrete `resolved_route`
- backend callbacks that do not support `GET`
- frontend form landing pages that require `POST`
- frontend query-driven resolver routes such as supported Wagtail API `find`
  endpoints
- frontend routable or resolver routes that still require path parameters
- frontend routes that still contain regex constructs after normalization
- page URLs that belong to a non-default Wagtail `Site`

## Where To Change Behavior

Start with the visual flow above, then use the canonical deep reference:
[discovery-architecture.md](https://github.com/nm-packages/wagtail-unveil/blob/main/docs/contributing/discovery-architecture.md).

The main implementation entry points are:

- `wagtail_unveil/discovery/backend.py` for admin orchestration and final
  `BackendURL` emission
- `wagtail_unveil/discovery/backend_resolution.py` for parameterized admin
  resolution strategies
- `wagtail_unveil/discovery/extensions.py` for admin instance resolver hooks
- `wagtail_unveil/discovery/frontend.py` for frontend candidate discovery,
  classification, and final `FrontendURL` emission
- `wagtail_unveil/discovery/frontend_resolution.py` for routable and API
  concrete URL inference
- `wagtail_unveil/discovery/utils.py` for shared resolver walking and route
  normalization helpers
- `wagtail_unveil/settings.py` for discovery-affecting settings such as page
  limits and skip prefixes
