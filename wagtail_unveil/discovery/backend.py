import re
from dataclasses import dataclass, field
from functools import cached_property

from django.apps import apps
from django.urls import get_resolver, reverse
from django.utils.functional import cached_property as django_cached_property

from wagtail_unveil.discovery.utils import clean_regex_route, walk_patterns
from wagtail_unveil.settings import get_skip_url_prefixes


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


@dataclass
class _ParameterizedURLResolution:
    """Internal resolution state for a parameterized admin URL."""

    resolved_route: str = ""
    resolved: bool = False
    method: str = ""
    detail: str = ""
    attempts: list[str] = field(default_factory=list)

    def add_attempt(self, strategy, outcome):
        self.attempts.append(f"{strategy}:{outcome}")


def _get_view_name(callback):
    """Return a dotted path for a view callback."""
    if hasattr(callback, "view_class"):
        cls = callback.view_class
        return f"{cls.__module__}.{cls.__qualname__}"
    if hasattr(callback, "__module__") and hasattr(callback, "__qualname__"):
        return f"{callback.__module__}.{callback.__qualname__}"
    return repr(callback)


WORKFLOW_USAGE_NAMES = ("usage", "usage_results")
NAMESPACE_INSTANCE_RESOLVERS = (
    {
        "label": "namespace:wagtailforms",
        "predicate": lambda namespace, name: namespace == "wagtailforms",
        "resolver": lambda: _get_form_page_instance(),
        "override": False,
    },
    {
        "label": "namespace:wagtailadmin_workflows",
        "predicate": lambda namespace, name: namespace == "wagtailadmin_workflows" and name in WORKFLOW_USAGE_NAMES,
        "resolver": lambda: _get_workflow_instance(),
        "override": True,
    },
)


def _get_model_from_modeladmin_name(name):
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


def _get_workflow_instance():
    """Return the first available Workflow instance."""
    try:
        from wagtail.models import Workflow

        return Workflow.objects.first()
    except Exception:
        return None


def _get_instance_for_model(model):
    """Return a representative instance for the given model, if one exists."""
    queryset = model.objects.all()
    if hasattr(model, "depth"):
        queryset = queryset.exclude(depth=1)
    return queryset.first()


def _build_url_name(namespace, name):
    """Return the fully namespaced URL name for reversal."""
    return f"{namespace}:{name}" if namespace else name


def _reverse_with_instance(namespace, name, instance):
    """Reverse a parameterized URL using a single positional PK argument."""
    result = _ParameterizedURLResolution(method="reverse")
    try:
        url = reverse(_build_url_name(namespace, name), args=[instance.pk])
    except Exception as exc:
        result.add_attempt("reverse", "failed")
        result.detail = str(exc) or exc.__class__.__name__
        return result

    result.add_attempt("reverse", "resolved")
    result.resolved = True
    result.resolved_route = url.lstrip("/")
    result.detail = f"Reversed {_build_url_name(namespace, name)} with pk={instance.pk}"
    return result


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

    Returns an internal resolution result.
    """
    result = _ParameterizedURLResolution(method="settings")
    try:
        from wagtail.contrib.settings.registry import registry
    except ImportError:
        result.add_attempt("settings", "registry-unavailable")
        result.detail = "Wagtail settings registry is unavailable"
        return result

    has_pk = "<int:pk>" in route
    matched_model = False
    found_instance = False
    for model in registry:
        app_name = model._meta.app_label
        model_name = model._meta.model_name
        kwargs = {"app_name": app_name, "model_name": model_name}
        matched_model = True

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
            found_instance = True
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
            url = reverse("wagtailsettings:%s" % name, kwargs=kwargs)
        except Exception as exc:
            result.detail = str(exc) or exc.__class__.__name__
            continue

        result.add_attempt("settings", "resolved")
        result.resolved = True
        result.resolved_route = url.lstrip("/")
        result.detail = f"Resolved wagtailsettings:{name} via {app_name}.{model_name}"
        return result

    if has_pk and matched_model and not found_instance:
        result.add_attempt("settings", "no-model-instance")
        result.detail = "No settings instances exist for the registered settings models"
    else:
        result.add_attempt("settings", "reverse-failed")
        if not result.detail:
            result.detail = "Could not reverse wagtailsettings URL for any registered settings model"
    return result


def _get_namespace_specific_instance(namespace, name, current_instance):
    """Return a namespace-specific instance override when one applies."""
    selected_method = ""
    selected_instance = current_instance
    attempts = []

    for rule in NAMESPACE_INSTANCE_RESOLVERS:
        if not rule["predicate"](namespace, name):
            continue
        if current_instance is not None and not rule["override"]:
            attempts.append(f"{rule['label']}:skipped")
            continue

        instance = rule["resolver"]()
        if instance is None:
            attempts.append(f"{rule['label']}:no-instance")
            if rule["override"]:
                selected_method = rule["label"]
                selected_instance = None
                current_instance = None
                break
            continue

        attempts.append(f"{rule['label']}:instance-found")
        selected_method = rule["label"]
        selected_instance = instance
        current_instance = instance

    return selected_method, selected_instance, attempts


def _resolve_parameterized_url(namespace, name, callback, route=""):
    """Attempt to resolve a parameterized admin URL using an explicit strategy order."""
    if namespace == "wagtailsettings":
        return _resolve_settings_url(name, route)

    result = _ParameterizedURLResolution()

    selected_method = ""
    selected_instance = None

    model = _get_model_from_callback(callback)
    if model is not None:
        result.add_attempt("callback-model", "model-found")
        selected_instance = _get_instance_for_model(model)
        if selected_instance is not None:
            selected_method = "callback-model"
            result.add_attempt("callback-model", "instance-found")
        else:
            result.add_attempt("callback-model", "no-instance")
    else:
        result.add_attempt("callback-model", "no-model")

    if selected_instance is None:
        model = _get_model_from_modeladmin_name(name)
        if model is not None:
            result.add_attempt("modeladmin-name", "model-found")
            selected_instance = _get_instance_for_model(model)
            if selected_instance is not None:
                selected_method = "modeladmin-name"
                result.add_attempt("modeladmin-name", "instance-found")
            else:
                result.add_attempt("modeladmin-name", "no-instance")
        else:
            result.add_attempt("modeladmin-name", "no-model")
    else:
        result.add_attempt("modeladmin-name", "skipped")

    namespace_method, namespace_instance, namespace_attempts = _get_namespace_specific_instance(
        namespace,
        name,
        selected_instance,
    )
    result.attempts.extend(namespace_attempts)
    if namespace_method:
        selected_method = namespace_method
        selected_instance = namespace_instance

    if selected_instance is None:
        result.method = selected_method
        if selected_method:
            result.detail = f"{selected_method} did not provide a compatible instance for URL parameters"
        else:
            result.detail = "No model-backed instance was available for URL parameters"
        return result

    reverse_result = _reverse_with_instance(namespace, name, selected_instance)
    result.attempts.extend(reverse_result.attempts)
    if reverse_result.resolved:
        result.resolved = True
        result.method = selected_method or "reverse"
        result.resolved_route = reverse_result.resolved_route
        result.detail = (
            f"{result.method} resolved {_build_url_name(namespace, name)} to {reverse_result.resolved_route}"
        )
        return result

    result.method = selected_method or "reverse"
    result.detail = (
        f"{result.method} found an instance for {_build_url_name(namespace, name)} "
        f"but reverse failed: {reverse_result.detail}"
    )
    return result


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
            resolution = _resolve_parameterized_url(namespace, name, callback, route)
            if resolution.resolved:
                is_testable = True
                resolved_route = resolution.resolved_route
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
