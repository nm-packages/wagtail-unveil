from unittest import mock

from django.test import TestCase

from wagtail_unveil.discovery.backend import (
    BackendURL,
    _AdminClassification,
    _classify_admin_route,
    _DiscoveredAdminRoute,
    _finalize_admin_route,
    _normalize_admin_route,
    get_admin_urls,
)
from wagtail_unveil.discovery.utils import clean_regex_route, route_contains_regex, route_has_parameters


class TestGetAdminUrls(TestCase):
    def setUp(self):
        self.urls = get_admin_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_all_urls_start_with_admin(self):
        for url in self.urls:
            self.assertTrue(url.route.startswith("admin/"), url.route)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, BackendURL)
        self.assertIsInstance(url.route, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.namespace, str)
        self.assertIsInstance(url.has_parameters, bool)
        self.assertIsInstance(url.view_name, str)
        self.assertIsInstance(url.page_type, str)

    def test_known_url_present(self):
        names = {url.name for url in self.urls}
        self.assertIn("wagtailadmin_home", names)

    def test_has_parameters_detection(self):
        parameterized = [url for url in self.urls if url.has_parameters]
        static = [url for url in self.urls if not url.has_parameters]
        self.assertGreater(len(parameterized), 0)
        self.assertGreater(len(static), 0)
        for url in static:
            self.assertNotIn("<", url.route)

    def test_is_testable_false_for_non_snippet_parameterized(self):
        for url in self.urls:
            if url.has_parameters and not url.resolved_route:
                self.assertFalse(url.is_testable, url.route)
                self.assertIn(url.skip_reason, ("URL requires parameters", "POST-only view"))

    def test_regex_routes_are_cleaned_and_testable(self):
        """Regex anchors are stripped so non-parameterised regex routes are testable."""
        modeladmin_index = [url for url in self.urls if url.name == "taxonomy_person_modeladmin_index"]
        self.assertEqual(len(modeladmin_index), 1)
        self.assertNotIn("^", modeladmin_index[0].route)
        self.assertTrue(modeladmin_index[0].is_testable, modeladmin_index[0].route)

    def test_is_testable_false_for_logout(self):
        logout = [url for url in self.urls if url.name == "wagtailadmin_logout"]
        self.assertEqual(len(logout), 1)
        self.assertFalse(logout[0].is_testable)
        self.assertEqual(logout[0].skip_reason, "POST-only view")

    def test_is_testable_false_for_error_test(self):
        error = [url for url in self.urls if url.name == "wagtailadmin_error_test"]
        self.assertEqual(len(error), 1)
        self.assertFalse(error[0].is_testable)
        self.assertEqual(error[0].skip_reason, "Intentional error endpoint")

    def test_is_testable_true_for_home(self):
        home = [url for url in self.urls if url.name == "wagtailadmin_home"]
        self.assertEqual(len(home), 1)
        self.assertTrue(home[0].is_testable)
        self.assertEqual(home[0].skip_reason, "")

    def test_page_instance_helpers_are_loaded_once_per_discovery_run(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend.get_page_instances_by_type",
            return_value=[],
        ) as get_page_instances_by_type:
            with mock.patch(
                "wagtail_unveil.discovery.backend.get_add_subpage_parent_page_instances_by_type",
                return_value=[],
            ) as get_add_subpage_parent_page_instances_by_type:
                get_admin_urls()

        get_page_instances_by_type.assert_called_once_with()
        get_add_subpage_parent_page_instances_by_type.assert_called_once_with()


class TestCleanRegexRoute(TestCase):
    """Test the clean_regex_route() helper."""

    def test_strips_caret(self):
        self.assertEqual(clean_regex_route("^foo/bar/"), "foo/bar/")

    def test_strips_dollar(self):
        self.assertEqual(clean_regex_route("foo/bar/$"), "foo/bar/")

    def test_strips_both_anchors(self):
        self.assertEqual(clean_regex_route("^foo/bar/$"), "foo/bar/")

    def test_converts_named_group(self):
        self.assertEqual(
            clean_regex_route("^edit/(?P<instance_pk>[-\\w]+)/$"),
            "edit/<instance_pk>/",
        )

    def test_passthrough_normal_route(self):
        self.assertEqual(clean_regex_route("admin/home/"), "admin/home/")

    def test_multiple_named_groups(self):
        self.assertEqual(
            clean_regex_route("^a/(?P<pk>[0-9]+)/b/(?P<slug>[-\\w]+)/$"),
            "a/<pk>/b/<slug>/",
        )

    def test_route_has_parameters(self):
        self.assertTrue(route_has_parameters("admin/images/<int:image_id>/"))
        self.assertFalse(route_has_parameters("admin/images/"))

    def test_route_contains_regex(self):
        self.assertTrue(route_contains_regex("documents/(.*)/"))
        self.assertTrue(route_contains_regex("year/[0-9]+/"))
        self.assertTrue(route_contains_regex(r"year/\d+/"))
        self.assertFalse(route_contains_regex("documents/<path:path>/"))


