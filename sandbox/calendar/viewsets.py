from django.urls import path
from wagtail.admin.viewsets.base import ViewSet

from sandbox.calendar import views


class CalendarViewSet(ViewSet):
    name = "calendar"
    url_prefix = "calendar"
    url_namespace = "calendar"
    icon = "date"
    add_to_admin_menu = True
    menu_label = "Calendar"

    def get_urlpatterns(self):
        return [
            path("", views.index, name="index"),
            path("month/", views.month, name="month"),
        ]
