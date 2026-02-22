from dataclasses import dataclass

from django.urls import URLPattern, URLResolver, get_resolver


@dataclass
class AdminURL:
    route: str
    name: str
    namespace: str
    has_parameters: bool
    view_name: str
    is_testable: bool = True
    skip_reason: str = ""


def _get_view_name(callback):
    """Return a dotted path for a view callback."""
    if hasattr(callback, "view_class"):
        cls = callback.view_class
        return f"{cls.__module__}.{cls.__qualname__}"
    if hasattr(callback, "__module__") and hasattr(callback, "__qualname__"):
        return f"{callback.__module__}.{callback.__qualname__}"
    return repr(callback)


def _walk_patterns(patterns, prefix="", namespace=""):
    """Recursively walk URL patterns, yielding (route, name, namespace) tuples."""
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            ns = namespace
            if pattern.namespace:
                ns = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
            yield from _walk_patterns(pattern.url_patterns, route, ns)
        elif isinstance(pattern, URLPattern):
            yield route, pattern.name or "", namespace, pattern.callback


def get_admin_urls():
    """Discover all Wagtail admin URLs from the root URL resolver.

    Returns a list of AdminURL dataclass instances for every URL pattern
    under the admin/ prefix.
    """
    # URL names that are known to be non-testable via GET.
    NON_TESTABLE_NAMES = {
        "wagtailadmin_logout": "POST-only view",
        "wagtailadmin_error_test": "Intentional error endpoint",
    }

    resolver = get_resolver()
    results = []
    for route, name, namespace, callback in _walk_patterns(resolver.url_patterns):
        if not route.startswith("admin/"):
            continue
        has_parameters = "<" in route or "(" in route
        is_testable = True
        skip_reason = ""
        if has_parameters:
            is_testable = False
            skip_reason = "URL requires parameters"
        elif "^" in route:
            is_testable = False
            skip_reason = "Regex-based route pattern"
        elif name in NON_TESTABLE_NAMES:
            is_testable = False
            skip_reason = NON_TESTABLE_NAMES[name]
        results.append(
            AdminURL(
                route=route,
                name=name,
                namespace=namespace,
                has_parameters=has_parameters,
                view_name=_get_view_name(callback),
                is_testable=is_testable,
                skip_reason=skip_reason,
            )
        )
    return results
