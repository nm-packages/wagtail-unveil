from unittest.mock import patch
from urllib.parse import urlparse

from django.test import TestCase, override_settings
from wagtail.models import Page, Site

from sandbox.core.models import StandardPage
from sandbox.events.models import EventIndexPage
from sandbox.forms.models import FormPage
from sandbox.home.models import HomePage
from wagtail_unveil.discovery.frontend import (
    FrontendURL,
    _build_frontend_url,
    _classify_frontend_candidate,
    _discover_routable_page_candidates,
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
        base_path = self._event_index_path()
        # Only one entry should match the base page URL (no duplicate from @path(""))
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

    def test_cross_site_candidate_without_hostname_uses_generic_reason(self):
        candidate = _FrontendCandidate(
            url="/about/",
            source="page",
            page_type="core.StandardPage",
            page_title="About",
            name="",
            is_cross_site=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "Belongs to non-default site host")

    def test_cross_site_candidate_with_non_standard_port_includes_port(self):
        candidate = _FrontendCandidate(
            url="/about/",
            source="page",
            page_type="core.StandardPage",
            page_title="About",
            name="",
            site_hostname="sub.localhost",
            site_port=8080,
            is_cross_site=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(
            classification.skip_reason,
            "Belongs to non-default site host: sub.localhost:8080",
        )


class TestMultisiteFrontendUrls(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()

        self.sub_home = HomePage(title="Subsite Home", slug="subsite-home")
        root.add_child(instance=self.sub_home)
        self.sub_home.save_revision().publish()

        self.sub_page = StandardPage(
            title="Subsite About",
            slug="subsite-about",
            body="<p>Subsite page body.</p>",
        )
        self.sub_home.add_child(instance=self.sub_page)
        self.sub_page.save_revision().publish()

        self.sub_site = Site.objects.create(
            hostname="sub.localhost",
            port=8000,
            site_name="Subsite",
            root_page=self.sub_home,
            is_default_site=False,
        )

        self.urls = get_frontend_urls()

    def test_non_default_site_page_is_discovered(self):
        matches = [u for u in self.urls if u.source == "page" and u.page_title == "Subsite About"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].url, "/subsite-about/")

    def test_non_default_site_page_is_marked_untestable(self):
        matches = [u for u in self.urls if u.source == "page" and u.page_title == "Subsite About"]
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertFalse(match.is_testable)
        self.assertEqual(match.skip_reason, "Belongs to non-default site host: sub.localhost:8000")

    def test_default_site_page_entries_remain_testable(self):
        default_site_pages = [
            u
            for u in self.urls
            if u.source == "page" and u.page_title != "Subsite About" and not u.name and not u.skip_reason
        ]
        self.assertGreater(len(default_site_pages), 0)
