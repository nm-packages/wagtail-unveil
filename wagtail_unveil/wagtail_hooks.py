from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.ui.components import Component


class UnveilReportPanel(Component):
    order = 350

    def render_html(self, parent_context):
        request = parent_context.get("request")
        if not request or not request.user.is_superuser or not settings.DEBUG:
            return ""
        admin_url = reverse("wagtail_unveil_report:admin_urls")
        frontend_url = reverse("wagtail_unveil_report:frontend_urls")
        return format_html(
            '<section class="w-panel w-panel--dashboard"'
            ' aria-labelledby="unveil-panel-heading">'
            '<div class="w-panel__header">'
            '<h2 class="w-panel__heading" id="unveil-panel-heading">'
            "Wagtail Unveil</h2>"
            '<div class="w-panel__divider"></div>'
            "</div>"
            '<div class="w-panel__content">'
            '<div class="nice-padding">'
            '<a href="{}" target="_blank" rel="noopener noreferrer"'
            ' class="button button-small button-secondary">'
            "View Admin URLs Report</a> "
            '<a href="{}" target="_blank" rel="noopener noreferrer"'
            ' class="button button-small button-secondary">'
            "View Frontend URLs Report</a>"
            "</div></div></section>",
            admin_url,
            frontend_url,
        )


@hooks.register("construct_homepage_panels")
def add_unveil_panel(request, panels):
    panels.append(UnveilReportPanel())
