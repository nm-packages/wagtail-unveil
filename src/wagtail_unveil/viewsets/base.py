from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import path
from wagtail.admin.views.reports import ReportView
from wagtail.admin.viewsets.base import ViewSet
from wagtail.admin.widgets.button import HeaderButton


def json_view_auth_required(request):
    """
    Check if the request requires authentication for JSON views.
    This function can be used to enforce token-based authentication
    for API endpoints in Wagtail Unveil reports.
    """
    # Require token authentication for other users
    required_token = getattr(settings, "WAGTAIL_UNVEIL_JSON_TOKEN", None)
    if not required_token:
        return HttpResponseForbidden("Access denied")

    # Check if user is authenticated and is a superuser
    if request.user.is_authenticated and request.user.is_superuser:
        # Allow access for authenticated superusers
        return True

    # Check for token in Authorization header or query parameter
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    token_from_header = None
    if auth_header.startswith("Bearer "):
        token_from_header = auth_header[7:]

    token_from_query = request.GET.get("token")
    provided_token = token_from_header or token_from_query

    if not provided_token or provided_token != required_token:
        return False

    return True


class UnveilReportView(ReportView):
    """Base view class for Unveil reports"""

    def get_header_buttons(self):
        """Get header buttons for the report, using the explicit api_slug attribute."""
        api_slug = getattr(self, "api_slug", "collection")
        api_url = f"/unveil/api/{api_slug}/"
        return [
            HeaderButton(
                label="Json View",
                icon_name="code",
                url=api_url,
                attrs={"target": "_blank"},
            ),
            HeaderButton(
                label="Run Checks",
                icon_name="link",
                attrs={"data-action": "check-urls"},
            ),
        ]


class UnveilReportViewSet(ViewSet):
    """Base ViewSet class for Unveil reports with JSON API support"""

    def as_json_view(self, request):
        """Return the report data as JSON"""

        if not json_view_auth_required(request):
            return HttpResponseForbidden("Access denied")

        # User is authenticated and has access, proceed with the JSON response
        view = self.index_view_class()
        queryset = view.get_queryset()
        data = [
            {
                "id": entry.id,
                "model_name": entry.model_name,
                "url_type": entry.url_type,
                "url": entry.url,
            }
            for entry in queryset
        ]
        return JsonResponse({"results": data})

    def get_urlpatterns(self):
        """Return the URL patterns for this ViewSet including JSON endpoint"""
        return [
            path("", self.index_view_class.as_view(), name="index"),
            path("results/", self.index_view_class.as_view(), name="results"),
        ]
