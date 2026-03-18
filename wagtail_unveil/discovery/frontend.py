import re
from dataclasses import dataclass
from urllib.parse import urlparse

from django.db import models
from django.urls import get_resolver

from wagtail_unveil.discovery.utils import clean_regex_route, route_contains_regex, route_has_parameters, walk_patterns
from wagtail_unveil.settings import get_pages_per_type, get_skip_url_prefixes

ROUTABLE_PARAMETER_PATTERN = re.compile(r"<(?:(?P<converter>[^:>]+):)?(?P<name>[^>]+)>")


@dataclass
class FrontendURL:
    url: str
    source: str
    page_type: str
    page_title: str
    name: str
    resolved_url: str = ""
    is_testable: bool = True
    skip_reason: str = ""


@dataclass
class _FrontendCandidate:
    url: str
    source: str
    page_type: str
    page_title: str
    name: str
    site_hostname: str = ""
    site_port: int | None = None
    is_cross_site: bool = False
    has_parameters: bool = False
    contains_regex: bool = False
    requires_post: bool = False
    resolved_url: str = ""


@dataclass
class _FrontendClassification:
    is_testable: bool = True
    skip_reason: str = ""


def _should_skip_frontend_url(url, skip_prefixes):
    """Return True when a frontend URL matches configured skip prefixes."""
    return bool(skip_prefixes and any(url.lstrip("/").startswith(prefix) for prefix in skip_prefixes))


def _get_default_site():
    """Return the default Wagtail Site instance when available."""
    try:
        from wagtail.models import Site
    except ImportError:
        return None

    return Site.objects.filter(is_default_site=True).first()


def _format_cross_site_skip_reason(candidate):
    """Build a skip reason for candidates that belong to a non-default site host."""
    if not candidate.site_hostname:
        return "Belongs to non-default site host"

    if candidate.site_port and candidate.site_port not in (80, 443):
        return f"Belongs to non-default site host: {candidate.site_hostname}:{candidate.site_port}"

    return f"Belongs to non-default site host: {candidate.site_hostname}"


def _join_frontend_paths(base_path, sub_path):
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


def _get_descendant_date_years(page):
    """Collect distinct years from concrete date fields on descendant pages."""
    years = []
    try:
        descendants = page.get_descendants().live().specific()
    except Exception:
        return years

    for descendant in descendants:
        for field in descendant._meta.fields:
            if field.model is not descendant.__class__:
                continue
            if not isinstance(field, models.DateField):
                continue
            value = getattr(descendant, field.name, None)
            if value is None or getattr(value, "year", None) is None:
                continue
            years.append(value.year)
    return _unique_values(sorted(years, reverse=True))


def _get_descendant_page_candidates(page, attribute_name):
    """Collect attribute values from descendant pages in tree order."""
    values = []
    try:
        descendants = page.get_descendants().live().specific()
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


def _resolve_routable_page_url(page, pattern, page_path, sub_route):
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

    resolved_url = _join_frontend_paths(page_path, resolved_subpath)
    if route_has_parameters(resolved_url) or route_contains_regex(resolved_url):
        return ""
    return resolved_url


def _discover_page_candidates():
    """Discover frontend page candidates before classification."""
    try:
        from wagtail.contrib.forms.models import FormMixin
    except ImportError:
        FormMixin = None

    try:
        from wagtail.contrib.routable_page.models import RoutablePageMixin
    except ImportError:
        RoutablePageMixin = None

    from wagtail.models import Page

    skip_prefixes = get_skip_url_prefixes()
    limit = get_pages_per_type()
    included_pages_by_type = {}
    default_site = _get_default_site()
    results = []
    pages = Page.objects.live().specific()
    for page in pages:
        if type(page) is Page:
            continue

        page_type = f"{page._meta.app_label}.{type(page).__name__}"
        if limit and included_pages_by_type.get(page_type, 0) >= limit:
            continue

        try:
            url = page.url
        except Exception:
            url = None
        if not url:
            continue
        parsed = urlparse(url)
        path = parsed.path
        if _should_skip_frontend_url(path, skip_prefixes):
            continue

        included_pages_by_type[page_type] = included_pages_by_type.get(page_type, 0) + 1

        page_site = None
        try:
            page_site = page.get_site()
        except Exception:
            page_site = None

        site_hostname = page_site.hostname if page_site else parsed.hostname or ""
        site_port = page_site.port if page_site else parsed.port
        is_cross_site = bool(default_site and page_site and page_site.pk != default_site.pk)

        results.append(
            _FrontendCandidate(
                url=path,
                source="page",
                page_type=page_type,
                page_title=page.title,
                name="",
                site_hostname=site_hostname,
                site_port=site_port,
                is_cross_site=is_cross_site,
            )
        )
        if FormMixin is not None and isinstance(page, FormMixin):
            results.append(
                _FrontendCandidate(
                    url=path,
                    source="page",
                    page_type=page_type,
                    page_title=page.title,
                    name="landing_page",
                    site_hostname=site_hostname,
                    site_port=site_port,
                    is_cross_site=is_cross_site,
                    requires_post=True,
                )
            )
        if RoutablePageMixin is not None and isinstance(page, RoutablePageMixin):
            results.extend(
                _discover_routable_page_candidates(
                    page,
                    path,
                    page_type,
                    skip_prefixes,
                    site_hostname,
                    site_port,
                    is_cross_site,
                )
            )

    return results


