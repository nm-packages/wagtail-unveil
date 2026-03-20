from datetime import date
from types import SimpleNamespace
from unittest import mock
from unittest.mock import patch
from urllib.parse import urlparse

from django.test import RequestFactory, TestCase, override_settings
from wagtail.contrib.redirects.models import Redirect
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site

from sandbox.core.models import StandardPage
from sandbox.events.models import EventIndexPage, EventPage
from sandbox.forms.models import FormPage
from sandbox.home.models import HomePage
from wagtail_unveil.discovery.frontend import (
    FrontendURL,
    _build_frontend_url,
    _classify_frontend_candidate,
    _discover_routable_page_candidates,
    _format_cross_site_skip_reason,
    _FrontendCandidate,
    _get_descendant_date_years,
    _get_descendant_page_candidates,
    _get_routable_parameter_candidates,
    _get_wagtail_api_detail_resolved_url,
    _is_supported_wagtail_api_find_route,
    _iter_routable_parameters,
    _join_frontend_paths,
    _resolve_routable_page_url,
    _unique_values,
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
        self.assertIsInstance(url.resolved_url, str)
        self.assertIsInstance(url.query_params, dict)
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
    def test_parameterized_resolver_candidate_with_resolved_url_is_testable(self):
        candidate = _FrontendCandidate(
            url="/api/v2/pages/<int:pk>/",
            source="resolver",
            page_type="",
            page_title="",
            name="detail",
            has_parameters=True,
            resolved_url="/api/v2/pages/2/",
        )

        classification = _classify_frontend_candidate(candidate)
        result = _build_frontend_url(candidate, classification)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")
        self.assertEqual(result.resolved_url, "/api/v2/pages/2/")

    def test_query_driven_candidate_without_query_params_is_untestable(self):
        candidate = _FrontendCandidate(
            url="/api/v2/pages/find/",
            source="resolver",
            page_type="",
            page_title="",
            name="find",
            requires_query_params=True,
        )

        classification = _classify_frontend_candidate(candidate)

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "Requires query parameters")

    def test_regex_routable_candidate_records_contains_regex(self):
        pattern = SimpleNamespace(
            name="tag_archive",
            pattern=SimpleNamespace(_regex="^tags/([\\w-]+)/$"),
        )

        class RegexRoutablePage:
            title = "Events"

            @classmethod
            def get_subpage_urls(cls):
                return [pattern]

        result = _discover_routable_page_candidates(
            RegexRoutablePage(),
            "/events/",
            "events.EventIndexPage",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].url, "/events/tags/([\\w-]+)/")
        self.assertFalse(result[0].has_parameters)
        self.assertTrue(result[0].contains_regex)

    def test_parameterized_routable_candidate_with_resolved_url_is_testable(self):
        candidate = _FrontendCandidate(
            url="/events/year/<int:year>/",
            source="page",
            page_type="events.EventIndexPage",
            page_title="Events",
            name="events_for_year",
            has_parameters=True,
            resolved_url="/events/year/2025/",
        )

        classification = _classify_frontend_candidate(candidate)
        result = _build_frontend_url(candidate, classification)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")
        self.assertEqual(result.resolved_url, "/events/year/2025/")

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


