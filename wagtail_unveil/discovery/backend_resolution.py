import re
from dataclasses import dataclass, field
from functools import cached_property

from django.apps import apps
from django.urls import reverse
from django.utils.functional import cached_property as django_cached_property

WORKFLOW_USAGE_NAMES = ("usage", "usage_results")


def _is_django_model(obj):
    """Check if obj is a Django model class."""
    return isinstance(obj, type) and hasattr(obj, "_meta")


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


def _get_model_from_view_class(view_class):
    """Extract a Django model class from a view class or its MRO."""
    if not view_class:
        return None

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


def _get_model_from_callback(callback):
    """Extract a Django model class from a view callback.

    Checks callback metadata in order:
    1. view_initkwargs["model"] — ModelViewSet views (as_view(model=Model))
    2. callback.view_class and its MRO
    3. callback.cls and its MRO
    """
    initkwargs = getattr(callback, "initkwargs", None) or getattr(callback, "view_initkwargs", None)
    if initkwargs:
        model = initkwargs.get("model")
        if _is_django_model(model):
            return model

    for view_class in (getattr(callback, "view_class", None), getattr(callback, "cls", None)):
        model = _get_model_from_view_class(view_class)
        if model is not None:
            return model

    return None


def _get_form_page_instance():
    """Find a live form page instance for wagtailforms URL resolution."""
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
    """Resolve a wagtailsettings URL using registered setting models."""
    result = _ParameterizedURLResolution(method="settings")
    try:
        from wagtail.contrib.settings.registry import registry
    except ImportError:
        result.add_attempt("settings", "registry-unavailable")
        result.detail = "Wagtail settings registry is unavailable"
        return result

    has_pk = "<int:pk>" in route
    eligible_model_seen = False
    found_instance = False
    for model in registry:
        app_name = model._meta.app_label
        model_name = model._meta.model_name
        kwargs = {"app_name": app_name, "model_name": model_name}

        if name == "preview_on_edit":
            try:
                from wagtail.models import PreviewableMixin

                if not issubclass(model, PreviewableMixin):
                    continue
            except ImportError:
                continue

        eligible_model_seen = True

        if has_pk:
            instance = model.objects.first()
            if not instance:
                continue
            found_instance = True
            try:
                from wagtail.contrib.settings.models import BaseSiteSetting

                if issubclass(model, BaseSiteSetting):
                    kwargs["pk"] = instance.site_id
                else:
                    kwargs["pk"] = instance.pk
            except ImportError:
                kwargs["pk"] = instance.pk
        try:
            url = reverse(f"wagtailsettings:{name}", kwargs=kwargs)
        except Exception as exc:
            result.detail = str(exc) or exc.__class__.__name__
            continue

        result.add_attempt("settings", "resolved")
        result.resolved = True
        result.resolved_route = url.lstrip("/")
        result.detail = f"Resolved wagtailsettings:{name} via {app_name}.{model_name}"
        return result

    if has_pk and eligible_model_seen and not found_instance:
        result.add_attempt("settings", "no-model-instance")
        result.detail = "No settings instances exist for the registered settings models"
    else:
        result.add_attempt("settings", "reverse-failed")
        if not result.detail:
            result.detail = "Could not reverse wagtailsettings URL for any registered settings model"
    return result


def _get_namespace_specific_instance(namespace, name, current_instance):
    """Return a namespace-specific instance override when one applies."""
    if namespace == "wagtailforms":
        if current_instance is not None:
            return "", current_instance, ["namespace:wagtailforms:skipped"]

        instance = _get_form_page_instance()
        if instance is None:
            return "", None, ["namespace:wagtailforms:no-instance"]
        return "namespace:wagtailforms", instance, ["namespace:wagtailforms:instance-found"]

    if namespace == "wagtailadmin_workflows" and name in WORKFLOW_USAGE_NAMES:
        instance = _get_workflow_instance()
        if instance is None:
            return "namespace:wagtailadmin_workflows", None, ["namespace:wagtailadmin_workflows:no-instance"]
        return (
            "namespace:wagtailadmin_workflows",
            instance,
            ["namespace:wagtailadmin_workflows:instance-found"],
        )

    return "", current_instance, []


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
