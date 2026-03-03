from django.test import TestCase
from wagtail.models import Page

from sandbox.events.models import EventIndexPage
from wagtail_unveil.discovery.frontend import (
    FrontendURL,
    _build_frontend_url,
    _classify_frontend_candidate,
    _FrontendCandidate,
    get_frontend_urls,
)


class TestGetFrontendUrls(TestCase):
    def setUp(self):
        self.urls = get_frontend_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, FrontendURL)
        self.assertIsInstance(url.url, str)
        self.assertIsInstance(url.source, str)
        self.assertIsInstance(url.page_type, str)
        self.assertIsInstance(url.page_title, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.is_testable, bool)

    def test_sources_are_valid(self):
        for url in self.urls:
            self.assertIn(url.source, ("page", "resolver"))

    def test_page_urls_have_page_type(self):
        page_urls = [u for u in self.urls if u.source == "page"]
        self.assertGreater(len(page_urls), 0)
        for url in page_urls:
            self.assertTrue(url.page_type, url.url)
            self.assertTrue(url.page_title, url.url)

    def test_resolver_urls_present(self):
        resolver_urls = [u for u in self.urls if u.source == "resolver"]
        self.assertGreater(len(resolver_urls), 0)

    def test_no_admin_urls_included(self):
        for url in self.urls:
            self.assertFalse(url.url.startswith("/admin/"), url.url)

    def test_no_unveil_urls_included(self):
        for url in self.urls:
            self.assertNotIn("unveil-api", url.url)
            self.assertNotIn("unveil-report", url.url)

    def test_page_urls_are_testable(self):
        page_urls = [u for u in self.urls if u.source == "page"]
        testable = [u for u in page_urls if not u.skip_reason]
        for url in testable:
            self.assertTrue(url.is_testable, url.url)

    def test_parameterized_resolver_urls_not_testable(self):
        for url in self.urls:
            if url.source == "resolver" and not url.is_testable:
                self.assertTrue(url.skip_reason, url.url)

    def test_regex_parameterized_resolver_urls_not_testable(self):
        regex_urls = {
            "wagtail_serve": "URL contains regex patterns",
            "wagtaildocs_serve": "URL contains regex patterns",
        }
        for name, expected_reason in regex_urls.items():
            matches = [u for u in self.urls if u.name == name]
            self.assertTrue(matches, f"Expected to find URL named {name}")
            for url in matches:
                self.assertFalse(url.is_testable, f"{name} should not be testable")
                self.assertEqual(url.skip_reason, expected_reason, name)

    def test_urls_start_with_slash(self):
        for url in self.urls:
            self.assertTrue(url.url.startswith("/"), url.url)


class TestRoutableSubUrls(TestCase):
    def setUp(self):
        root = Page.objects.first()
        home = root.get_children().first()
        self.event_index = EventIndexPage(title="Events", slug="events")
        home.add_child(instance=self.event_index)
        self.event_index.save_revision().publish()
        self.urls = get_frontend_urls()
        self.page_type = "events.EventIndexPage"

    def _get_event_urls(self):
        return [u for u in self.urls if u.source == "page" and u.page_type == self.page_type]

    def test_static_sub_route_discovered_and_testable(self):
        event_urls = self._get_event_urls()
        past_urls = [u for u in event_urls if u.url.endswith("/past/")]
        self.assertEqual(len(past_urls), 1)
        past = past_urls[0]
        self.assertTrue(past.is_testable)
        self.assertFalse(past.skip_reason)
        self.assertEqual(past.name, "past_events")

    def test_parameterized_sub_route_discovered_and_not_testable(self):
        event_urls = self._get_event_urls()
        year_urls = [u for u in event_urls if "year/" in u.url]
        self.assertEqual(len(year_urls), 1)
        year = year_urls[0]
        self.assertFalse(year.is_testable)
        self.assertEqual(year.skip_reason, "URL requires parameters")
        self.assertEqual(year.name, "events_for_year")

    def test_index_route_not_duplicated(self):
        event_urls = self._get_event_urls()
        base_path = self.event_index.url
        # Only one entry should match the base page URL (no duplicate from @path(""))
        base_urls = [u for u in event_urls if u.url == base_path]
        self.assertEqual(len(base_urls), 1)

    def test_sub_route_urls_correctly_constructed(self):
        event_urls = self._get_event_urls()
        base_path = self.event_index.url.rstrip("/")
        for url in event_urls:
            self.assertTrue(
                url.url.startswith(base_path),
                f"{url.url} does not start with {base_path}",
            )

    def test_sub_route_fields(self):
        event_urls = self._get_event_urls()
        sub_routes = [u for u in event_urls if u.url != self.event_index.url]
        self.assertGreater(len(sub_routes), 0)
        for url in sub_routes:
            self.assertEqual(url.source, "page")
            self.assertEqual(url.page_type, self.page_type)
            self.assertEqual(url.page_title, "Events")
            self.assertTrue(url.name)


class TestFrontendDiscoveryPhases(TestCase):
    def test_plain_page_candidate_is_testable(self):
        candidate = _FrontendCandidate(
            url="/about/",
            source="page",
            page_type="core.StandardPage",
            page_title="About",
            name="",
        )

        classification = _classify_frontend_candidate(candidate)
        result = _build_frontend_url(candidate, classification)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")

    def test_form_landing_candidate_requires_post(self):
        candidate = _FrontendCandidate(
            url="/contact/",
            source="page",
            page_type="forms.FormPage",
            page_title="Contact",
            name="landing_page",
            requires_post=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "Requires POST submission")

    def test_parameterized_routable_candidate_requires_parameters(self):
        candidate = _FrontendCandidate(
            url="/events/year/<int:year>/",
            source="page",
            page_type="events.EventIndexPage",
            page_title="Events",
            name="events_for_year",
            has_parameters=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "URL requires parameters")

    def test_regex_resolver_candidate_is_marked_untestable(self):
        candidate = _FrontendCandidate(
            url="/documents/(.*)/",
            source="resolver",
            page_type="",
            page_title="",
            name="wagtaildocs_serve",
            contains_regex=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "URL contains regex patterns")
