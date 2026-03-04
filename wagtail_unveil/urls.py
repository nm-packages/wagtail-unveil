from django.urls import path

from wagtail_unveil.views import admin_urls_json, admin_urls_report, frontend_urls_json, frontend_urls_report

app_name = "wagtail_unveil"

urlpatterns = [
    path("api/v1/backend-urls/", admin_urls_json, name="api_v1_backend_urls"),
    path("api/v1/frontend-urls/", frontend_urls_json, name="api_v1_frontend_urls"),
    path("report/backend-urls/", admin_urls_report, name="report_backend_urls"),
    path("report/frontend-urls/", frontend_urls_report, name="report_frontend_urls"),
]
