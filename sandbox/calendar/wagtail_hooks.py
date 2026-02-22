from wagtail import hooks

from sandbox.calendar.viewsets import CalendarViewSet


@hooks.register("register_admin_viewset")
def register_calendar_viewset():
    return CalendarViewSet()
