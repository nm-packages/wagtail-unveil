from unittest.mock import patch

from django.test import TestCase, override_settings
from wagtail.models import Page

from sandbox.events.models import EventIndexPage
from sandbox.forms.models import FormPage
from wagtail_unveil.discovery.frontend import _discover_routable_page_candidates, get_frontend_urls


class TestFrontendPageLimitPerformance(TestCase):
    def setUp(self):
        root = Page.objects.first()
        self.home = root.get_children().first()

    def _publish(self, page):
        self.home.add_child(instance=page)
        page.save_revision().publish()
        return page

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_limit_one_skips_extra_pages_before_routable_expansion(self):
        self._publish(EventIndexPage(title="Events A", slug="events-a"))
        self._publish(EventIndexPage(title="Events B", slug="events-b"))

        with patch(
            "wagtail_unveil.discovery.frontend._discover_routable_page_candidates",
            wraps=_discover_routable_page_candidates,
        ) as discover_routable:
            urls = get_frontend_urls()

        event_urls = [u for u in urls if u.page_type == "events.EventIndexPage" and u.source == "page"]
        self.assertEqual(discover_routable.call_count, 1)
        self.assertEqual(len({u.page_title for u in event_urls}), 1)

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=0)
    def test_zero_limit_processes_all_pages(self):
        self._publish(EventIndexPage(title="Events A", slug="events-a"))
        self._publish(EventIndexPage(title="Events B", slug="events-b"))

        with patch(
            "wagtail_unveil.discovery.frontend._discover_routable_page_candidates",
            wraps=_discover_routable_page_candidates,
        ) as discover_routable:
            urls = get_frontend_urls()

        event_urls = [u for u in urls if u.page_type == "events.EventIndexPage" and u.source == "page"]
        self.assertEqual(discover_routable.call_count, 2)
        self.assertEqual({u.page_title for u in event_urls}, {"Events A", "Events B"})

    @override_settings(WAGTAIL_UNVEIL_PAGES_PER_TYPE=1)
    def test_selected_pages_keep_form_and_routable_candidates(self):
        self._publish(
            FormPage(
                title="Contact A",
                slug="contact-a",
                from_address="noreply@example.com",
                to_address="team@example.com",
                subject="Contact form",
            )
        )
        self._publish(EventIndexPage(title="Events A", slug="events-a"))

        urls = get_frontend_urls()

        form_urls = [u for u in urls if u.page_type == "forms.FormPage" and u.page_title == "Contact A"]
        event_urls = [u for u in urls if u.page_type == "events.EventIndexPage" and u.page_title == "Events A"]

        self.assertEqual({u.name for u in form_urls}, {"", "landing_page"})
        self.assertIn("past_events", {u.name for u in event_urls})
        self.assertIn("events_for_year", {u.name for u in event_urls})
