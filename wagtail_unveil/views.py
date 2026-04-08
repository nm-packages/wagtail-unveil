import platform
from datetime import datetime, time
from datetime import timezone as datetime_timezone
from email.utils import format_datetime
from importlib.metadata import PackageNotFoundError, version
from secrets import compare_digest, token_urlsafe

import wagtail
from django import get_version as get_django_version
from django.conf import settings
from django.core import signing
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import patch_vary_headers
from wagtail.admin.auth import user_passes_test

from wagtail_unveil.api_contract import (
    APIVersionContract,
    get_api_contract,
    get_latest_stable_api_contract,
    get_latest_stable_api_version,
)
from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.frontend import get_frontend_urls
from wagtail_unveil.settings import (
    get_api_key,
    get_enable_production_reports,
    get_setting_diagnostics,
    is_report_ui_enabled,
)
from wagtail_unveil.platform_data import PlatformSnapshot, get_platform_snapshot

# Shared API response and authentication helpers

REPORT_ACCESS_HEADER = "X-Wagtail-Unveil-Report-Access"
REPORT_ACCESS_SALT = "wagtail_unveil.report_api_access"
REPORT_ACCESS_MAX_AGE = 300
REPORT_ACCESS_SESSION_NONCE_KEY = "_wagtail_unveil_report_access_nonce"


def _apply_private_no_store_headers(response, *, vary_headers=()):
    """Mark a response as private and non-cacheable."""
    response["Cache-Control"] = "private, no-store"
    if vary_headers:
        patch_vary_headers(response, vary_headers)
    return response


def _apply_api_cache_headers(response):
    """Mark API responses as private and non-cacheable."""
    return _apply_private_no_store_headers(response, vary_headers=("Authorization", "Cookie"))


def _json_error(message, *, status):
    """Return a JSON error response with a consistent shape."""
    response = JsonResponse({"error": message}, status=status)
    return _apply_api_cache_headers(response)


def _get_report_access_session_nonce(request, *, create=False):
    """Return the session-bound nonce used to validate report access tokens."""
    session = getattr(request, "session", None)
    if session is None:
        return ""

    if hasattr(session, "get"):
        nonce = session.get(REPORT_ACCESS_SESSION_NONCE_KEY, "")
    else:
        nonce = getattr(session, REPORT_ACCESS_SESSION_NONCE_KEY, "")

    if nonce or not create:
        return nonce or ""

    nonce = token_urlsafe(32)
    if hasattr(session, "__setitem__"):
        session[REPORT_ACCESS_SESSION_NONCE_KEY] = nonce
    else:
        setattr(session, REPORT_ACCESS_SESSION_NONCE_KEY, nonce)
    return nonce


def _build_report_access_token(request):
    """Build a short-lived signed token for report-triggered API access."""
    return signing.dumps(
        {
            "purpose": "report-api-access",
            "user_id": getattr(request.user, "pk", None),
            "session_nonce": _get_report_access_session_nonce(request, create=True),
        },
        salt=REPORT_ACCESS_SALT,
    )


def _has_valid_report_access_token(request):
    """Return True when the request carries a valid signed report access token."""
    token = request.headers.get(REPORT_ACCESS_HEADER, "")
    if not token:
        return False

    try:
        claims = signing.loads(token, salt=REPORT_ACCESS_SALT, max_age=REPORT_ACCESS_MAX_AGE)
    except signing.SignatureExpired:
        return False
    except signing.BadSignature:
        return False

    if not isinstance(claims, dict):
        return False

    user = getattr(request, "user", None)
    session_nonce = _get_report_access_session_nonce(request, create=False)

    if claims.get("purpose") != "report-api-access":
        return False
    if claims.get("user_id") != getattr(user, "pk", None):
        return False
    if not session_nonce:
        return False
    return compare_digest(claims.get("session_nonce", ""), session_nonce)


