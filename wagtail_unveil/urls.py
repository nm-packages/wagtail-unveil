import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from urllib.parse import urlparse

from django.apps import apps
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils.functional import cached_property as django_cached_property

from wagtail_unveil.settings import get_pages_per_type

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


def _clean_regex_route(route):
    """Strip regex syntax from a route string.

    Removes ^ and $ anchors and converts regex named groups
    ``(?P<name>...)`` to path-style ``<name>`` placeholders.
    """
    route = route.replace("^", "").replace("$", "")
    route = re.sub(r"\(\?P<(\w+)>[^)]+\)", r"<\1>", route)
    return route


def _get_model_from_name(name):
    """Extract a Django model from a modeladmin-style URL name.

    Modeladmin URL names follow the pattern ``{app}_{model}_modeladmin_{action}``.
    Returns the model class or None.
    """
    match = re.match(r"^(\w+)_(\w+)_modeladmin_\w+$", name)
    if not match:
        return None
    app_label, model_name = match.groups()
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


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


def _get_form_page_instance():
    """Find a live form page instance for wagtailforms URL resolution.

    Returns the first Page instance whose specific type is an AbstractForm
    subclass, or None if wagtail.contrib.forms is not installed or no form
    pages exist.
    """
    try:
        from wagtail.contrib.forms.models import FormMixin
    except ImportError:
        return None

    from wagtail.models import Page

    for page in Page.objects.live().specific().iterator():
        if isinstance(page, FormMixin):
            return page
    return None


def _resolve_parameterised_url(namespace, name, callback):
    """Attempt to resolve a parameterised URL using a real model instance.

    Extracts the model from the view callback, fetches the first instance,
    and reverses the URL with that instance's PK. For treebeard models
    (e.g. Collection), skips the root node (depth=1) which Wagtail protects.

    Falls back to parsing the URL name for modeladmin-style patterns when
    the callback doesn't expose a model directly. For ``wagtailforms``
    namespace URLs, falls back to finding a live form page instance.

    Returns the resolved path (without leading '/') or None.
    """
    model = _get_model_from_callback(callback)
    if model is None:
        model = _get_model_from_name(name)

    instance = None
    if model is not None:
        queryset = model.objects.all()
        if hasattr(model, "depth"):
            queryset = queryset.exclude(depth=1)
        instance = queryset.first()

    # Fallback: wagtailforms views use page_id but don't expose a model
    if instance is None and namespace == "wagtailforms":
        instance = _get_form_page_instance()

    if instance is None:
        return None
    try:
        url_name = f"{namespace}:{name}" if namespace else name
        url = reverse(url_name, args=[instance.pk])
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
        route = _clean_regex_route(route)
        has_parameters = "<" in route
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


@dataclass
class FrontendURL:
    url: str
    source: str
    page_type: str
    page_title: str
    name: str
    is_testable: bool = True
    skip_reason: str = ""


def _get_page_urls():
    """Discover frontend URLs from live Wagtail pages.

    Uses Page.objects.live().specific() to get all live pages, returning
    their .url property. Skips the root Page model and pages without a URL.
    Form pages (FormMixin subclasses) also get a second non-testable entry
    for the landing page (POST response).
    """
    try:
        from wagtail.contrib.forms.models import FormMixin
    except ImportError:
        FormMixin = None

    from wagtail.models import Page

    results = []
    pages = Page.objects.live().specific()
    for page in pages:
        # Skip the base Page model (depth 1 is the abstract root)
        if type(page) is Page:
            continue
        try:
            url = page.url
        except Exception:
            url = None
        if not url:
            continue
        # Strip to path-only for multi-site support
        parsed = urlparse(url)
        path = parsed.path
        page_type = f"{page._meta.app_label}.{type(page).__name__}"
        results.append(
            FrontendURL(
                url=path,
                source="page",
                page_type=page_type,
                page_title=page.title,
                name="",
            )
        )
        if FormMixin is not None and isinstance(page, FormMixin):
            results.append(
                FrontendURL(
                    url=path,
                    source="page",
                    page_type=page_type,
                    page_title=page.title,
                    name="landing_page",
                    is_testable=False,
                    skip_reason="Requires POST submission",
                )
            )
    limit = get_pages_per_type()
    if limit:
        grouped = defaultdict(list)
        for frontend_url in results:
            grouped[frontend_url.page_type].append(frontend_url)
        results = []
        for page_type_urls in grouped.values():
            results.extend(page_type_urls[:limit])

    return results


# Namespaces that belong to unveil itself — exclude from frontend resolver URLs.
_UNVEIL_NAMESPACES = {"wagtail_unveil_api", "wagtail_unveil_report"}


def _get_resolver_frontend_urls():
    """Discover frontend URLs from Django's URL resolver (non-admin routes).

    Reuses _walk_patterns() but excludes admin/ routes and unveil's own
    namespaces. Parameterized and regex URLs are marked as non-testable.
    """
    resolver = get_resolver()
    results = []
    for route, name, namespace, _callback in _walk_patterns(resolver.url_patterns):
        # Exclude admin routes
        if route.startswith("admin/"):
            continue
        # Exclude Django admin
        if route.startswith("django-admin/"):
            continue
        # Exclude unveil's own namespaces
        if namespace in _UNVEIL_NAMESPACES:
            continue

        route = _clean_regex_route(route)
        is_testable = True
        skip_reason = ""

        # Parameterized URLs are not directly testable
        has_parameters = "<" in route
        if has_parameters:
            is_testable = False
            skip_reason = "URL requires parameters"

        url = f"/{route}" if not route.startswith("/") else route
        results.append(
            FrontendURL(
                url=url,
                source="resolver",
                page_type="",
                page_title="",
                name=name,
                is_testable=is_testable,
                skip_reason=skip_reason,
            )
        )
    return results


def get_frontend_urls():
    """Discover all frontend URLs from pages and the URL resolver.

    Returns a list of FrontendURL dataclass instances combining page URLs
    and non-admin resolver URLs.
    """
    return _get_page_urls() + _get_resolver_frontend_urls()
