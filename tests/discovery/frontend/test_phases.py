from types import SimpleNamespace
from unittest import mock

from django.test import TestCase

from wagtail_unveil.discovery.frontend import (
    _classify_frontend_candidate,
    _discover_routable_page_candidates,
    _FrontendCandidate,
    get_frontend_urls,
)


class TestFrontendDiscoveryPhases(TestCase):
    def _get_frontend_result(self, candidate):
        with (
            mock.patch(
                "wagtail_unveil.discovery.frontend._discover_page_candidates",
                return_value=[candidate],
            ),
            mock.patch(
                "wagtail_unveil.discovery.frontend._discover_resolver_candidates",
                return_value=[],
            ),
        ):
            results = get_frontend_urls()

        self.assertEqual(len(results), 1)
        return results[0]

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
        result = self._get_frontend_result(candidate)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")
        self.assertEqual(result.resolved_url, "/api/v2/pages/2/")
        self.assertTrue(classification.is_testable)

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
        result = self._get_frontend_result(candidate)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")
        self.assertEqual(result.resolved_url, "/events/year/2025/")
        self.assertTrue(classification.is_testable)

    def test_plain_page_candidate_is_testable(self):
        candidate = _FrontendCandidate(
            url="/about/",
            source="page",
            page_type="core.StandardPage",
            page_title="About",
            name="",
        )

        classification = _classify_frontend_candidate(candidate)
        result = self._get_frontend_result(candidate)

        self.assertTrue(result.is_testable)
        self.assertEqual(result.skip_reason, "")
        self.assertTrue(classification.is_testable)

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
