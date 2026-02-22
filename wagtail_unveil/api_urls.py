from django.urls import path

from wagtail_unveil.views import admin_urls_json, frontend_urls_json

app_name = "wagtail_unveil_api"

urlpatterns = [
    path("admin-urls/", admin_urls_json, name="admin_urls"),
    path("frontend-urls/", frontend_urls_json, name="frontend_urls"),
]
