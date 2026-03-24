from datetime import date
from unittest.mock import patch
from urllib.parse import urlparse

from django.test import RequestFactory, TestCase
from wagtail.models import Page

from sandbox.events.models import EventIndexPage, EventPage
from wagtail_unveil.discovery.frontend import get_frontend_urls


class TestRoutableSubUrls(TestCase):
    def setUp(self):
        root = Page.objects.first()
        home = root.get_children().first()
        self.event_index = EventIndexPage(title="Events", slug="events")
        home.add_child(instance=self.event_index)
        self.event_index.save_revision().publish()
        self.event_page = EventPage(
            title="Spring Conference",
            slug="spring-conference",
            event_date=date(2025, 4, 15),
            location="Convention Centre",
            body="<p>Event details.</p>",
        )
        self.event_index.add_child(instance=self.event_page)
        self.event_page.save_revision().publish()
        self.urls = get_frontend_urls()
        self.page_type = "events.EventIndexPage"
        self.factory = RequestFactory()

    def _get_event_urls(self):
        return [u for u in self.urls if u.source == "page" and u.page_type == self.page_type]

    def _event_index_path(self):
        parsed = urlparse(self.event_index.url)
        return parsed.path or self.event_index.url

    def test_static_sub_route_discovered_and_testable(self):
        event_urls = self._get_event_urls()
        past_urls = [u for u in event_urls if u.url.endswith("/past/")]
        self.assertEqual(len(past_urls), 1)
        past = past_urls[0]
        self.assertTrue(past.is_testable)
        self.assertFalse(past.skip_reason)
        self.assertEqual(past.name, "past_events")

    def test_parameterized_sub_route_is_resolved_and_testable(self):
        event_urls = self._get_event_urls()
        year_urls = [u for u in event_urls if "year/" in u.url]
        self.assertEqual(len(year_urls), 1)
        year = year_urls[0]
        self.assertEqual(year.url, "/events/year/<int:year>/")
        self.assertTrue(year.is_testable)
        self.assertEqual(year.skip_reason, "")
        self.assertEqual(year.resolved_url, "/events/year/2025/")
        self.assertEqual(year.name, "events_for_year")

    def test_static_regex_family_sub_route_discovered_and_testable(self):
        event_urls = self._get_event_urls()
        tag_urls = [u for u in event_urls if u.url.endswith("/tags/")]
        self.assertEqual(len(tag_urls), 1)
        tag_index = tag_urls[0]
        self.assertTrue(tag_index.is_testable)
        self.assertEqual(tag_index.skip_reason, "")
        self.assertEqual(tag_index.name, "tag_archive")

    def test_regex_sub_route_discovered_and_not_testable(self):
        event_urls = self._get_event_urls()
        regex_urls = [u for u in event_urls if "([\\w-]+)" in u.url]
        self.assertEqual(len(regex_urls), 1)
        regex_url = regex_urls[0]
        self.assertEqual(regex_url.url, "/events/tags/([\\w-]+)/")
        self.assertEqual(regex_url.source, "page")
        self.assertFalse(regex_url.is_testable)
        self.assertEqual(regex_url.skip_reason, "URL contains regex patterns")
        self.assertEqual(regex_url.name, "tag_archive")

    def test_static_tag_route_invokes_render_with_default_title(self):
        request = self.factory.get("/events/tags/")
        response = object()

        with patch.object(self.event_index, "render", return_value=response) as render:
            result = self.event_index.tag_archive(request)

        self.assertIs(result, response)
        self.assertEqual(render.call_args.kwargs["context_overrides"]["filter_title"], "Tagged Events")
        self.assertEqual(render.call_args.kwargs["context_overrides"]["active_tag"], "")

    def test_concrete_regex_tag_route_invokes_render_with_tag_context(self):
        request = self.factory.get("/events/tags/sourdough/")
        response = object()

        with patch.object(self.event_index, "render", return_value=response) as render:
            result = self.event_index.tag_archive(request, "sourdough")

        self.assertIs(result, response)
        self.assertEqual(
            render.call_args.kwargs["context_overrides"]["filter_title"],
            "Events tagged sourdough",
        )
        self.assertEqual(render.call_args.kwargs["context_overrides"]["active_tag"], "sourdough")

    def test_index_route_not_duplicated(self):
        event_urls = self._get_event_urls()
        base_path = self._event_index_path()
        base_urls = [u for u in event_urls if u.url == base_path]
        self.assertEqual(len(base_urls), 1)

    def test_sub_route_urls_correctly_constructed(self):
        event_urls = self._get_event_urls()
        base_path = self._event_index_path().rstrip("/")
        for url in event_urls:
            self.assertTrue(
                url.url.startswith(base_path),
                f"{url.url} does not start with {base_path}",
            )

    def test_sub_route_fields(self):
        event_urls = self._get_event_urls()
        sub_routes = [u for u in event_urls if u.url != self._event_index_path()]
        self.assertGreater(len(sub_routes), 0)
        for url in sub_routes:
            self.assertEqual(url.source, "page")
            self.assertEqual(url.page_type, self.page_type)
            self.assertEqual(url.page_title, "Events")
            self.assertTrue(url.name)
