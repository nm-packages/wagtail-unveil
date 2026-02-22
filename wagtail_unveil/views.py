import os

from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from wagtail.admin.auth import user_passes_test

from wagtail_unveil.urls import get_admin_urls


def admin_urls_json(request):
    """Return admin URLs as JSON, protected by API key."""
    api_key = os.environ.get("WAGTAIL_UNVEIL_API_KEY")
    if not api_key:
        return JsonResponse(
            {"error": "WAGTAIL_UNVEIL_API_KEY environment variable is not set"},
            status=500,
        )

    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {api_key}":
        return JsonResponse({"error": "Invalid or missing API key"}, status=403)

    urls = get_admin_urls()

    url_filter = request.GET.get("filter")
    if url_filter == "static":
        urls = [u for u in urls if not u.has_parameters]
    elif url_filter == "parameterized":
        urls = [u for u in urls if u.has_parameters]

    data = {
        "urls": [
            {
                "route": u.route,
                "name": u.name,
                "namespace": u.namespace,
                "has_parameters": u.has_parameters,
                "view_name": u.view_name,
                "is_testable": u.is_testable,
                "skip_reason": u.skip_reason,
                "resolved_route": u.resolved_route,
            }
            for u in urls
        ],
        "count": len(urls),
    }
    return JsonResponse(data)


@user_passes_test(lambda u: u.is_superuser)
def admin_urls_report(request):
    """Render an HTML report of all admin URLs. Only available when DEBUG=True."""
    if not settings.DEBUG:
        return HttpResponseNotFound()

    urls = get_admin_urls()
    static_count = sum(1 for u in urls if not u.has_parameters)
    context = {
        "urls": urls,
        "url_count": len(urls),
        "static_count": static_count,
        "parameterized_count": len(urls) - static_count,
    }
    return render(request, "wagtail_unveil/admin_urls_report.html", context)
