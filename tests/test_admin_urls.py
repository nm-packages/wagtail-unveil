from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import TestCase
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from wagtail_unveil.discovery.backend import (
    BackendURL,
    _AdminClassification,
    _classify_admin_route,
    _DiscoveredAdminRoute,
    _finalize_admin_route,
    _get_instance_for_model,
    _get_model_from_callback,
    _get_model_from_modeladmin_name,
    _get_namespace_specific_instance,
    _normalize_admin_route,
    _resolve_parameterized_url,
    _resolve_settings_url,
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
            "wagtail_unveil.discovery.backend._resolve_parameterized_url",
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
            "wagtail_unveil.discovery.backend._resolve_parameterized_url",
            return_value=mock.Mock(
                resolved=True,
                resolved_route="admin/inventory/product/reorder/1/",
            ),
        ):
            result = _finalize_admin_route(normalized, classification)

        self.assertFalse(result.is_testable)
        self.assertEqual(result.skip_reason, "POST-only view")
        self.assertEqual(result.resolved_route, "admin/inventory/product/reorder/1/")


class TestCallbackModelDiscovery(TestCase):
    def test_get_model_from_callback_supports_callback_cls_mro(self):
        class BaseView:
            model = Document

        class DetailView(BaseView):
            pass

        def callback(request):
            return None

        callback.cls = DetailView

        self.assertIs(_get_model_from_callback(callback), Document)


