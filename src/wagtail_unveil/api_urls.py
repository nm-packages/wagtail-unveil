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
# Format: (url_path, viewset_class, endpoint_name)
API_ENDPOINTS = [
    ("collection", UnveilCollectionReportViewSet, "collection"),
    ("document", UnveilDocumentReportViewSet, "document"),
    ("form", UnveilFormReportViewSet, "form"),
    ("generic", UnveilGenericReportViewSet, "generic"),
    ("image", UnveilImageReportViewSet, "image"),
    ("locale", UnveilLocaleReportViewSet, "locale"),
    ("modeladmin", UnveilModelAdminReportViewSet, "modeladmin"),
    ("page", UnveilPageReportViewSet, "page"),
    ("redirect", UnveilRedirectReportViewSet, "redirect"),
    ("search-promotion", UnveilSearchPromotionReportViewSet, "search-promotion"),
    ("settings", UnveilSettingsReportViewSet, "settings"),
    ("site", UnveilSiteReportViewSet, "site"),
    ("snippet", UnveilSnippetReportViewSet, "snippet"),
    ("user", UnveilUserReportViewSet, "user"),
    ("admin", UnveilAdminReportViewSet, "admin"),
    ("workflow", UnveilWorkflowReportViewSet, "workflow"),
    ("workflow-task", UnveilWorkflowTaskReportViewSet, "workflow-task"),
]


def api_index_view(request):
    """Return a list of all available API endpoints."""
    if not json_view_auth_required(request):
        return HttpResponseForbidden("Access denied")

    endpoints = {
        endpoint_name: request.build_absolute_uri(f"{url_path}/")
        for url_path, _, endpoint_name in API_ENDPOINTS
    }
    return JsonResponse({"endpoints": endpoints})


urlpatterns = [
    path("", api_index_view),
]

# Generate JSON API endpoint URL
for url_path, viewset_class, _ in API_ENDPOINTS:
    viewset_instance = viewset_class()
    urlpatterns.append(path(f"{url_path}/", viewset_instance.as_json_view))
