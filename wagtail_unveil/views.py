import os

from django.http import JsonResponse

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
            }
            for u in urls
        ],
        "count": len(urls),
    }
    return JsonResponse(data)
