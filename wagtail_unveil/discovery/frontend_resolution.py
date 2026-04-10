import re

from django.apps import apps
from django.db import models
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents import get_document_model
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images import get_image_model
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.models import Page, Site

from wagtail_unveil.discovery.utils import route_contains_regex, route_has_parameters

ROUTABLE_PARAMETER_PATTERN = re.compile(r"<(?:(?P<converter>[^:>]+):)?(?P<name>[^>]+)>")


def join_frontend_paths(base_path, sub_path):
    """Join a page path and relative sub-route into a normalized absolute path."""
    base = base_path.rstrip("/")
    joined = f"{base}/{sub_path.lstrip('/')}"
    return joined if joined.startswith("/") else f"/{joined}"


def _iter_routable_parameters(sub_route):
    """Yield ordered (name, converter) tuples from a path-style route string."""
    for match in ROUTABLE_PARAMETER_PATTERN.finditer(sub_route):
        yield match.group("name"), match.group("converter") or "str"


def _unique_values(values):
    """Return values in first-seen order without duplicates."""
    unique = []
    for value in values:
        if value in (None, ""):
            continue
        if value in unique:
            continue
        unique.append(value)
    return unique


def get_default_site():
    """Return the default Wagtail Site instance when available."""
    return Site.objects.filter(is_default_site=True).first()


# Routable page parameter helpers


def _get_descendant_date_years(page):
    """Collect distinct years from concrete date fields on descendant pages."""
    years = []
    try:
        descendants = page.get_descendants().live().public().specific()
    except Exception:
        return years

    for descendant in descendants:
        for model_field in descendant._meta.fields:
            if model_field.model is not descendant.__class__:
                continue
            if not isinstance(model_field, models.DateField):
                continue
            value = getattr(descendant, model_field.name, None)
            if value is None or getattr(value, "year", None) is None:
                continue
            years.append(value.year)
    return _unique_values(sorted(years, reverse=True))


def _get_descendant_page_candidates(page, attribute_name):
    """Collect attribute values from descendant pages in tree order."""
    values = []
    try:
        descendants = page.get_descendants().live().public().specific()
    except Exception:
        return values

    for descendant in descendants:
        value = getattr(descendant, attribute_name, None)
        if callable(value):
            continue
        values.append(value)
    return _unique_values(values)


def _get_routable_parameter_candidates(page, parameter_name, converter_name):
    """Return best-effort candidate values for a routable page parameter."""
    values = []

    if not (
        parameter_name in {"pk", "id", "slug", "uuid"}
        or parameter_name.endswith("_id")
        or parameter_name.endswith("_slug")
    ):
        page_value = getattr(page, parameter_name, None)
        if not callable(page_value):
            values.append(page_value)

    if parameter_name == "year":
        values.extend(_get_descendant_date_years(page))

    if parameter_name in {"pk", "id"} or parameter_name.endswith("_id"):
        values.extend(_get_descendant_page_candidates(page, "pk"))

    if converter_name == "slug" or parameter_name == "slug" or parameter_name.endswith("_slug"):
        values.extend(_get_descendant_page_candidates(page, "slug"))

    if converter_name == "uuid" or parameter_name == "uuid":
        values.extend(_get_descendant_page_candidates(page, "uuid"))

    return _unique_values(values)


def resolve_routable_page_url(page, pattern, page_path, sub_route):
    """Resolve a concrete routable subpage URL when safe example args can be inferred."""
    if not getattr(pattern.pattern, "_route", None):
        return ""
    if not pattern.name or not route_has_parameters(sub_route) or route_contains_regex(sub_route):
        return ""

    parameters = list(_iter_routable_parameters(sub_route))
    if len(parameters) != 1:
        return ""

    args = []
    for parameter_name, converter_name in parameters:
        candidates = _get_routable_parameter_candidates(page, parameter_name, converter_name)
        if not candidates:
            return ""
        args.append(candidates[0])

    try:
        resolved_subpath = page.reverse_subpage(pattern.name, args=args)
    except Exception:
        return ""

    resolved_url = join_frontend_paths(page_path, resolved_subpath)
    if route_has_parameters(resolved_url) or route_contains_regex(resolved_url):
        return ""
    return resolved_url


# Resolver-backed API ID helpers


def _get_first_public_live_page_id():
    """Return the first live public page ID when available."""
    page_id = Page.objects.live().public().order_by("path").values_list("pk", flat=True).first()
    return str(page_id) if page_id else ""


def _get_first_image_id():
    """Return the first Wagtail image ID when available."""
    image_model = get_image_model()
    image_id = image_model.objects.order_by("pk").values_list("pk", flat=True).first()
    return str(image_id) if image_id else ""


def _get_first_document_id():
    """Return the first Wagtail document ID when available."""
    document_model = get_document_model()
    document_id = document_model.objects.order_by("pk").values_list("pk", flat=True).first()
    return str(document_id) if document_id else ""


def _get_first_redirect_id():
    """Return the first redirect ID when available."""
    if not apps.is_installed("wagtail.contrib.redirects"):
        return ""

    # Optional contrib app: only import when redirects is enabled.
    from wagtail.contrib.redirects.models import Redirect

    redirect_id = Redirect.objects.order_by("pk").values_list("pk", flat=True).first()
    return str(redirect_id) if redirect_id else ""


# Wagtail API resolution helpers


def get_wagtail_api_detail_resolved_url(callback, url):
    """Return a concrete resolved URL for supported Wagtail API detail routes."""
    callback_cls = getattr(callback, "cls", None)
    callback_actions = getattr(callback, "actions", {}) or {}
    if callback_actions.get("get") != "detail_view":
        return ""

    if callback_cls is PagesAPIViewSet:
        default_site = get_default_site()
        page_id = ""
        if default_site and default_site.root_page_id:
            if Page.objects.live().public().filter(pk=default_site.root_page_id).exists():
                page_id = str(default_site.root_page_id)
        if not page_id:
            page_id = _get_first_public_live_page_id()
        return url.replace("<int:pk>", page_id, 1) if page_id else ""

    if callback_cls is ImagesAPIViewSet:
        image_id = _get_first_image_id()
        return url.replace("<int:pk>", image_id, 1) if image_id else ""

    if callback_cls is DocumentsAPIViewSet:
        document_id = _get_first_document_id()
        return url.replace("<int:pk>", document_id, 1) if document_id else ""

    if apps.is_installed("wagtail.contrib.redirects"):
        # Optional contrib app: only import when redirects is enabled.
        from wagtail.contrib.redirects.api import RedirectsAPIViewSet

        if callback_cls is RedirectsAPIViewSet:
            redirect_id = _get_first_redirect_id()
            return url.replace("<int:pk>", redirect_id, 1) if redirect_id else ""

    return ""


def is_supported_wagtail_api_find_route(name, callback):
    """Return True for supported Wagtail API GET find routes."""
    if name != "find":
        return False

    callback_actions = getattr(callback, "actions", {}) or {}
    if callback_actions.get("get") != "find_view":
        return False

    supported_viewsets = {
        PagesAPIViewSet,
        ImagesAPIViewSet,
        DocumentsAPIViewSet,
    }

    if apps.is_installed("wagtail.contrib.redirects"):
        # Optional contrib app: only import when redirects is enabled.
        from wagtail.contrib.redirects.api import RedirectsAPIViewSet

        supported_viewsets.add(RedirectsAPIViewSet)

    return getattr(callback, "cls", None) in supported_viewsets