class TestParameterisedURLResolution(TestCase):
    """Test that parameterised admin URLs are resolved using real model instances."""

    def setUp(self):
        # Create instances for models that need them
        from wagtail.contrib.redirects.models import Redirect
        from wagtail.contrib.search_promotions.models import Query

        self.query = Query.objects.create(query_string="test search")
        self.redirect = Redirect.objects.create(
            old_path="/test-redirect",
            site=Site.objects.first(),
            redirect_link="/destination",
        )
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.document = Document.objects.create(
            title="Test document",
            file="test.pdf",
        )
        self.user = User.objects.create_user(username="testuser", password="password")
        self.group = Group.objects.create(name="Test group")

        from sandbox.inventory.models import Product, Supplier
        from sandbox.taxonomy.models import Banner, Category, Colour

        self.supplier = Supplier.objects.create(
            name="Test supplier",
            email="supplier@example.com",
            website="https://supplier.example.com",
        )
        self.product = Product.objects.create(
            name="Test product alpha",
            sku="TEST-ALPHA",
            description="First reorder candidate",
            price="9.99",
            sort_order=0,
            supplier=self.supplier,
        )
        self.second_product = Product.objects.create(
            name="Test product beta",
            sku="TEST-BETA",
            description="Second reorder candidate",
            price="19.99",
            sort_order=1,
            supplier=self.supplier,
        )
        self.category = Category.objects.create(name="Test category")
        self.colour = Colour.objects.create(name="Test colour")
        self.banner = Banner.objects.create(title="Test banner")

        self.urls = get_admin_urls()
        self.snippet_urls = [u for u in self.urls if u.namespace.startswith("wagtailsnippets_") and u.has_parameters]

    def _assert_namespace_name_testable(self, namespace_contains, name):
        urls = [u for u in self.urls if namespace_contains in u.namespace and u.name == name]
        self.assertGreater(len(urls), 0)
        for url in urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_snippet_action_urls_are_testable(self):
        for action in ("edit", "copy", "delete"):
            with self.subTest(action=action):
                urls = [u for u in self.snippet_urls if u.name == action]
                self.assertGreater(len(urls), 0)
                for url in urls:
                    self.assertTrue(url.is_testable, url.route)
                    self.assertTrue(url.resolved_route, url.route)

    def test_resolved_route_contains_pk(self):
        for url in self.snippet_urls:
            if url.resolved_route:
                self.assertNotIn("<", url.resolved_route)
                self.assertRegex(url.resolved_route, r"/\d+/")

    def test_redirect_urls_are_testable(self):
        self._assert_namespace_name_testable("redirect", "edit")
        self._assert_namespace_name_testable("redirect", "delete")

    def test_image_action_urls_are_testable(self):
        self._assert_namespace_name_testable("wagtailimages", "edit")
        self._assert_namespace_name_testable("wagtailimages", "delete")

    def test_image_url_generator_is_testable(self):
        url_gen_urls = [
            u
            for u in self.urls
            if "wagtailimages" in u.namespace and u.name in ("url_generator", "url_generator_output")
        ]
        self.assertGreater(len(url_gen_urls), 0)
        for url in url_gen_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_document_edit_url_is_testable(self):
        self._assert_namespace_name_testable("wagtaildocs", "edit")

    def test_user_edit_url_is_testable(self):
        self._assert_namespace_name_testable("wagtailusers_users", "edit")

    def test_admin_api_detail_urls_are_testable_with_resolved_route(self):
        expected_pks = {
            "wagtailadmin_api:pages": Site.objects.get(is_default_site=True).root_page.pk,
            "wagtailadmin_api:documents": self.document.pk,
            "wagtailadmin_api:images": self.image.pk,
        }

        for namespace, expected_pk in expected_pks.items():
            with self.subTest(namespace=namespace):
                urls = [u for u in self.urls if u.namespace == namespace and u.name == "detail"]
                self.assertEqual(len(urls), 1)
                self.assertTrue(urls[0].is_testable, urls[0].route)
                self.assertEqual(urls[0].skip_reason, "")
                self.assertTrue(urls[0].resolved_route, urls[0].route)
                self.assertIn(f"/{expected_pk}/", urls[0].resolved_route)

    def test_admin_api_action_urls_remain_untestable(self):
        action_urls = [u for u in self.urls if u.namespace == "wagtailadmin_api:pages" and u.name == "action"]
        self.assertEqual(len(action_urls), 1)
        self.assertFalse(action_urls[0].is_testable, action_urls[0].route)
        self.assertEqual(action_urls[0].skip_reason, "URL requires parameters")
        self.assertEqual(action_urls[0].resolved_route, "")

    def test_resolved_route_has_no_angle_brackets(self):
        resolved = [u for u in self.urls if u.resolved_route]
        self.assertGreater(len(resolved), 0)
        for url in resolved:
            self.assertNotIn("<", url.resolved_route, url.route)

    def test_multi_param_urls_remain_untestable(self):
        multi_param = [u for u in self.urls if u.has_parameters and u.route.count("<") > 1 and not u.resolved_route]
        for url in multi_param:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "URL requires parameters")

    def test_searchpick_edit_url_is_testable(self):
        self._assert_namespace_name_testable("searchpromotions", "edit")

    def test_inventory_reorder_urls_remain_visible_but_untestable(self):
        reorder_urls = [u for u in self.urls if u.name == "reorder" and "/reorder/" in u.route]

        self.assertGreater(len(reorder_urls), 0)
        for url in reorder_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "POST-only view")
            self.assertTrue(url.resolved_route, url.route)
            self.assertRegex(url.resolved_route, r"admin/.+/reorder/\d+/")

    def test_unresolvable_parameterised_urls_are_untestable(self):
        unresolvable = [u for u in self.urls if u.has_parameters and not u.resolved_route]
        self.assertGreater(len(unresolvable), 0)
        for url in unresolvable:
            self.assertFalse(url.is_testable, url.route)
            self.assertIn(url.skip_reason, ("URL requires parameters", "POST-only view"))

    @mock.patch("wagtail_unveil.discovery.backend._get_instance_for_model", return_value=None)
    def test_admin_api_detail_urls_stay_untestable_without_instances(self, get_instance):
        urls = get_admin_urls()
        detail_urls = [u for u in urls if u.namespace.startswith("wagtailadmin_api:") and u.name == "detail"]

        self.assertGreater(len(detail_urls), 0)
        for url in detail_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "URL requires parameters")
            self.assertEqual(url.resolved_route, "")

        self.assertGreaterEqual(get_instance.call_count, 3)


