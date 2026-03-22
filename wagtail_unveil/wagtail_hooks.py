from django.conf import settings
from wagtail import hooks
from wagtail.admin.ui.components import Component

from wagtail_unveil.discovery import backend_resolution
from wagtail_unveil.discovery.extensions import AdminInstanceResolver


class UnveilReportPanel(Component):
    order = 1000
    template_name = "wagtail_unveil/dashboard_panel.html"

    def render_html(self, parent_context):
        request = parent_context.get("request")
        if not request or not request.user.is_superuser or not settings.DEBUG:
            return ""
        return super().render_html(parent_context)


@hooks.register("construct_homepage_panels")
def add_unveil_panel(request, panels):
    panels.append(UnveilReportPanel())


@hooks.register("register_unveil_admin_instance_resolvers")
def register_unveil_admin_instance_resolvers():
    """Register built-in admin parameter resolvers through the public hook API."""
    return (
        AdminInstanceResolver(
            label="namespace:wagtailforms",
            predicate=lambda context: context.namespace == "wagtailforms",
            resolver=lambda context: backend_resolution._get_form_page_instance(),
        ),
        AdminInstanceResolver(
            label="namespace:wagtailadmin_workflows",
            predicate=lambda context: (
                context.namespace == "wagtailadmin_workflows"
                and context.name in backend_resolution.WORKFLOW_USAGE_NAMES
            ),
            resolver=lambda context: backend_resolution._get_workflow_instance(),
            override=True,
        ),
    )
