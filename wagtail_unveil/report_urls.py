from django.urls import path

from wagtail_unveil.views import admin_urls_report, frontend_urls_report

app_name = "wagtail_unveil_report"

urlpatterns = [
    path("admin-urls/", admin_urls_report, name="admin_urls"),
    path("frontend-urls/", frontend_urls_report, name="frontend_urls"),
]