class TestParameterizedResolutionStrategies(TestCase):
    def test_settings_resolution_runs_first_and_stops(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend._resolve_settings_url",
            return_value=mock.Mock(resolved=False, attempts=["settings:no-model-instance"], detail="missing"),
        ) as resolve_settings:
            with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback") as get_model:
                result = _resolve_parameterized_url(
                    "wagtailsettings",
                    "edit",
                    callback=object(),
                    route="admin/settings/",
                )

        resolve_settings.assert_called_once_with("edit", "admin/settings/")
        get_model.assert_not_called()
        self.assertFalse(result.resolved)
        self.assertEqual(result.attempts, ["settings:no-model-instance"])

    def test_callback_model_strategy_wins_before_modeladmin_name(self):
        instance = mock.Mock(pk=42)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=User):
            with mock.patch("wagtail_unveil.discovery.backend._get_instance_for_model", return_value=instance):
                with mock.patch("wagtail_unveil.discovery.backend._get_model_from_modeladmin_name") as get_modeladmin:
                    with mock.patch("wagtail_unveil.discovery.backend.reverse", return_value="/admin/users/42/"):
                        result = _resolve_parameterized_url(
                            "",
                            "edit",
                            callback=object(),
                            route="admin/users/<int:pk>/",
                        )

        get_modeladmin.assert_not_called()
        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "callback-model")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:model-found",
                "callback-model:instance-found",
                "modeladmin-name:skipped",
                "reverse:resolved",
            ],
        )

    def test_modeladmin_name_fallback_resolves_when_callback_has_no_model(self):
        instance = mock.Mock(pk=7)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=None):
            with mock.patch("wagtail_unveil.discovery.backend._get_model_from_modeladmin_name", return_value=Group):
                with mock.patch("wagtail_unveil.discovery.backend._get_instance_for_model", return_value=instance):
                    with mock.patch("wagtail_unveil.discovery.backend.reverse", return_value="/admin/groups/7/"):
                        result = _resolve_parameterized_url(
                            "",
                            "taxonomy_person_modeladmin_edit",
                            callback=object(),
                            route="admin/taxonomy/person/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "modeladmin-name")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "modeladmin-name:model-found",
                "modeladmin-name:instance-found",
                "reverse:resolved",
            ],
        )

    def test_wagtailforms_namespace_fallback_resolves_without_model_metadata(self):
        instance = mock.Mock(pk=9)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=None):
            with mock.patch("wagtail_unveil.discovery.backend._get_model_from_modeladmin_name", return_value=None):
                with mock.patch("wagtail_unveil.discovery.backend._get_form_page_instance", return_value=instance):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend.reverse",
                        return_value="/admin/forms/submissions/9/",
                    ):
                        result = _resolve_parameterized_url(
                            "wagtailforms",
                            "list_submissions",
                            callback=object(),
                            route="admin/forms/submissions/<int:page_id>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "namespace:wagtailforms")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "modeladmin-name:no-model",
                "namespace:wagtailforms:instance-found",
                "reverse:resolved",
            ],
        )

    def test_workflow_namespace_overrides_callback_model_instance(self):
        callback_instance = mock.Mock(pk=1)
        workflow_instance = mock.Mock(pk=99)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend._get_instance_for_model",
                return_value=callback_instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend._get_workflow_instance",
                    return_value=workflow_instance,
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend.reverse",
                        return_value="/admin/workflows/usage/99/",
                    ) as reverse_mock:
                        result = _resolve_parameterized_url(
                            "wagtailadmin_workflows",
                            "usage",
                            callback=object(),
                            route="admin/workflows/usage/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "namespace:wagtailadmin_workflows")
        reverse_mock.assert_called_once_with("wagtailadmin_workflows:usage", args=[99])
        self.assertEqual(
            result.attempts,
            [
                "callback-model:model-found",
                "callback-model:instance-found",
                "modeladmin-name:skipped",
                "namespace:wagtailadmin_workflows:instance-found",
                "reverse:resolved",
            ],
        )

    def test_workflow_namespace_fails_closed_without_workflow_instance(self):
        callback_instance = mock.Mock(pk=1)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend._get_instance_for_model",
                return_value=callback_instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend._get_workflow_instance",
                    return_value=None,
                ):
                    with mock.patch("wagtail_unveil.discovery.backend.reverse") as reverse_mock:
                        result = _resolve_parameterized_url(
                            "wagtailadmin_workflows",
                            "usage",
                            callback=object(),
                            route="admin/workflows/usage/<int:pk>/",
                        )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "namespace:wagtailadmin_workflows")
        reverse_mock.assert_not_called()
        self.assertEqual(
            result.attempts,
            [
                "callback-model:model-found",
                "callback-model:instance-found",
                "modeladmin-name:skipped",
                "namespace:wagtailadmin_workflows:no-instance",
            ],
        )
        self.assertIn("did not provide a compatible instance", result.detail)

    def test_treebeard_models_skip_root_nodes(self):
        first_instance = mock.Mock()
        queryset = mock.Mock()
        queryset.exclude.return_value.first.return_value = first_instance
        objects = mock.Mock()
        objects.all.return_value = queryset
        model = mock.Mock(depth=mock.Mock(), objects=objects)

        instance = _get_instance_for_model(model)

        objects.all.assert_called_once_with()
        queryset.exclude.assert_called_once_with(depth=1)
        self.assertIs(instance, first_instance)

    def test_reverse_failure_records_detail_and_leaves_result_unresolved(self):
        instance = mock.Mock(pk=5)
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=User):
            with mock.patch("wagtail_unveil.discovery.backend._get_instance_for_model", return_value=instance):
                with mock.patch(
                    "wagtail_unveil.discovery.backend.reverse",
                    side_effect=RuntimeError("boom"),
                ):
                    result = _resolve_parameterized_url("", "edit", callback=object(), route="admin/users/<int:pk>/")

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "callback-model")
        self.assertIn("reverse:failed", result.attempts)
        self.assertIn("boom", result.detail)

    def test_attempts_record_full_fallback_order_when_unresolved(self):
        with mock.patch("wagtail_unveil.discovery.backend._get_model_from_callback", return_value=None):
            with mock.patch("wagtail_unveil.discovery.backend._get_model_from_modeladmin_name", return_value=None):
                with mock.patch("wagtail_unveil.discovery.backend._get_form_page_instance", return_value=None):
                    result = _resolve_parameterized_url(
                        "wagtailforms",
                        "list_submissions",
                        callback=object(),
                        route="admin/forms/submissions/<int:page_id>/",
                    )

        self.assertFalse(result.resolved)
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "modeladmin-name:no-model",
                "namespace:wagtailforms:no-instance",
            ],
        )
        self.assertIn("No model-backed instance", result.detail)

    def test_settings_resolution_result_explains_missing_instances(self):
        objects = mock.Mock()
        objects.first.return_value = None
        model = mock.Mock()
        model._meta.app_label = "core"
        model._meta.model_name = "socialmediasettings"
        model.objects = objects

        with mock.patch("wagtail_unveil.discovery.backend.reverse", side_effect=RuntimeError("should not reverse")):
            with mock.patch("wagtail.contrib.settings.registry.registry", [model]):
                result = _resolve_settings_url("edit", "admin/settings/core/socialmedia/<int:pk>/")

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "settings")
        self.assertEqual(result.attempts, ["settings:no-model-instance"])

    def test_settings_resolution_records_reverse_failures(self):
        from sandbox.core.models import SocialMediaSettings

        instance = mock.Mock(pk=3, site_id=11)
        with mock.patch.object(SocialMediaSettings.objects, "first", return_value=instance):
            with mock.patch("wagtail_unveil.discovery.backend.reverse", side_effect=RuntimeError("cannot reverse")):
                with mock.patch("wagtail.contrib.settings.registry.registry", [SocialMediaSettings]):
                    result = _resolve_settings_url("edit", "admin/settings/core/socialmedia/<int:pk>/")

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "settings")
        self.assertEqual(result.attempts, ["settings:reverse-failed"])
        self.assertIn("cannot reverse", result.detail)

    def test_settings_preview_resolution_skips_ineligible_models(self):
        class PreviewableMixin:
            pass

        class PlainSettings:
            _meta = type("Meta", (), {"app_label": "core", "model_name": "plainsettings"})()
            objects = mock.Mock()

        PlainSettings.objects.first.return_value = mock.Mock(pk=7, site_id=7)

        with mock.patch("wagtail.contrib.settings.registry.registry", [PlainSettings]):
            with mock.patch("wagtail.models.PreviewableMixin", PreviewableMixin, create=True):
                result = _resolve_settings_url(
                    "preview_on_edit",
                    "admin/settings/core/plainsettings/<int:pk>/",
                )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "settings")
        self.assertEqual(result.attempts, ["settings:reverse-failed"])
        self.assertEqual(
            result.detail,
            "Could not reverse wagtailsettings URL for any registered settings model",
        )

    def test_settings_preview_resolution_reports_missing_instances_for_eligible_models(self):
        class PreviewableMixin:
            pass

        class PreviewableSettings(PreviewableMixin):
            _meta = type("Meta", (), {"app_label": "core", "model_name": "previewablesettings"})()
            objects = mock.Mock()

        PreviewableSettings.objects.first.return_value = None

        with mock.patch("wagtail.contrib.settings.registry.registry", [PreviewableSettings]):
            with mock.patch("wagtail.models.PreviewableMixin", PreviewableMixin, create=True):
                result = _resolve_settings_url(
                    "preview_on_edit",
                    "admin/settings/core/previewablesettings/<int:pk>/",
                )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "settings")
        self.assertEqual(result.attempts, ["settings:no-model-instance"])
        self.assertEqual(result.detail, "No settings instances exist for the registered settings models")

    def test_namespace_specific_forms_rule_skips_when_instance_already_exists(self):
        instance = mock.Mock(pk=1)

        method, selected_instance, attempts = _get_namespace_specific_instance("wagtailforms", "edit", instance)

        self.assertEqual(method, "")
        self.assertIs(selected_instance, instance)
        self.assertEqual(attempts, ["namespace:wagtailforms:skipped"])

    def test_modeladmin_name_helpers_return_none_for_unknown_models(self):
        self.assertIsNone(_get_model_from_modeladmin_name("not_a_modeladmin_route"))