class TestFrontendDiscoveryHelpers(TestCase):
    def test_supported_wagtail_api_find_route_detection_requires_find_view(self):
        callback = SimpleNamespace(name="find", cls=SimpleNamespace(), actions={"get": "listing_view"})

        self.assertFalse(_is_supported_wagtail_api_find_route("find", callback))

    def test_non_wagtail_detail_route_does_not_get_resolved_url(self):
        callback = SimpleNamespace(cls=SimpleNamespace(), actions={"get": "detail_view"})

        self.assertEqual(_get_wagtail_api_detail_resolved_url(callback, "/api/v2/pages/<int:pk>/"), "")

    def test_format_cross_site_skip_reason_with_standard_port_omits_port(self):
        candidate = _FrontendCandidate(
            url="/about/",
            source="page",
            page_type="core.StandardPage",
            page_title="About",
            name="",
            site_hostname="sub.localhost",
            site_port=80,
            is_cross_site=True,
        )

        self.assertEqual(
            _format_cross_site_skip_reason(candidate),
            "Belongs to non-default site host: sub.localhost",
        )

    def test_join_frontend_paths_normalizes_root_and_relative_subpath(self):
        self.assertEqual(_join_frontend_paths("/", "events/"), "/events/")
        self.assertEqual(_join_frontend_paths("/events/", "year/2025/"), "/events/year/2025/")

    def test_iter_routable_parameters_preserves_order_and_defaults_str_converter(self):
        self.assertEqual(
            list(_iter_routable_parameters("tags/<slug:slug>/<value>/")),
            [("slug", "slug"), ("value", "str")],
        )

    def test_unique_values_drops_blanks_and_duplicates(self):
        self.assertEqual(_unique_values([None, "", "alpha", "alpha", "beta"]), ["alpha", "beta"])

    def test_get_descendant_date_years_returns_empty_when_descendants_fail(self):
        page = mock.Mock()
        page.get_descendants.side_effect = RuntimeError("boom")

        self.assertEqual(_get_descendant_date_years(page), [])

    def test_get_descendant_page_candidates_skips_callables_and_duplicates(self):
        page = mock.Mock()
        page.get_descendants.return_value.live.return_value.specific.return_value = [
            SimpleNamespace(slug="alpha"),
            SimpleNamespace(slug=lambda: "ignored"),
            SimpleNamespace(slug="alpha"),
            SimpleNamespace(slug="beta"),
        ]

        self.assertEqual(_get_descendant_page_candidates(page, "slug"), ["alpha", "beta"])

    @mock.patch("wagtail_unveil.discovery.frontend._get_descendant_date_years", return_value=[2025])
    def test_get_routable_parameter_candidates_prefers_year_values(self, get_years):
        page = SimpleNamespace(year=None)

        self.assertEqual(_get_routable_parameter_candidates(page, "year", "int"), [2025])
        get_years.assert_called_once_with(page)

    @mock.patch("wagtail_unveil.discovery.frontend._get_descendant_page_candidates", return_value=["alpha"])
    def test_get_routable_parameter_candidates_supports_slug_and_uuid(self, get_candidates):
        page = SimpleNamespace(slug=None, uuid=None)

        self.assertEqual(_get_routable_parameter_candidates(page, "slug", "slug"), ["alpha"])
        self.assertEqual(_get_routable_parameter_candidates(page, "uuid", "uuid"), ["alpha"])
        self.assertEqual(get_candidates.call_count, 2)

    def test_get_routable_parameter_candidates_does_not_use_index_page_slug(self):
        page = SimpleNamespace(slug="events")
        page.get_descendants = mock.Mock()
        page.get_descendants.return_value.live.return_value.specific.return_value = []

        self.assertEqual(_get_routable_parameter_candidates(page, "slug", "slug"), [])

    def test_resolve_routable_page_url_returns_empty_when_reverse_fails(self):
        page = mock.Mock(year=2025)
        page.get_descendants.return_value.live.return_value.specific.return_value = []
        page.reverse_subpage.side_effect = RuntimeError("boom")
        pattern = SimpleNamespace(
            name="events_for_year",
            pattern=SimpleNamespace(_route="year/<int:year>/"),
        )

        self.assertEqual(
            _resolve_routable_page_url(page, pattern, "/events/", "year/<int:year>/"),
            "",
        )

    def test_resolve_routable_page_url_returns_empty_when_reversed_path_is_still_parameterized(self):
        page = mock.Mock(year=2025)
        page.get_descendants.return_value.live.return_value.specific.return_value = []
        page.reverse_subpage.return_value = "year/<int:year>/"
        pattern = SimpleNamespace(
            name="events_for_year",
            pattern=SimpleNamespace(_route="year/<int:year>/"),
        )

        self.assertEqual(
            _resolve_routable_page_url(page, pattern, "/events/", "year/<int:year>/"),
            "",
        )

    def test_resolve_routable_page_url_returns_empty_for_multi_parameter_routes(self):
        page = mock.Mock(year=2025, slug="events")
        pattern = SimpleNamespace(
            name="event_detail",
            pattern=SimpleNamespace(_route="year/<int:year>/<slug:slug>/"),
        )

        self.assertEqual(
            _resolve_routable_page_url(page, pattern, "/events/", "year/<int:year>/<slug:slug>/"),
            "",
        )
        page.reverse_subpage.assert_not_called()

    def test_discover_routable_page_candidates_ignores_unknown_pattern_objects(self):
        pattern = SimpleNamespace(name="broken", pattern=SimpleNamespace())

        class UnknownPatternPage:
            title = "Events"

            @classmethod
            def get_subpage_urls(cls):
                return [pattern]

        self.assertEqual(
            _discover_routable_page_candidates(
                UnknownPatternPage(),
                "/events/",
                "events.EventIndexPage",
            ),
            [],
        )


