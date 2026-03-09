import platform
from datetime import datetime, time
from datetime import timezone as datetime_timezone
from email.utils import format_datetime
from importlib.metadata import PackageNotFoundError, version

import wagtail
from django import get_version as get_django_version
from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from wagtail.admin.auth import user_passes_test

from wagtail_unveil.api_contract import (
    APIVersionContract,
    get_api_contract,
    get_latest_stable_api_contract,
    get_latest_stable_api_version,
)
from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.frontend import get_frontend_urls
from wagtail_unveil.settings import get_api_key, get_pages_per_type, get_setting_diagnostics


def _json_error(message, *, status):
    """Return a JSON error response with a consistent shape."""
    return JsonResponse({"error": message}, status=status)


def _authenticate_api_request(request):
    """Validate the configured API key against the request Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ", 1)
    is_bearer_auth = len(parts) == 2 and parts[0].lower() == "bearer"

    if is_bearer_auth:
        api_key = get_api_key()
        if not api_key:
            return _json_error("WAGTAIL_UNVEIL_API_KEY is not set", status=500)

        if parts[1] != api_key:
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


def _serialize_api_lifecycle(contract: APIVersionContract):
    """Serialize lifecycle metadata for API contract responses."""
    return {
        "status": contract.status,
        "deprecated_on": contract.deprecated_on.isoformat() if contract.deprecated_on else None,
        "sunset_on": contract.sunset_on.isoformat() if contract.sunset_on else None,
    }


def _build_urls_metadata(urls, *, applied_filter, contract: APIVersionContract):
    """Build metadata describing how a URL payload was produced."""
    testable_count = sum(1 for url in urls if url.is_testable)
    return {
        "api_version": contract.version,
        "api_lifecycle": _serialize_api_lifecycle(contract),
        "generated_at": timezone.now().isoformat(),
        "applied_filter": applied_filter,
        "total_count": len(urls),
        "testable_count": testable_count,
        "untestable_count": len(urls) - testable_count,
        "package_version": _get_package_version(),
    }


def _apply_lifecycle_headers(response: JsonResponse, contract: APIVersionContract):
    """Attach deprecation headers for deprecated API versions."""
    if contract.status != "deprecated":
        return response

    response["Deprecation"] = "true"
    if contract.sunset_on is not None:
        sunset_at = datetime.combine(contract.sunset_on, time(23, 59, 59), tzinfo=datetime_timezone.utc)
        response["Sunset"] = format_datetime(sunset_at, usegmt=True)

    return response


def _build_urls_json_response(urls, serializer, *, applied_filter=None, contract: APIVersionContract):
    """Serialize URL entries and wrap them in the standard JSON payload."""
    data = {
        "urls": [serializer(url) for url in urls],
        "count": len(urls),
        "metadata": _build_urls_metadata(urls, applied_filter=applied_filter, contract=contract),
    }
    response = JsonResponse(data)
    return _apply_lifecycle_headers(response, contract)


def _get_display_package_version():
    """Return the installed package version or a useful placeholder."""
    package_version = _get_package_version()
    if package_version:
        return package_version
    return "Unknown"


def _build_lifecycle_detail(contract: APIVersionContract):
    """Render lifecycle detail text for diagnostics output."""
    details = []
    if contract.deprecated_on is not None:
        details.append(f"Deprecated on {contract.deprecated_on.isoformat()}")
    if contract.sunset_on is not None:
        details.append(f"Sunsets on {contract.sunset_on.isoformat()}")
    if not details:
        return "Current stable contract."
    return ". ".join(details)


def _build_settings_report_context():
    """Build diagnostics content for the settings page."""
    contract = get_latest_stable_api_contract()
    api_key = get_api_key()
    return {
        "package_settings": get_setting_diagnostics(),
        "runtime_entries": [
            {
                "label": "DEBUG",
                "value": repr(settings.DEBUG),
                "detail": "Controls access to the HTML reports.",
            },
            {
                "label": "HTML report access",
                "value": "Enabled" if settings.DEBUG else "Disabled",
                "detail": "Report pages require a superuser and DEBUG=True.",
            },
            {
                "label": "Superuser session API access",
                "value": "Enabled" if settings.DEBUG else "Disabled",
                "detail": "Session-based JSON access is only allowed for superusers when DEBUG=True.",
            },
            {
                "label": "Bearer API auth",
                "value": "Configured" if api_key else "Not configured",
                "detail": "Uses WAGTAIL_UNVEIL_API_KEY.",
            },
        ],
        "version_entries": [
            {
                "label": "wagtail-unveil",
                "value": _get_display_package_version(),
                "detail": "Installed package version metadata.",
            },
            {
                "label": "Django",
                "value": get_django_version(),
                "detail": "Runtime framework version.",
            },
            {
                "label": "Wagtail",
                "value": wagtail.__version__,
                "detail": "Runtime CMS version.",
            },
            {
                "label": "Python",
                "value": platform.python_version(),
                "detail": "Interpreter version used by this process.",
            },
        ],
        "url_entries": [
            {
                "label": "Latest stable API version",
                "value": contract.version,
                "detail": "Selected from API_VERSION_REGISTRY.",
            },
            {
                "label": "API lifecycle",
                "value": contract.status,
                "detail": _build_lifecycle_detail(contract),
            },
            {
                "label": "Backend API",
                "value": reverse(f"wagtail_unveil:{contract.backend_url_name}"),
                "detail": f"URL name: wagtail_unveil:{contract.backend_url_name}",
            },
            {
                "label": "Frontend API",
                "value": reverse(f"wagtail_unveil:{contract.frontend_url_name}"),
                "detail": f"URL name: wagtail_unveil:{contract.frontend_url_name}",
            },
            {
                "label": "Backend URLs report",
                "value": reverse("wagtail_unveil:report_backend_urls"),
                "detail": "URL name: wagtail_unveil:report_backend_urls",
            },
            {
                "label": "Frontend URLs report",
                "value": reverse("wagtail_unveil:report_frontend_urls"),
                "detail": "URL name: wagtail_unveil:report_frontend_urls",
            },
            {
                "label": "Settings report",
                "value": reverse("wagtail_unveil:report_settings"),
                "detail": "URL name: wagtail_unveil:report_settings",
            },
        ],
    }


def _get_backend_urls_for_version(api_version):
    """Return backend URL objects for a specific API version."""
    # Future API versions can customize discovery behavior here.
    return get_admin_urls()


def _get_frontend_urls_for_version(api_version):
    """Return frontend URL objects for a specific API version."""
    # Future API versions can customize discovery behavior here.
    return get_frontend_urls()


def _get_backend_serializer_for_version(api_version):
    """Return backend serializer function for a specific API version."""
    # Future API versions can customize response fields here.
    return _serialize_backend_url


def _get_frontend_serializer_for_version(api_version):
    """Return frontend serializer function for a specific API version."""
    # Future API versions can customize response fields here.
    return _serialize_frontend_url


def _admin_urls_json_for_version(request, api_version):
    """Return admin URLs as JSON for a specific API version."""
    contract = get_api_contract(api_version)
    auth_error = _authenticate_api_request(request)
    if auth_error is not None:
        return auth_error

    urls = _get_backend_urls_for_version(api_version)
    serializer = _get_backend_serializer_for_version(api_version)

    url_filter = request.GET.get("filter")
    applied_filter = None
    if url_filter == "static":
        urls = [u for u in urls if not u.has_parameters]
        applied_filter = url_filter
    elif url_filter == "parameterized":
        urls = [u for u in urls if u.has_parameters]
        applied_filter = url_filter

    return _build_urls_json_response(
        urls,
        serializer,
        applied_filter=applied_filter,
        contract=contract,
    )


def _frontend_urls_json_for_version(request, api_version):
    """Return frontend URLs as JSON for a specific API version."""
    contract = get_api_contract(api_version)
    auth_error = _authenticate_api_request(request)
    if auth_error is not None:
        return auth_error

    urls = _get_frontend_urls_for_version(api_version)
    serializer = _get_frontend_serializer_for_version(api_version)

    source_filter = request.GET.get("filter")
    applied_filter = None
    if source_filter == "pages":
        urls = [u for u in urls if u.source == "page"]
        applied_filter = source_filter
    elif source_filter == "resolver":
        urls = [u for u in urls if u.source == "resolver"]
        applied_filter = source_filter

    return _build_urls_json_response(
        urls,
        serializer,
        applied_filter=applied_filter,
        contract=contract,
    )


def build_admin_urls_json_view(api_version):
    """Build a Django view callable bound to a specific backend API version."""

    def view(request):
        return _admin_urls_json_for_version(request, api_version)

    view.__name__ = f"admin_urls_json_{api_version}"
    return view


def build_frontend_urls_json_view(api_version):
    """Build a Django view callable bound to a specific frontend API version."""

    def view(request):
        return _frontend_urls_json_for_version(request, api_version)

    view.__name__ = f"frontend_urls_json_{api_version}"
    return view


# Backward-compatible callables bound to the current latest stable API version.
admin_urls_json = build_admin_urls_json_view(get_latest_stable_api_version())
frontend_urls_json = build_frontend_urls_json_view(get_latest_stable_api_version())


@user_passes_test(lambda u: u.is_superuser)
def admin_urls_report(request):
    """Render an HTML report of all admin URLs. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    contract = get_latest_stable_api_contract()
    context = {
        "api_url": reverse(f"wagtail_unveil:{contract.backend_url_name}"),
        "report_kind": "backend",
        "active_report": "backend",
    }
    return render(request, "wagtail_unveil/admin_urls_report.html", context)


@user_passes_test(lambda u: u.is_superuser)
def frontend_urls_report(request):
    """Render an HTML report of all frontend URLs. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    contract = get_latest_stable_api_contract()
    pages_per_type = get_pages_per_type()
    context = {
        "api_url": reverse(f"wagtail_unveil:{contract.frontend_url_name}"),
        "report_kind": "frontend",
        "pages_per_type": pages_per_type,
        "active_report": "frontend",
    }
    return render(request, "wagtail_unveil/frontend_urls_report.html", context)


@user_passes_test(lambda u: u.is_superuser)
def settings_report(request):
    """Render an HTML settings and diagnostics page. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    context = {
        **_build_settings_report_context(),
        "active_report": "settings",
    }
    return render(request, "wagtail_unveil/settings_report.html", context)
