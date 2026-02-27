from django.urls import path

from wagtail_unveil.views import admin_urls_json, admin_urls_report, frontend_urls_json, frontend_urls_report

app_name = "wagtail_unveil"

urlpatterns = [
    path("api/admin-urls/", admin_urls_json, name="api_admin_urls"),
    path("api/frontend-urls/", frontend_urls_json, name="api_frontend_urls"),
    path("report/admin-urls/", admin_urls_report, name="report_admin_urls"),
    path("report/frontend-urls/", frontend_urls_report, name="report_frontend_urls"),
]