class TestWagtailAPIFrontendUrls(TestCase):
    def setUp(self):
        self.default_site = Site.objects.get(is_default_site=True)
        self.redirect = Redirect.objects.create(
            old_path="/test-redirect/",
            site=self.default_site,
            redirect_link="/",
        )
        self.image = Image.objects.create(
            title="Frontend test image",
            file=get_test_image_file(),
        )
        self.document = Document.objects.create(
            title="Frontend test document",
            file="frontend-test.pdf",
        )
        self.urls = get_frontend_urls()

    def _get_match(self, path, name):
        matches = [url for url in self.urls if url.url == path and url.name == name]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_pages_detail_route_uses_default_site_root_page_id(self):
        match = self._get_match("/api/v2/pages/<int:pk>/", "detail")

        self.assertTrue(match.is_testable)
        self.assertEqual(match.skip_reason, "")
        self.assertEqual(match.resolved_url, f"/api/v2/pages/{self.default_site.root_page_id}/")
        self.assertEqual(match.query_params, {})

    def test_images_detail_route_uses_image_id(self):
        match = self._get_match("/api/v2/images/<int:pk>/", "detail")

        self.assertTrue(match.is_testable)
        self.assertEqual(match.resolved_url, f"/api/v2/images/{self.image.pk}/")
        self.assertEqual(match.query_params, {})

    def test_documents_detail_route_uses_document_id(self):
        match = self._get_match("/api/v2/documents/<int:pk>/", "detail")

        self.assertTrue(match.is_testable)
        self.assertEqual(match.resolved_url, f"/api/v2/documents/{self.document.pk}/")
        self.assertEqual(match.query_params, {})

    def test_redirects_detail_route_uses_redirect_id(self):
        match = self._get_match("/api/v2/redirects/<int:pk>/", "detail")

        self.assertTrue(match.is_testable)
        self.assertEqual(match.resolved_url, f"/api/v2/redirects/{self.redirect.pk}/")
        self.assertEqual(match.query_params, {})

    def test_wagtail_api_find_routes_stay_visible_but_untestable(self):
        expected_paths = {
            "/api/v2/pages/find/",
            "/api/v2/images/find/",
            "/api/v2/documents/find/",
            "/api/v2/redirects/find/",
        }

        matches = [url for url in self.urls if url.name == "find" and url.url in expected_paths]

        self.assertEqual({url.url for url in matches}, expected_paths)
        for match in matches:
            self.assertFalse(match.is_testable)
            self.assertEqual(match.skip_reason, "Requires query parameters")
            self.assertEqual(match.query_params, {})

    def test_pages_detail_endpoint_is_request_testable(self):
        match = self._get_match("/api/v2/pages/<int:pk>/", "detail")

        response = self.client.get(match.resolved_url)

        self.assertEqual(response.status_code, 200)

    def test_bare_pages_find_endpoint_returns_404(self):
        response = self.client.get("/api/v2/pages/find/")

        self.assertEqual(response.status_code, 404)


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
