from dataclasses import dataclass
from urllib.parse import urlparse

from django.urls import get_resolver

from wagtail_unveil.discovery.utils import clean_regex_route, route_contains_regex, route_has_parameters, walk_patterns
from wagtail_unveil.settings import get_pages_per_type, get_skip_url_prefixes


@dataclass
class FrontendURL:
    url: str
    source: str
    page_type: str
    page_title: str
    name: str
    is_testable: bool = True
    skip_reason: str = ""


@dataclass
class _FrontendCandidate:
    url: str
    source: str
    page_type: str
    page_title: str
    name: str
    has_parameters: bool = False
    contains_regex: bool = False
    requires_post: bool = False


@dataclass
class _FrontendClassification:
    is_testable: bool = True
    skip_reason: str = ""


def _should_skip_frontend_url(url, skip_prefixes):
    """Return True when a frontend URL matches configured skip prefixes."""
    return bool(skip_prefixes and any(url.lstrip("/").startswith(prefix) for prefix in skip_prefixes))


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
        results.append(
            _FrontendCandidate(
                url=path,
                source="page",
                page_type=page_type,
                page_title=page.title,
                name="",
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
                    requires_post=True,
                )
            )
        if RoutablePageMixin is not None and isinstance(page, RoutablePageMixin):
            results.extend(_discover_routable_page_candidates(page, path, page_type, skip_prefixes))

    return results


def _discover_routable_page_candidates(page, page_path, page_type, skip_prefixes=()):
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

        full_url = page_path.rstrip("/") + "/" + sub_route.lstrip("/")
        if _should_skip_frontend_url(full_url, skip_prefixes):
            continue
        results.append(
            _FrontendCandidate(
                url=full_url,
                source="page",
                page_type=page_type,
                page_title=page.title,
                name=pattern.name or "",
                has_parameters=route_has_parameters(sub_route),
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
    if candidate.requires_post:
        return _FrontendClassification(
            is_testable=False,
            skip_reason="Requires POST submission",
        )
    if candidate.has_parameters:
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
