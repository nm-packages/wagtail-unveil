from django.http import JsonResponse, HttpResponseForbidden
from django.urls import path

from wagtail_unveil.viewsets.admin_report import UnveilAdminReportViewSet
from wagtail_unveil.viewsets.base import json_view_auth_required
from wagtail_unveil.viewsets.collection_report import UnveilCollectionReportViewSet
from wagtail_unveil.viewsets.document_report import UnveilDocumentReportViewSet
from wagtail_unveil.viewsets.form_report import UnveilFormReportViewSet
from wagtail_unveil.viewsets.generic_report import UnveilGenericReportViewSet
from wagtail_unveil.viewsets.image_report import UnveilImageReportViewSet
from wagtail_unveil.viewsets.locale_report import UnveilLocaleReportViewSet
from wagtail_unveil.viewsets.modeladmin_report import UnveilModelAdminReportViewSet
from wagtail_unveil.viewsets.page_report import UnveilPageReportViewSet
from wagtail_unveil.viewsets.redirect_report import UnveilRedirectReportViewSet
from wagtail_unveil.viewsets.search_promotion_report import (
    UnveilSearchPromotionReportViewSet,
)
from wagtail_unveil.viewsets.settings_report import UnveilSettingsReportViewSet
from wagtail_unveil.viewsets.site_report import UnveilSiteReportViewSet
from wagtail_unveil.viewsets.snippet_report import UnveilSnippetReportViewSet
from wagtail_unveil.viewsets.user_report import UnveilUserReportViewSet
from wagtail_unveil.viewsets.workflow_report import UnveilWorkflowReportViewSet
from wagtail_unveil.viewsets.workflow_task_report import UnveilWorkflowTaskReportViewSet


# Registry of API endpoints
# Format: (url_path, viewset_class)
API_ENDPOINTS = [
    ("collection", UnveilCollectionReportViewSet),
    ("document", UnveilDocumentReportViewSet),
    ("form", UnveilFormReportViewSet),
    ("generic", UnveilGenericReportViewSet),
    ("image", UnveilImageReportViewSet),
    ("locale", UnveilLocaleReportViewSet),
    ("modeladmin", UnveilModelAdminReportViewSet),
    ("page", UnveilPageReportViewSet),
    ("redirect", UnveilRedirectReportViewSet),
    ("search-promotion", UnveilSearchPromotionReportViewSet),
    ("settings", UnveilSettingsReportViewSet),
    ("site", UnveilSiteReportViewSet),
    ("snippet", UnveilSnippetReportViewSet),
    ("user", UnveilUserReportViewSet),
    ("admin", UnveilAdminReportViewSet),
    ("workflow", UnveilWorkflowReportViewSet),
    ("workflow-task", UnveilWorkflowTaskReportViewSet),
]


def api_index_view(request):
    """
    Return a list of all available API endpoints with their absolute URLs.

    This view provides a discovery endpoint that lists all available API endpoints
    in the wagtail-unveil API, making it easier for clients to explore the API.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: Dictionary with 'endpoints' key containing URL mappings
        HttpResponseForbidden: If authentication/authorization fails
    """
    # Check if the user is authorized to access the API
    auth_result = json_view_auth_required(request)
    if not auth_result:
        return HttpResponseForbidden("Access denied")

    # Build absolute URLs for each endpoint
    endpoint_urls = {}
    for endpoint_path, _ in API_ENDPOINTS:
        absolute_url = request.build_absolute_uri(f"{endpoint_path}/")
        endpoint_urls[endpoint_path] = absolute_url

    return JsonResponse({"endpoints": endpoint_urls})


urlpatterns = [
    path("", api_index_view),
]

# Generate JSON API endpoint URL
for url_path, viewset_class in API_ENDPOINTS:
    viewset_instance = viewset_class()
    urlpatterns.append(path(f"{url_path}/", viewset_instance.as_json_view))
