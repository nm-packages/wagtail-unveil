import logging
import re
from dataclasses import dataclass
from functools import cached_property

from django.apps import apps
from django.urls import get_resolver, reverse
from django.utils.functional import cached_property as django_cached_property

from wagtail_unveil.discovery.utils import clean_regex_route, walk_patterns
from wagtail_unveil.settings import get_skip_url_prefixes

logger = logging.getLogger(__name__)


def _is_url_registered(url_name):
    """Return True if the given URL name exists in the root URLconf."""
    return url_name in get_resolver().reverse_dict


def _is_django_model(obj):
    """Check if obj is a Django model class."""
    return isinstance(obj, type) and hasattr(obj, "_meta")


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


def _get_view_name(callback):
    """Return a dotted path for a view callback."""
    if hasattr(callback, "view_class"):
        cls = callback.view_class
        return f"{cls.__module__}.{cls.__qualname__}"
    if hasattr(callback, "__module__") and hasattr(callback, "__qualname__"):
        return f"{callback.__module__}.{callback.__qualname__}"
    return repr(callback)


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
    initkwargs = getattr(callback, "initkwargs", None) or getattr(callback, "view_initkwargs", None)
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


def _resolve_settings_url(name, route):
    """Resolve a wagtailsettings URL using registered setting models.

    Settings URLs use kwargs (app_name, model_name, and optionally pk)
    rather than positional args. Iterates over registered setting models
    to find one with an existing instance.

    Note: This function handles version-specific differences:
    - Wagtail 7.0: No preview_on_edit URL; BaseSiteSetting.site_id always correct
    - Wagtail 7.1+: Adds preview_on_edit URL (only for PreviewableMixin models)
    - Wagtail 7.0+: pk parameter differs by model type (site_id vs instance pk)

    If we drop Wagtail 7.0 support, we can simplify:
    - Remove the preview_on_edit guard (always check PreviewableMixin)
    - Remove the try/except on PreviewableMixin import
    - Always use BaseSiteSetting (no fallback needed)

    Returns the resolved path (without leading '/') or None.
    """
    try:
        from wagtail.contrib.settings.registry import registry
    except ImportError:
        return None

    has_pk = "<int:pk>" in route
    for model in registry:
        app_name = model._meta.app_label
        model_name = model._meta.model_name
        kwargs = {"app_name": app_name, "model_name": model_name}

        # preview_on_edit is only meaningful for previewable settings models
        # This URL was added in Wagtail 7.1. In 7.0, it doesn't exist in URL patterns.
        # If Wagtail 7.0 support is dropped, the try/except can be removed.
        if name == "preview_on_edit":
            try:
                from wagtail.models import PreviewableMixin

                if not issubclass(model, PreviewableMixin):
                    continue
            except ImportError:
                # Wagtail <7.1: PreviewableMixin doesn't exist; skip this URL
                continue

        if has_pk:
            instance = model.objects.first()
            if not instance:
                continue
            # Wagtail 7.0+: The <int:pk> parameter means different things by model type.
            # BaseSiteSetting: pk in URL = site pk (not settings row pk)
            # BaseGenericSetting: pk in URL = settings row pk
            # If Wagtail 7.0 support is dropped, always use BaseSiteSetting and remove the check.
            try:
                from wagtail.contrib.settings.models import BaseSiteSetting

                if issubclass(model, BaseSiteSetting):
                    kwargs["pk"] = instance.site_id
                else:
                    kwargs["pk"] = instance.pk
            except ImportError:
                # Fallback: assume BaseGenericSetting (unlikely in modern Wagtail)
                kwargs["pk"] = instance.pk
        try:
            url = reverse(f"wagtailsettings:{name}", kwargs=kwargs)
            return url.lstrip("/")
        except Exception:
            continue
    return None


def _resolve_parameterised_url(namespace, name, callback, route=""):
    """Attempt to resolve a parameterised URL using a real model instance.

    Extracts the model from the view callback, fetches the first instance,
    and reverses the URL with that instance's PK. For treebeard models
    (e.g. Collection), skips the root node (depth=1) which Wagtail protects.

    Falls back to parsing the URL name for modeladmin-style patterns when
    the callback doesn't expose a model directly. For ``wagtailforms``
    namespace URLs, falls back to finding a live form page instance. For
    ``wagtailsettings`` namespace URLs, uses registered setting models
    with kwargs-based reversal.

    Returns the resolved path (without leading '/') or None.
    """
    # Settings URLs use kwargs, not positional args
    if namespace == "wagtailsettings":
        return _resolve_settings_url(name, route)

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

    # Fallback: workflow usage views inherit model=Page from PageListingMixin
    # but actually look up a Workflow instance by pk
    if namespace == "wagtailadmin_workflows" and name in ("usage", "usage_results"):
        try:
            from wagtail.models import Workflow

            instance = Workflow.objects.first()
        except Exception:
            instance = None

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

    Returns a list of BackendURL dataclass instances for every URL pattern
    under the admin/ prefix.
    """
    # URL names that are known to be non-testable via GET.
    NON_TESTABLE_NAMES = {
        "wagtailadmin_logout": "POST-only view",
        "wagtailadmin_error_test": "Intentional error endpoint",
        "process_import": "POST-only view",
        "wagtailadmin_block_preview": "POST-only view",
        "lock": "POST-only view",
        "unlock": "POST-only view",
        "find": "Requires query parameters",
    }

    images_serve_available = _is_url_registered("wagtailimages_serve")
    docs_serve_available = _is_url_registered("wagtaildocs_serve")

    resolver = get_resolver()
    skip_prefixes = get_skip_url_prefixes()
    results = []
    for route, name, namespace, callback in walk_patterns(resolver.url_patterns):
        if not route.startswith("admin/"):
            continue
        route = clean_regex_route(route)

        # Skip routes that still contain regex metacharacters after cleaning
        # (e.g. Wagtail's catch-all `.*/$` pattern)
        if re.search(r"[.][*+?]|\(", route):
            continue

        # User-configured prefix exclusions
        if skip_prefixes and any(route.startswith(p) for p in skip_prefixes):
            continue

        has_parameters = "<" in route
        is_testable = True
        skip_reason = ""
        resolved_route = ""
        if name in NON_TESTABLE_NAMES:
            is_testable = False
            skip_reason = NON_TESTABLE_NAMES[name]
        elif not docs_serve_available and namespace in {
            "wagtaildocs",
            "wagtaildocs_chooser",
            "wagtailadmin_api:documents",
        }:
            is_testable = False
            skip_reason = 'Requires path("documents/", include(wagtaildocs_urls)) in URLconf'
        elif (
            not images_serve_available
            and namespace == "wagtailimages"
            and name
            in {
                "url_generator",
                "url_generator_output",
            }
        ):
            is_testable = False
            skip_reason = 'Requires path("images/", include(wagtailimages_urls)) in URLconf'
        elif has_parameters:
            resolved = _resolve_parameterised_url(namespace, name, callback, route)
            if resolved:
                is_testable = True
                resolved_route = resolved
            else:
                is_testable = False
                skip_reason = "URL requires parameters"
        results.append(
            BackendURL(
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
