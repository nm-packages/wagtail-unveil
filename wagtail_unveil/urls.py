from django.urls import path

from wagtail_unveil.api_contract import get_api_contract, get_supported_api_versions
from wagtail_unveil.views import (
    backend_urls_report,
    build_admin_urls_json_view,
    build_frontend_urls_json_view,
    frontend_urls_report,
    settings_report,
)

app_name = "wagtail_unveil"

urlpatterns = []

for api_version in get_supported_api_versions():
    contract = get_api_contract(api_version)
    urlpatterns.append(
        path(
            contract.backend_url_path,
            build_admin_urls_json_view(api_version),
            name=contract.backend_url_name,
        ),
    )
    urlpatterns.append(
        path(
            contract.frontend_url_path,
            build_frontend_urls_json_view(api_version),
            name=contract.frontend_url_name,
        ),
    )

urlpatterns.extend(
    [
        path("report/backend-urls/", backend_urls_report, name="report_backend_urls"),
        path("report/frontend-urls/", frontend_urls_report, name="report_frontend_urls"),
        path("report/settings/", settings_report, name="report_settings"),
    ],
)