class TestAdminDiscoveryPhases(TestCase):
    def test_normalization_cleans_route_and_sets_metadata(self):
        def callback(request):
            return None

        discovered = _DiscoveredAdminRoute(
            raw_route="^admin/example/(?P<pk>[0-9]+)/$",
            name="example_edit",
            namespace="example",
            callback=callback,
        )

        normalized = _normalize_admin_route(discovered, skip_prefixes=[])

        self.assertIsNotNone(normalized)
        self.assertEqual(normalized.route, "admin/example/<pk>/")
        self.assertTrue(normalized.has_parameters)
        self.assertTrue(normalized.view_name.endswith(".callback"))

    def test_normalization_drops_routes_with_unsafe_regex(self):
        discovered = _DiscoveredAdminRoute(
            raw_route="admin/catch-all/.*/",
            name="unsafe",
            namespace="",
            callback=lambda request: None,
        )

        normalized = _normalize_admin_route(discovered, skip_prefixes=[])

        self.assertIsNone(normalized)

    def test_classification_marks_known_non_testable_name(self):
        normalized = _normalize_admin_route(
            _DiscoveredAdminRoute(
                raw_route="admin/logout/",
                name="wagtailadmin_logout",
                namespace="wagtailadmin",
                callback=lambda request: None,
            ),
            skip_prefixes=[],
        )

        classification = _classify_admin_route(
            normalized,
            docs_serve_available=True,
            images_serve_available=True,
        )

        self.assertFalse(classification.is_testable)
        self.assertEqual(classification.skip_reason, "POST-only view")
        self.assertFalse(classification.should_resolve)

    def test_classification_marks_missing_docs_dependency(self):
        normalized = _normalize_admin_route(
            _DiscoveredAdminRoute(
                raw_route="admin/documents/<int:document_id>/edit/",
                name="edit",
                namespace="wagtaildocs",
                callback=lambda request: None,
            ),
            skip_prefixes=[],
        )

        classification = _classify_admin_route(
            normalized,
            docs_serve_available=False,
            images_serve_available=True,
        )

        self.assertFalse(classification.is_testable)
        self.assertIn("wagtaildocs_urls", classification.skip_reason)
        self.assertFalse(classification.should_resolve)

    def test_parameterized_routes_require_resolution_before_skip_reason(self):
        normalized = _normalize_admin_route(
            _DiscoveredAdminRoute(
                raw_route="admin/images/<int:image_id>/edit/",
                name="edit",
                namespace="wagtailimages",
                callback=lambda request: None,
            ),
            skip_prefixes=[],
        )

        classification = _classify_admin_route(
            normalized,
            docs_serve_available=True,
            images_serve_available=True,
        )

        self.assertTrue(classification.is_testable)
        self.assertTrue(classification.should_resolve)
        self.assertEqual(classification.skip_reason, "")

    def test_finalization_assigns_parameter_skip_reason_after_failed_resolution(self):
        normalized = _normalize_admin_route(
            _DiscoveredAdminRoute(
                raw_route="admin/images/<int:image_id>/edit/",
                name="edit",
                namespace="wagtailimages",
                callback=lambda request: None,
            ),
            skip_prefixes=[],
        )
        classification = _AdminClassification(should_resolve=True)

        with mock.patch(
            "wagtail_unveil.discovery.backend.resolve_parameterized_url",
            return_value=mock.Mock(resolved=False, resolved_route=""),
        ):
            result = _finalize_admin_route(normalized, classification)

        self.assertFalse(result.is_testable)
        self.assertEqual(result.skip_reason, "URL requires parameters")
        self.assertEqual(result.resolved_route, "")

    def test_finalization_marks_resolved_post_only_route_untestable(self):
        class ReorderView:
            http_method_names = ["post", "options"]

            def post(self, request, *args, **kwargs):
                return None

        def callback(request):
            return None

        callback.view_class = ReorderView

        normalized = _normalize_admin_route(
            _DiscoveredAdminRoute(
                raw_route="admin/inventory/product/reorder/<int:pk>/",
                name="reorder",
                namespace="inventory_product",
                callback=callback,
            ),
            skip_prefixes=[],
        )
        classification = _AdminClassification(should_resolve=True)

        with mock.patch(
            "wagtail_unveil.discovery.backend.resolve_parameterized_url",
            return_value=mock.Mock(
                resolved=True,
                resolved_route="admin/inventory/product/reorder/1/",
            ),
        ):
            result = _finalize_admin_route(normalized, classification)

        self.assertFalse(result.is_testable)
        self.assertEqual(result.skip_reason, "POST-only view")
        self.assertEqual(result.resolved_route, "admin/inventory/product/reorder/1/")


class TestMissingServeUrls(TestCase):
    """Test that admin URLs are marked non-testable when required serve URLs are absent."""

    def _get_admin_urls_without(self, *missing_names):
        with mock.patch(
            "wagtail_unveil.discovery.backend._is_url_registered",
            side_effect=lambda name: name not in missing_names,
        ):
            return get_admin_urls()

    def test_doc_urls_non_testable_without_docs_serve(self):
        urls = self._get_admin_urls_without("wagtaildocs_serve")
        doc_urls = [u for u in urls if u.namespace in {"wagtaildocs", "wagtaildocs_chooser"}]
        self.assertGreater(len(doc_urls), 0)
        for url in doc_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertIn("wagtaildocs_urls", url.skip_reason)

    def test_image_url_generator_non_testable_without_images_serve(self):
        urls = self._get_admin_urls_without("wagtailimages_serve")
        gen_urls = [
            u for u in urls if u.namespace == "wagtailimages" and u.name in {"url_generator", "url_generator_output"}
        ]
        self.assertGreater(len(gen_urls), 0)
        for url in gen_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertIn("wagtailimages_urls", url.skip_reason)

    def test_other_image_urls_still_testable_without_images_serve(self):
        urls = self._get_admin_urls_without("wagtailimages_serve")
        image_urls = [
            u
            for u in urls
            if u.namespace == "wagtailimages" and u.name not in {"url_generator", "url_generator_output"}
        ]
        self.assertTrue(any(u.is_testable for u in image_urls))