def _discover_routable_page_candidates(
    page,
    page_path,
    page_type,
    skip_prefixes=(),
    site_hostname="",
    site_port=None,
    is_cross_site=False,
):
    """Discover routable page candidates before classification."""
    results = []
    for pattern in type(page).get_subpage_urls():
        if hasattr(pattern.pattern, "_route"):
            sub_route = pattern.pattern._route
        elif hasattr(pattern.pattern, "_regex"):
            sub_route = clean_regex_route(pattern.pattern._regex)
        else:
            continue

        if not sub_route:
            continue

        full_url = _join_frontend_paths(page_path, sub_route)
        if _should_skip_frontend_url(full_url, skip_prefixes):
            continue
        results.append(
            _FrontendCandidate(
                url=full_url,
                source="page",
                page_type=page_type,
                page_title=page.title,
                name=pattern.name or "",
                site_hostname=site_hostname,
                site_port=site_port,
                is_cross_site=is_cross_site,
                has_parameters=route_has_parameters(sub_route),
                contains_regex=route_contains_regex(sub_route),
                resolved_url=_resolve_routable_page_url(page, pattern, page_path, sub_route),
            )
        )
    return results


def _discover_resolver_candidates():
    """Discover resolver-backed frontend candidates before classification."""
    resolver = get_resolver()
    skip_prefixes = get_skip_url_prefixes()
    results = []
    for route, name, namespace, _callback in walk_patterns(resolver.url_patterns):
        if route.startswith("admin/"):
            continue
        if route.startswith("django-admin/"):
            continue
        if namespace == "wagtail_unveil":
            continue
        if skip_prefixes and any(route.startswith(prefix) for prefix in skip_prefixes):
            continue

        normalized_route = clean_regex_route(route)
        url = normalized_route if normalized_route.startswith("/") else f"/{normalized_route}"
        results.append(
            _FrontendCandidate(
                url=url,
                source="resolver",
                page_type="",
                page_title="",
                name=name,
                has_parameters=route_has_parameters(normalized_route),
                contains_regex=route_contains_regex(normalized_route),
            )
        )
    return results


def _classify_frontend_candidate(candidate):
    """Classify a frontend candidate and assign any skip reason."""
    if candidate.is_cross_site:
        return _FrontendClassification(
            is_testable=False,
            skip_reason=_format_cross_site_skip_reason(candidate),
        )
    if candidate.requires_post:
        return _FrontendClassification(
            is_testable=False,
            skip_reason="Requires POST submission",
        )
    if candidate.has_parameters and not candidate.resolved_url:
        return _FrontendClassification(
            is_testable=False,
            skip_reason="URL requires parameters",
        )
    if candidate.contains_regex:
        return _FrontendClassification(
            is_testable=False,
            skip_reason="URL contains regex patterns",
        )
    return _FrontendClassification()


def _build_frontend_url(candidate, classification):
    """Emit a FrontendURL from candidate and classification state."""
    return FrontendURL(
        url=candidate.url,
        source=candidate.source,
        page_type=candidate.page_type,
        page_title=candidate.page_title,
        name=candidate.name,
        resolved_url=candidate.resolved_url,
        is_testable=classification.is_testable,
        skip_reason=classification.skip_reason,
    )


def get_frontend_urls():
    """Discover all frontend URLs from pages and the URL resolver.

    Returns a list of FrontendURL dataclass instances combining page URLs
    and non-admin resolver URLs.
    """
    results = []
    candidates = _discover_page_candidates() + _discover_resolver_candidates()
    for candidate in candidates:
        classification = _classify_frontend_candidate(candidate)
        results.append(_build_frontend_url(candidate, classification))
    return results
