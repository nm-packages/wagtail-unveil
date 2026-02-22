import logging
from dataclasses import dataclass
from functools import cached_property

from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils.functional import cached_property as django_cached_property

logger = logging.getLogger(__name__)


@dataclass
class AdminURL:
    route: str
    name: str
    namespace: str
    has_parameters: bool
    view_name: str
    is_testable: bool = True
    skip_reason: str = ""
    resolved_route: str = ""


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


def _is_django_model(obj):
    """Check if obj is a Django model class."""
    return isinstance(obj, type) and hasattr(obj, "_meta")


def _get_model_from_callback(callback):
    """Extract a Django model class from a view callback.

    Checks three sources in order:
    1. view_initkwargs["model"] — ModelViewSet views (as_view(model=Model))
    2. view_class.__dict__["model"] as a plain class attribute
    3. view_class.__dict__["model"] as a cached_property (calls func(None))
    """
    # Source 1: initkwargs (ModelViewSet pattern)
    initkwargs = getattr(callback, "initkwargs", None) or getattr(
        callback, "view_initkwargs", None
    )
    if initkwargs:
        model = initkwargs.get("model")
        if _is_django_model(model):
            return model

    # Sources 2 & 3: class attribute or cached_property on view_class
    view_class = getattr(callback, "view_class", None)
    if view_class:
        model_attr = view_class.__dict__.get("model")
        if _is_django_model(model_attr):
            return model_attr
        if isinstance(model_attr, (cached_property, django_cached_property)):
            try:
                model = model_attr.func(None)
                if _is_django_model(model):
                    return model
            except Exception:
                pass

        # Source 4: model inherited from a parent class (e.g. search promotions mixin)
        for cls in view_class.__mro__:
            model_attr = cls.__dict__.get("model")
            if _is_django_model(model_attr):
                return model_attr
            if isinstance(model_attr, (cached_property, django_cached_property)):
                try:
                    model = model_attr.func(None)
                    if _is_django_model(model):
                        return model
                except Exception:
                    pass

    return None


def _resolve_parameterised_url(namespace, name, callback):
    """Attempt to resolve a parameterised URL using a real model instance.

    Extracts the model from the view callback, fetches the first instance,
    and reverses the URL with that instance's PK.

    Returns the resolved path (without leading '/') or None.
    """
    model = _get_model_from_callback(callback)
    if model is None:
        return None
    instance = model.objects.first()
    if instance is None:
        return None
    try:
        url = reverse(f"{namespace}:{name}", args=[instance.pk])
        return url.lstrip("/")
    except Exception:
        logger.debug("Failed to reverse %s:%s", namespace, name, exc_info=True)
        return None


def get_admin_urls():
    """Discover all Wagtail admin URLs from the root URL resolver.

    Returns a list of AdminURL dataclass instances for every URL pattern
    under the admin/ prefix.
    """
    # URL names that are known to be non-testable via GET.
    NON_TESTABLE_NAMES = {
        "wagtailadmin_logout": "POST-only view",
        "wagtailadmin_error_test": "Intentional error endpoint",
        "process_import": "POST-only view",
        "wagtailadmin_block_preview": "POST-only view",
    }

    resolver = get_resolver()
    results = []
    for route, name, namespace, callback in _walk_patterns(resolver.url_patterns):
        if not route.startswith("admin/"):
            continue
        has_parameters = "<" in route or "(" in route
        is_testable = True
        skip_reason = ""
        resolved_route = ""
        if has_parameters:
            resolved = _resolve_parameterised_url(namespace, name, callback)
            if resolved:
                is_testable = True
                resolved_route = resolved
            else:
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
                resolved_route=resolved_route,
            )
        )
    return results