class TestModeladminURLDiscovery(TestCase):
    """Test that wagtail-modeladmin URLs are discovered and testable."""

    def setUp(self):
        from sandbox.taxonomy.models import Person

        Person.objects.create(name="Test Person", email="test@example.com")
        self.urls = get_admin_urls()
        self.modeladmin_urls = [u for u in self.urls if "modeladmin" in u.name]

    def test_modeladmin_urls_discovered(self):
        self.assertGreater(len(self.modeladmin_urls), 0)

    def test_index_is_testable(self):
        index = [u for u in self.modeladmin_urls if u.name.endswith("_index")]
        self.assertEqual(len(index), 1)
        self.assertTrue(index[0].is_testable)
        self.assertFalse(index[0].has_parameters)

    def test_create_is_testable(self):
        create = [u for u in self.modeladmin_urls if u.name.endswith("_create")]
        self.assertEqual(len(create), 1)
        self.assertTrue(create[0].is_testable)
        self.assertFalse(create[0].has_parameters)

    def _get_modeladmin_url(self, suffix):
        urls = [u for u in self.modeladmin_urls if u.name.endswith(suffix)]
        self.assertEqual(len(urls), 1)
        return urls[0]

    def test_parameterized_urls_are_testable_with_resolved_route(self):
        for suffix in ("_edit", "_delete", "_history"):
            with self.subTest(suffix=suffix):
                url = self._get_modeladmin_url(suffix)
                self.assertTrue(url.is_testable)
                self.assertTrue(url.resolved_route)

    def test_routes_have_no_regex_anchors(self):
        for url in self.modeladmin_urls:
            self.assertNotIn("^", url.route, url.route)
            self.assertNotIn("$", url.route, url.route)

    def test_empty_namespace(self):
        for url in self.modeladmin_urls:
            if url.name.startswith("taxonomy_person"):
                self.assertEqual(url.namespace, "")


