from types import SimpleNamespace
from unittest import mock

from django.test import TestCase
from wagtail.contrib.redirects.models import Redirect
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from wagtail_unveil.discovery.frontend import (
    _discover_routable_page_candidates,
    _format_cross_site_skip_reason,
    _FrontendCandidate,
    get_frontend_urls,
)
from wagtail_unveil.discovery.frontend_resolution import (
    _get_descendant_date_years,
    _get_descendant_page_candidates,
    _get_routable_parameter_candidates,
    _get_wagtail_api_detail_resolved_url,
    _is_supported_wagtail_api_find_route,
    _iter_routable_parameters,
    _join_frontend_paths,
    _resolve_routable_page_url,
    _unique_values,
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

    @mock.patch("wagtail_unveil.discovery.frontend_resolution._get_descendant_date_years", return_value=[2025])
    def test_get_routable_parameter_candidates_prefers_year_values(self, get_years):
        page = SimpleNamespace(year=None)

        self.assertEqual(_get_routable_parameter_candidates(page, "year", "int"), [2025])
        get_years.assert_called_once_with(page)

    @mock.patch("wagtail_unveil.discovery.frontend_resolution._get_descendant_page_candidates", return_value=["alpha"])
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