def _authenticate_api_request(request, *, allow_debug_superuser_session=True):
    """Validate the configured API key against the request Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ", 1)
    is_bearer_auth = len(parts) == 2 and parts[0].lower() == "bearer"

    if is_bearer_auth:
        api_key = get_api_key()
        if not api_key:
            return _json_error("WAGTAIL_UNVEIL_API_KEY is not set", status=500)

        if not compare_digest(parts[1], api_key):
            return _json_error("Invalid or missing API key", status=403)

        return None

    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_superuser:
        if allow_debug_superuser_session and settings.DEBUG:
            return None
        if allow_debug_superuser_session and get_enable_production_reports() and _has_valid_report_access_token(request):
            return None

    return _json_error("Invalid or missing API key", status=403)


# Shared serialization and metadata helpers


def _serialize_backend_url(url):
    """Serialize a BackendURL dataclass for JSON responses."""
    return {
        "route": url.route,
        "name": url.name,
        "namespace": url.namespace,
        "has_parameters": url.has_parameters,
        "view_name": url.view_name,
        "page_type": url.page_type,
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
        "resolved_url": url.resolved_url,
        "query_params": url.query_params,
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


def _build_platform_metadata(*, contract: APIVersionContract):
    """Build metadata describing how a platform payload was produced."""
    return {
        "api_version": contract.version,
        "api_lifecycle": _serialize_api_lifecycle(contract),
        "generated_at": timezone.now().isoformat(),
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
    response = _apply_api_cache_headers(JsonResponse(data))
    return _apply_lifecycle_headers(response, contract)


def _serialize_platform_snapshot(snapshot: PlatformSnapshot):
    """Serialize platform runtime and dependency inventory for JSON responses."""
    return {
        "platform": {
            "runtime": {
                "python_version": snapshot.runtime.python_version,
                "python_implementation": snapshot.runtime.python_implementation,
                "django_version": snapshot.runtime.django_version,
                "wagtail_version": snapshot.runtime.wagtail_version,
            },
            "python_dependencies": {
                "source": {
                    "path": snapshot.dependency_source.path,
                    "format": snapshot.dependency_source.format,
                },
                "packages": [
                    {
                        "name": dependency.name,
                        "specifier": dependency.specifier,
                        "installed_version": dependency.installed_version,
                        "is_installed": dependency.is_installed,
                        "source_kind": dependency.source_kind,
                        "source_name": dependency.source_name,
                    }
                    for dependency in snapshot.python_dependencies
                ],
            },
            "warnings": snapshot.warnings,
        },
    }


def _build_platform_json_response(snapshot: PlatformSnapshot, *, contract: APIVersionContract):
    """Serialize platform data and wrap it in the versioned JSON payload."""
    data = {
        **_serialize_platform_snapshot(snapshot),
        "metadata": _build_platform_metadata(contract=contract),
    }
    response = JsonResponse(data)
    return _apply_lifecycle_headers(response, contract)


# Settings report helpers


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
    production_reports_enabled = get_enable_production_reports()
    reports_enabled = is_report_ui_enabled()
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
                "value": "Enabled" if reports_enabled else "Disabled",
                "detail": (
                    "Report pages require a superuser and either DEBUG=True or "
                    "WAGTAIL_UNVEIL_ENABLE_PRODUCTION_REPORTS=True."
                ),
            },
            {
                "label": "Superuser session API access",
                "value": "Enabled" if settings.DEBUG or production_reports_enabled else "Disabled",
                "detail": (
                    "Session-based JSON access is allowed for URL discovery endpoints "
                    "for superusers in DEBUG mode, or for signed report requests when "
                    "production reports are enabled. The platform API still requires "
                    "Bearer authentication."
                ),
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
                "label": "Platform API",
                "value": reverse(f"wagtail_unveil:{contract.platform_url_name}"),
                "detail": f"URL name: wagtail_unveil:{contract.platform_url_name}",
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


# Version-specific API dispatch helpers


def _get_backend_urls_for_version(_api_version):
    """Return backend URL objects for a specific API version."""
    # Future API versions can customize discovery behavior here.
    return get_admin_urls()


def _get_frontend_urls_for_version(_api_version):
    """Return frontend URL objects for a specific API version."""
    # Future API versions can customize discovery behavior here.
    return get_frontend_urls()


def _get_backend_serializer_for_version(_api_version):
    """Return backend serializer function for a specific API version."""
    # Future API versions can customize response fields here.
    return _serialize_backend_url


def _get_frontend_serializer_for_version(_api_version):
    """Return frontend serializer function for a specific API version."""
    # Future API versions can customize response fields here.
    return _serialize_frontend_url


def _get_platform_snapshot_for_version(_api_version):
    """Return platform runtime and dependency metadata for a specific API version."""
    return get_platform_snapshot()


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


def _platform_json_for_version(request, api_version):
    """Return platform runtime and dependency metadata for a specific API version."""
    contract = get_api_contract(api_version)
    auth_error = _authenticate_api_request(request, allow_debug_superuser_session=False)
    if auth_error is not None:
        return auth_error

    snapshot = _get_platform_snapshot_for_version(api_version)
    return _build_platform_json_response(snapshot, contract=contract)


# JSON view builders


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


def build_platform_json_view(api_version):
    """Build a Django view callable bound to a specific platform API version."""

    def view(request):
        return _platform_json_for_version(request, api_version)

    view.__name__ = f"platform_json_{api_version}"
    return view


# Backward-compatible callables bound to the current latest stable API version.
admin_urls_json = build_admin_urls_json_view(get_latest_stable_api_version())
frontend_urls_json = build_frontend_urls_json_view(get_latest_stable_api_version())
platform_json = build_platform_json_view(get_latest_stable_api_version())


# HTML report views


@user_passes_test(lambda u: u.is_superuser)
def backend_urls_report(request):
    """Render an HTML report of all backend URLs for eligible superusers."""
    if not is_report_ui_enabled():
        return HttpResponseNotFound()

    contract = get_latest_stable_api_contract()
    context = {
        "api_url": reverse(f"wagtail_unveil:{contract.backend_url_name}"),
        "report_kind": "backend",
        "active_report": "backend",
        "report_access_token": _build_report_access_token(request),
    }
    response = render(request, "wagtail_unveil/backend_urls_report.html", context)
    return _apply_private_no_store_headers(response, vary_headers=("Cookie",))


@user_passes_test(lambda u: u.is_superuser)
def frontend_urls_report(request):
    """Render an HTML report of all frontend URLs for eligible superusers."""
    if not is_report_ui_enabled():
        return HttpResponseNotFound()

    contract = get_latest_stable_api_contract()
    context = {
        "api_url": reverse(f"wagtail_unveil:{contract.frontend_url_name}"),
        "report_kind": "frontend",
        "active_report": "frontend",
        "report_access_token": _build_report_access_token(request),
    }
    response = render(request, "wagtail_unveil/frontend_urls_report.html", context)
    return _apply_private_no_store_headers(response, vary_headers=("Cookie",))


@user_passes_test(lambda u: u.is_superuser)
def settings_report(request):
    """Render an HTML settings and diagnostics page for eligible superusers."""
    if not is_report_ui_enabled():
        return HttpResponseNotFound()

    context = {
        **_build_settings_report_context(),
        "active_report": "settings",
    }
    response = render(request, "wagtail_unveil/settings_report.html", context)
    return _apply_private_no_store_headers(response, vary_headers=("Cookie",))
