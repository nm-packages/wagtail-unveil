import re
from dataclasses import dataclass

from django.urls import get_resolver

from wagtail_unveil.discovery.backend_resolution import resolve_parameterized_url
from wagtail_unveil.discovery.utils import clean_regex_route, route_has_parameters, walk_patterns
from wagtail_unveil.settings import get_skip_url_prefixes


def _is_url_registered(url_name):
    """Return True if the given URL name exists in the root URLconf."""
    return url_name in get_resolver().reverse_dict


@dataclass
class BackendURL:
    route: str
    name: str
    namespace: str
    has_parameters: bool
    view_name: str
    is_testable: bool = True
    skip_reason: str = ""
    resolved_route: str = ""


@dataclass
class _DiscoveredAdminRoute:
    raw_route: str
    name: str
    namespace: str
    callback: object


@dataclass
class _NormalizedAdminRoute:
    route: str
    name: str
    namespace: str
    callback: object
    has_parameters: bool
    view_name: str


@dataclass
class _AdminClassification:
    is_testable: bool = True
    skip_reason: str = ""
    should_resolve: bool = False


def _get_view_name(callback):
    """Return a dotted path for a view callback."""
    if hasattr(callback, "view_class"):
        cls = callback.view_class
        return f"{cls.__module__}.{cls.__qualname__}"
    if hasattr(callback, "__module__") and hasattr(callback, "__qualname__"):
        return f"{callback.__module__}.{callback.__qualname__}"
    return repr(callback)


def _iter_callback_view_classes(callback):
    """Yield distinct view classes exposed by a callback."""
    seen = set()
    for attr_name in ("view_class", "cls"):
        view_class = getattr(callback, attr_name, None)
        if view_class is None or view_class in seen:
            continue
        seen.add(view_class)
        yield view_class


def _get_callback_allowed_http_methods(callback):
    """Return declared HTTP methods for the callback when discoverable."""
    allowed_methods = set()
    callback_actions = getattr(callback, "actions", None)
    if callback_actions:
        allowed_methods.update(str(method_name).upper() for method_name in callback_actions)

    for view_class in _iter_callback_view_classes(callback):
        declared_methods = getattr(view_class, "http_method_names", None)
        if declared_methods is None:
            continue
        for method_name in declared_methods:
            if hasattr(view_class, method_name):
                allowed_methods.add(method_name.upper())

    callback_allowed_methods = getattr(callback, "allowed_methods", None)
    if callback_allowed_methods:
        allowed_methods.update(str(method_name).upper() for method_name in callback_allowed_methods)

    return allowed_methods


def _get_method_skip_reason(callback):
    """Return a skip reason when the callback does not support GET."""
    allowed_methods = _get_callback_allowed_http_methods(callback)
    if not allowed_methods or "GET" in allowed_methods:
        return ""
    if allowed_methods.issubset({"POST", "OPTIONS"}):
        return "POST-only view"
    return "GET not supported"


NON_TESTABLE_NAMES = {
    "wagtailadmin_logout": "POST-only view",
    "wagtailadmin_error_test": "Intentional error endpoint",
    "process_import": "POST-only view",
    "wagtailadmin_block_preview": "POST-only view",
    "lock": "POST-only view",
    "unlock": "POST-only view",
    "find": "Requires query parameters",
}
DOCS_SERVE_NAMESPACES = {
    "wagtaildocs",
    "wagtaildocs_chooser",
    "wagtailadmin_api:documents",
}
IMAGE_GENERATOR_NAMES = {
    "url_generator",
    "url_generator_output",
}


def _discover_admin_routes():
    """Return raw admin routes discovered from the resolver."""
    resolver = get_resolver()
    results = []
    for route, name, namespace, callback in walk_patterns(resolver.url_patterns):
        if route.startswith("admin/"):
            results.append(
                _DiscoveredAdminRoute(
                    raw_route=route,
                    name=name,
                    namespace=namespace,
                    callback=callback,
                )
            )
    return results


def _has_unsafe_admin_regex(route):
    """Return True when a cleaned admin route still contains unsafe regex syntax."""
    return bool(re.search(r"[.][*+?]|\(", route))


def _normalize_admin_route(discovered_route, skip_prefixes):
    """Normalize a raw admin route and filter unsupported patterns."""
    route = clean_regex_route(discovered_route.raw_route)
    if _has_unsafe_admin_regex(route):
        return None
    if skip_prefixes and any(route.startswith(prefix) for prefix in skip_prefixes):
        return None
    return _NormalizedAdminRoute(
        route=route,
        name=discovered_route.name,
        namespace=discovered_route.namespace,
        callback=discovered_route.callback,
        has_parameters=route_has_parameters(route),
        view_name=_get_view_name(discovered_route.callback),
    )


def _classify_admin_route(normalized_route, docs_serve_available, images_serve_available):
    """Classify a normalized admin route before parameter resolution."""
    if normalized_route.name in NON_TESTABLE_NAMES:
        return _AdminClassification(
            is_testable=False,
            skip_reason=NON_TESTABLE_NAMES[normalized_route.name],
        )
    if not docs_serve_available and normalized_route.namespace in DOCS_SERVE_NAMESPACES:
        return _AdminClassification(
            is_testable=False,
            skip_reason='Requires path("documents/", include(wagtaildocs_urls)) in URLconf',
        )
    if (
        not images_serve_available
        and normalized_route.namespace == "wagtailimages"
        and normalized_route.name in IMAGE_GENERATOR_NAMES
    ):
        return _AdminClassification(
            is_testable=False,
            skip_reason='Requires path("images/", include(wagtailimages_urls)) in URLconf',
        )
    if normalized_route.has_parameters:
        return _AdminClassification(should_resolve=True)
    return _AdminClassification()


def _finalize_admin_route(normalized_route, classification):
    """Emit the final BackendURL from normalized and classified state."""
    resolved_route = ""
    is_testable = classification.is_testable
    skip_reason = classification.skip_reason

    if classification.should_resolve:
        resolution = resolve_parameterized_url(
            normalized_route.namespace,
            normalized_route.name,
            normalized_route.callback,
            normalized_route.route,
        )
        if resolution.resolved:
            resolved_route = resolution.resolved_route
        else:
            is_testable = False
            skip_reason = "URL requires parameters"

    if is_testable:
        method_skip_reason = _get_method_skip_reason(normalized_route.callback)
        if method_skip_reason:
            is_testable = False
            skip_reason = method_skip_reason

    return BackendURL(
        route=normalized_route.route,
        name=normalized_route.name,
        namespace=normalized_route.namespace,
        has_parameters=normalized_route.has_parameters,
        view_name=normalized_route.view_name,
        is_testable=is_testable,
        skip_reason=skip_reason,
        resolved_route=resolved_route,
    )


def get_admin_urls():
    """Discover all Wagtail admin URLs from the root URL resolver.

    Returns a list of BackendURL dataclass instances for every URL pattern
    under the admin/ prefix.
    """
    images_serve_available = _is_url_registered("wagtailimages_serve")
    docs_serve_available = _is_url_registered("wagtaildocs_serve")
    skip_prefixes = get_skip_url_prefixes()
    results = []
    for discovered_route in _discover_admin_routes():
        normalized_route = _normalize_admin_route(discovered_route, skip_prefixes)
        if normalized_route is None:
            continue
        classification = _classify_admin_route(
            normalized_route,
            docs_serve_available=docs_serve_available,
            images_serve_available=images_serve_available,
        )
        results.append(_finalize_admin_route(normalized_route, classification))
    return results
