from django.conf import settings
from wagtail import hooks
from wagtail.admin.ui.components import Component


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
