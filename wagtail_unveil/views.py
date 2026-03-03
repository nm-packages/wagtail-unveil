from importlib.metadata import PackageNotFoundError, version

from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from wagtail.admin.auth import user_passes_test

from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.frontend import get_frontend_urls
from wagtail_unveil.settings import get_api_key, get_pages_per_type


def _json_error(message, *, status):
    """Return a JSON error response with a consistent shape."""
    return JsonResponse({"error": message}, status=status)


def _authenticate_api_request(request):
    """Validate the configured API key against the request Authorization header."""
    auth_header = request.headers.get("Authorization", "")

    if auth_header:
        api_key = get_api_key()
        if not api_key:
            return _json_error("WAGTAIL_UNVEIL_API_KEY is not set", status=500)

        if auth_header != f"Bearer {api_key}":
            return _json_error("Invalid or missing API key", status=403)

        return None

    user = getattr(request, "user", None)
    if settings.DEBUG and user and user.is_authenticated and user.is_superuser:
        return None

    return _json_error("Invalid or missing API key", status=403)


def _serialize_backend_url(url):
    """Serialize a BackendURL dataclass for JSON responses."""
    return {
        "route": url.route,
        "name": url.name,
        "namespace": url.namespace,
        "has_parameters": url.has_parameters,
        "view_name": url.view_name,
        "is_testable": url.is_testable,
        "skip_reason": url.skip_reason,
        "resolved_route": url.resolved_route,
    }


def _serialize_frontend_url(url):
    """Serialize a FrontendURL dataclass for JSON responses."""
    return {
        "url": url.url,
        "source": url.source,
        "page_type": url.page_type,
        "page_title": url.page_title,
        "name": url.name,
        "is_testable": url.is_testable,
        "skip_reason": url.skip_reason,
    }


def _get_package_version():
    """Return the installed wagtail-unveil package version, or an empty string."""
    try:
        return version("wagtail-unveil")
    except PackageNotFoundError:
        return ""


def _build_urls_metadata(urls, *, applied_filter):
    """Build metadata describing how a URL payload was produced."""
    testable_count = sum(1 for url in urls if url.is_testable)
    return {
        "generated_at": timezone.now().isoformat(),
        "applied_filter": applied_filter,
        "total_count": len(urls),
        "testable_count": testable_count,
        "untestable_count": len(urls) - testable_count,
        "package_version": _get_package_version(),
    }


def _build_urls_json_response(urls, serializer, *, applied_filter=None):
    """Serialize URL entries and wrap them in the standard JSON payload."""
    data = {
        "urls": [serializer(url) for url in urls],
        "count": len(urls),
        "metadata": _build_urls_metadata(urls, applied_filter=applied_filter),
    }
    return JsonResponse(data)


def admin_urls_json(request):
    """Return admin URLs as JSON, protected by API key."""
    auth_error = _authenticate_api_request(request)
    if auth_error is not None:
        return auth_error

    urls = get_admin_urls()

    url_filter = request.GET.get("filter")
    applied_filter = None
    if url_filter == "static":
        urls = [u for u in urls if not u.has_parameters]
        applied_filter = url_filter
    elif url_filter == "parameterized":
        urls = [u for u in urls if u.has_parameters]
        applied_filter = url_filter

    return _build_urls_json_response(urls, _serialize_backend_url, applied_filter=applied_filter)


@user_passes_test(lambda u: u.is_superuser)
def admin_urls_report(request):
    """Render an HTML report of all admin URLs. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    context = {
        "api_url": reverse("wagtail_unveil:api_backend_urls"),
        "report_kind": "backend",
    }
    return render(request, "wagtail_unveil/admin_urls_report.html", context)


def frontend_urls_json(request):
    """Return frontend URLs as JSON, protected by API key."""
    auth_error = _authenticate_api_request(request)
    if auth_error is not None:
        return auth_error

    urls = get_frontend_urls()

    source_filter = request.GET.get("filter")
    applied_filter = None
    if source_filter == "pages":
        urls = [u for u in urls if u.source == "page"]
        applied_filter = source_filter
    elif source_filter == "resolver":
        urls = [u for u in urls if u.source == "resolver"]
        applied_filter = source_filter

    return _build_urls_json_response(urls, _serialize_frontend_url, applied_filter=applied_filter)


@user_passes_test(lambda u: u.is_superuser)
def frontend_urls_report(request):
    """Render an HTML report of all frontend URLs. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    pages_per_type = get_pages_per_type()
    context = {
        "api_url": reverse("wagtail_unveil:api_frontend_urls"),
        "report_kind": "frontend",
        "pages_per_type": pages_per_type,
    }
    return render(request, "wagtail_unveil/frontend_urls_report.html", context)
