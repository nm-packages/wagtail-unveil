from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urlparse

from django.urls import get_resolver

from wagtail_unveil.discovery.utils import clean_regex_route, walk_patterns
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


def _get_page_urls():
    """Discover frontend URLs from live Wagtail pages.

    Uses Page.objects.live().specific() to get all live pages, returning
    their .url property. Skips the root Page model and pages without a URL.
    Form pages (FormMixin subclasses) also get a second non-testable entry
    for the landing page (POST response). RoutablePageMixin pages also get
    entries for each sub-route defined via @path() decorators.
    """
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
        if skip_prefixes and any(path.lstrip("/").startswith(p) for p in skip_prefixes):
            continue
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
        # Discover sub-routes from RoutablePageMixin pages
        if RoutablePageMixin is not None and isinstance(page, RoutablePageMixin):
            for sub_url_entry in _get_routable_sub_urls(page, path, page_type, skip_prefixes):
                results.append(sub_url_entry)

    limit = get_pages_per_type()
    if limit:
        # Group URLs by page (type + title), then limit to N pages per type.
        # Each page may have multiple URL entries (sub-routes, landing pages).
        page_urls = defaultdict(list)
        for frontend_url in results:
            key = (frontend_url.page_type, frontend_url.page_title)
            page_urls[key].append(frontend_url)
        # Group pages by type and take up to `limit` pages per type
        type_pages = defaultdict(list)
        for (page_type, _title), urls in page_urls.items():
            type_pages[page_type].append(urls)
        results = []
        for pages_in_type in type_pages.values():
            for page_entries in pages_in_type[:limit]:
                results.extend(page_entries)

    return results


def _get_routable_sub_urls(page, page_path, page_type, skip_prefixes=()):
    """Discover sub-route URLs from a RoutablePageMixin page.

    Inspects the page class's subpage_urls to find @path() decorated routes,
    and builds FrontendURL entries for each non-index sub-route.
    """
    results = []
    for pattern in type(page).get_subpage_urls():
        # Extract the route string from the URL pattern
        if hasattr(pattern.pattern, "_route"):
            sub_route = pattern.pattern._route
        elif hasattr(pattern.pattern, "_regex"):
            sub_route = clean_regex_route(pattern.pattern._regex)
        else:
            continue

        # Skip the index route (empty string) — already covered by base page URL
        if not sub_route:
            continue

        full_url = page_path.rstrip("/") + "/" + sub_route.lstrip("/")
        if skip_prefixes and any(full_url.lstrip("/").startswith(p) for p in skip_prefixes):
            continue
        has_parameters = "<" in sub_route
        if has_parameters:
            results.append(
                FrontendURL(
                    url=full_url,
                    source="page",
                    page_type=page_type,
                    page_title=page.title,
                    name=pattern.name or "",
                    is_testable=False,
                    skip_reason="URL requires parameters",
                )
            )
        else:
            results.append(
                FrontendURL(
                    url=full_url,
                    source="page",
                    page_type=page_type,
                    page_title=page.title,
                    name=pattern.name or "",
                )
            )
    return results


def _get_resolver_frontend_urls():
    """Discover frontend URLs from Django's URL resolver (non-admin routes).

    Reuses walk_patterns() but excludes admin/ routes and unveil's own
    namespaces. Parameterized and regex URLs are marked as non-testable.
    """
    resolver = get_resolver()
    skip_prefixes = get_skip_url_prefixes()
    results = []
    for route, name, namespace, _callback in walk_patterns(resolver.url_patterns):
        # Exclude admin routes
        if route.startswith("admin/"):
            continue
        # Exclude Django admin
        if route.startswith("django-admin/"):
            continue
        # Exclude unveil's own namespaces
        if namespace == "wagtail_unveil":
            continue
        # User-configured prefix exclusions
        if skip_prefixes and any(route.startswith(p) for p in skip_prefixes):
            continue

        route = clean_regex_route(route)
        is_testable = True
        skip_reason = ""

        # Parameterized URLs are not directly testable
        if "<" in route:
            is_testable = False
            skip_reason = "URL requires parameters"
        elif "(" in route:
            is_testable = False
            skip_reason = "URL contains regex patterns"

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
