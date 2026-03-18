from datetime import date

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path, route
from wagtail.fields import RichTextField
from wagtail.models import Page


class EventPage(Page):
    """A single event with a date, location, and description."""

    event_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("event_date"),
        FieldPanel("location"),
        FieldPanel("body"),
    ]

    parent_page_types = ["events.EventIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Event Page"
        verbose_name_plural = "Event Pages"


class EventIndexPage(RoutablePageMixin, Page):
    """A routable page that lists events with sub-URL filtering."""

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.EventPage"]

    def _get_events(self):
        return EventPage.objects.live().descendant_of(self).order_by("-event_date")

    def _get_nav_context(self):
        """Return shared navigation context for all sub-routes."""
        years = self._get_events().values_list("event_date__year", flat=True).distinct().order_by("-event_date__year")
        return {
            "past_url": self.url + self.reverse_subpage("past_events"),
            "all_url": self.url.rstrip("/") + "/",
            "years": [(year, self.url + self.reverse_subpage("events_for_year", args=[year])) for year in years],
            "tags_url": self.url + self.reverse_subpage("tag_archive"),
            "sample_tag_url": self.url + self.reverse_subpage("tag_archive", args=["sourdough"]),
        }

    @path("")
    def index(self, request):
        """Default view — lists all events."""
        return self.render(
            request,
            context_overrides={"events": self._get_events(), **self._get_nav_context()},
        )

    @path("past/")
    def past_events(self, request):
        """Static sub-route listing past events."""
        events = self._get_events().filter(event_date__lt=date.today())
        return self.render(
            request,
            context_overrides={
                "events": events,
                "filter_title": "Past Events",
                **self._get_nav_context(),
            },
        )

    @path("year/<int:year>/")
    def events_for_year(self, request, year):
        """Parameterized sub-route for events in a specific year."""
        events = self._get_events().filter(event_date__year=year)
        return self.render(
            request,
            context_overrides={
                "events": events,
                "filter_title": f"Events in {year}",
                **self._get_nav_context(),
            },
        )

    @route(r"^tags/$", name="tag_archive")
    @route(r"^tags/([\w-]+)/$", name="tag_archive")
    def tag_archive(self, request, tag=None):
        """Regex routes used to exercise routable discovery edge cases."""
        events = self._get_events()
        filter_title = "Tagged Events"
        if tag:
            filter_title = f"Events tagged {tag}"

        return self.render(
            request,
            context_overrides={
                "events": events,
                "filter_title": filter_title,
                "active_tag": tag or "",
                **self._get_nav_context(),
            },
        )

    class Meta:
        verbose_name = "Event Index Page"
        verbose_name_plural = "Event Index Pages"
