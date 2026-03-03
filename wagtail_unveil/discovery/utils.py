import re

from django.urls import URLPattern, URLResolver

UNSAFE_REGEX_ROUTE_PATTERN = re.compile(r"(\\|\(|\[|[.][*+?])")


def walk_patterns(patterns, prefix="", namespace=""):
    """Recursively walk URL patterns, yielding (route, name, namespace) tuples."""
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            ns = namespace
            if pattern.namespace:
                ns = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
            yield from walk_patterns(pattern.url_patterns, route, ns)
        elif isinstance(pattern, URLPattern):
            yield route, pattern.name or "", namespace, pattern.callback


def clean_regex_route(route):
    """Strip regex syntax from a route string.

    Removes ^ and $ anchors and converts regex named groups
    ``(?P<name>...)`` to path-style ``<name>`` placeholders.
    """
    route = route.replace("^", "").replace("$", "")
    route = re.sub(r"\(\?P<(\w+)>[^)]+\)", r"<\1>", route)
    return route


def route_has_parameters(route):
    """Return True when a normalized route still contains path parameters."""
    return "<" in route


def route_contains_regex(route):
    """Return True when a normalized route still contains regex syntax."""
    return bool(UNSAFE_REGEX_ROUTE_PATTERN.search(route))