class TestSettingsURLDiscovery(TestCase):
    """Test that Wagtail site and generic settings URLs are discovered and testable."""

    def setUp(self):
        from sandbox.core.models import BrandingSettings, SocialMediaSettings

        site = Site.objects.first()
        SocialMediaSettings.objects.get_or_create(
            site=site,
            defaults={
                "facebook": "https://facebook.com/test",
                "twitter": "https://twitter.com/test",
                "instagram": "https://instagram.com/test",
            },
        )
        if not BrandingSettings.objects.exists():
            BrandingSettings.objects.create(
                site_name="Test Site",
                tagline="Test tagline",
            )

        self.urls = get_admin_urls()
        self.settings_urls = [u for u in self.urls if u.namespace == "wagtailsettings"]

    def test_settings_urls_discovered(self):
        self.assertGreater(len(self.settings_urls), 0)

    def test_settings_urls_have_correct_namespace(self):
        for url in self.settings_urls:
            self.assertEqual(url.namespace, "wagtailsettings")

    def test_settings_edit_urls_present(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)

    def test_settings_urls_are_parameterised(self):
        for url in self.settings_urls:
            self.assertTrue(url.has_parameters, url.route)

    def test_settings_routes_contain_settings_prefix(self):
        for url in self.settings_urls:
            self.assertTrue(url.route.startswith("admin/settings/"), url.route)

    def test_settings_redirect_url_is_testable(self):
        redirect_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" not in u.route]
        self.assertGreater(len(redirect_urls), 0)
        for url in redirect_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_settings_edit_url_is_testable(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)
            self.assertNotIn("<", url.resolved_route)

    def test_settings_resolved_route_contains_app_and_model(self):
        for url in self.settings_urls:
            if url.resolved_route:
                self.assertIn("/core/", url.resolved_route)

    def test_settings_edit_url_uses_site_pk(self):
        """For BaseSiteSetting edit URL, resolved_route should contain site pk, not settings row pk."""
        from sandbox.core.models import SocialMediaSettings

        # Get the site_id from the settings instance
        settings_instance = SocialMediaSettings.objects.first()
        self.assertIsNotNone(settings_instance)
        expected_site_pk = settings_instance.site_id

        # Find the edit URL for SocialMediaSettings
        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route and u.resolved_route]
        self.assertGreater(len(edit_urls), 0)

        # Assert the resolved_route contains the site pk (from settings.site_id), not settings row pk
        for url in edit_urls:
            self.assertIn(f"/{expected_site_pk}/", url.resolved_route)

    def test_settings_preview_url_is_non_testable(self):
        """preview_on_edit URL should be non-testable since sandbox settings don't implement PreviewableMixin."""
        preview_urls = [u for u in self.settings_urls if u.name == "preview_on_edit"]

        # If preview_on_edit URLs are discovered, they should all be non-testable
        for url in preview_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertTrue(url.skip_reason)


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
