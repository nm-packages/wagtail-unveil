from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import get_resolver
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.backend_resolution import (
    _apply_admin_instance_resolvers,
    _get_instance_for_model,
    _get_model_from_callback,
    _resolve_parameterized_url,
    _resolve_settings_url,
)
from wagtail_unveil.discovery.extensions import AdminInstanceResolver
from wagtail_unveil.discovery.utils import walk_patterns
from wagtail_unveil.wagtail_hooks import register_unveil_admin_instance_resolvers


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

    def test_runtime_reorder_urls_remain_visible_but_untestable(self):
        reorder_urls = [u for u in self.urls if u.name == "reorder" and "/reorder/" in u.route]

        if not reorder_urls:
            self.assertFalse(any(u.name == "reorder" for u in self.urls))
            return

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

    @mock.patch("wagtail_unveil.discovery.backend_resolution._get_instance_for_model", return_value=None)
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
            "wagtail_unveil.discovery.backend_resolution._resolve_settings_url",
            return_value=mock.Mock(resolved=False, attempts=["settings:no-model-instance"], detail="missing"),
        ) as resolve_settings:
            with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback") as get_model:
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

    def test_callback_model_strategy_wins_before_registered_resolvers(self):
        instance = mock.Mock(pk=42)
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution._get_instance_for_model",
                return_value=instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=[],
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
                        return_value="/admin/users/42/",
                    ):
                        result = _resolve_parameterized_url(
                            "",
                            "edit",
                            callback=object(),
                            route="admin/users/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "callback-model")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:model-found",
                "callback-model:instance-found",
                "reverse:resolved",
            ],
        )

    def test_registered_admin_resolver_fallback_resolves_when_callback_has_no_model(self):
        instance = mock.Mock(pk=7)
        resolver = AdminInstanceResolver(
            label="extension:custom-package",
            matches=lambda context: context.name == "taxonomy_person_modeladmin_edit",
            resolver=lambda context: instance,
        )
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=[resolver],
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.reverse",
                    return_value="/admin/groups/7/",
                ):
                    result = _resolve_parameterized_url(
                        "",
                        "taxonomy_person_modeladmin_edit",
                        callback=object(),
                        route="admin/taxonomy/person/<int:pk>/",
                    )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "extension:custom-package")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "extension:custom-package:instance-found",
                "reverse:resolved",
            ],
        )

    def test_wagtailforms_namespace_fallback_resolves_without_model_metadata(self):
        instance = mock.Mock(pk=9)
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=register_unveil_admin_instance_resolvers(),
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution._get_form_page_instance",
                    return_value=instance,
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
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
                "namespace:wagtailforms:instance-found",
                "reverse:resolved",
            ],
        )

    def test_workflow_namespace_overrides_callback_model_instance(self):
        callback_instance = mock.Mock(pk=1)
        workflow_instance = mock.Mock(pk=99)
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution._get_instance_for_model",
                return_value=callback_instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=register_unveil_admin_instance_resolvers(),
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution._get_workflow_instance",
                        return_value=workflow_instance,
                    ):
                        with mock.patch(
                            "wagtail_unveil.discovery.backend_resolution.reverse",
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
                "namespace:wagtailadmin_workflows:instance-found",
                "reverse:resolved",
            ],
        )

    def test_workflow_namespace_fails_closed_without_workflow_instance(self):
        callback_instance = mock.Mock(pk=1)
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution._get_instance_for_model",
                return_value=callback_instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=register_unveil_admin_instance_resolvers(),
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution._get_workflow_instance",
                        return_value=None,
                    ):
                        with mock.patch("wagtail_unveil.discovery.backend_resolution.reverse") as reverse_mock:
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
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution._get_instance_for_model",
                return_value=instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=[],
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
                        side_effect=RuntimeError("boom"),
                    ):
                        result = _resolve_parameterized_url(
                            "",
                            "edit",
                            callback=object(),
                            route="admin/users/<int:pk>/",
                        )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "callback-model")
        self.assertIn("reverse:failed", result.attempts)
        self.assertIn("boom", result.detail)

    def test_resolver_match_errors_are_recorded_and_later_resolvers_can_still_resolve(self):
        instance = mock.Mock(pk=7)

        def broken_matches(context):
            raise RuntimeError("matches boom")

        resolvers = [
            AdminInstanceResolver(
                label="extension:broken-matches",
                matches=broken_matches,
                resolver=lambda context: None,
            ),
            AdminInstanceResolver(
                label="extension:custom-package",
                matches=lambda context: True,
                resolver=lambda context: instance,
            ),
        ]

        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=resolvers,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.reverse",
                    return_value="/admin/groups/7/",
                ):
                    with self.assertLogs("wagtail_unveil.discovery.backend_resolution", level="WARNING") as logs:
                        result = _resolve_parameterized_url(
                            "",
                            "taxonomy_person_modeladmin_edit",
                            callback=object(),
                            route="admin/taxonomy/person/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "extension:broken-matches:error",
                "extension:custom-package:instance-found",
                "reverse:resolved",
            ],
        )
        self.assertEqual(len(logs.output), 1)
        self.assertIn("extension:broken-matches", logs.output[0])
        self.assertIn("match evaluation", logs.output[0])

    def test_resolver_errors_are_recorded_and_later_resolvers_can_still_resolve(self):
        instance = mock.Mock(pk=7)

        def broken_resolver(context):
            raise RuntimeError("resolver boom")

        resolvers = [
            AdminInstanceResolver(
                label="extension:broken-resolver",
                matches=lambda context: True,
                resolver=broken_resolver,
            ),
            AdminInstanceResolver(
                label="extension:custom-package",
                matches=lambda context: True,
                resolver=lambda context: instance,
            ),
        ]

        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=resolvers,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.reverse",
                    return_value="/admin/groups/7/",
                ):
                    with self.assertLogs("wagtail_unveil.discovery.backend_resolution", level="WARNING") as logs:
                        result = _resolve_parameterized_url(
                            "",
                            "taxonomy_person_modeladmin_edit",
                            callback=object(),
                            route="admin/taxonomy/person/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "extension:broken-resolver:error",
                "extension:custom-package:instance-found",
                "reverse:resolved",
            ],
        )
        self.assertEqual(len(logs.output), 1)
        self.assertIn("extension:broken-resolver", logs.output[0])
        self.assertIn("instance resolution", logs.output[0])

    def test_override_resolver_errors_do_not_clear_existing_instance(self):
        callback_instance = mock.Mock(pk=1)

        def broken_resolver(context):
            raise RuntimeError("resolver boom")

        resolver = AdminInstanceResolver(
            label="extension:override",
            matches=lambda context: True,
            resolver=broken_resolver,
            override=True,
        )

        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=User):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution._get_instance_for_model",
                return_value=callback_instance,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=[resolver],
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
                        return_value="/admin/users/1/",
                    ) as reverse_mock:
                        with self.assertLogs("wagtail_unveil.discovery.backend_resolution", level="WARNING") as logs:
                            result = _resolve_parameterized_url(
                                "",
                                "edit",
                                callback=object(),
                                route="admin/users/<int:pk>/",
                            )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "callback-model")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:model-found",
                "callback-model:instance-found",
                "extension:override:error",
                "reverse:resolved",
            ],
        )
        reverse_mock.assert_called_once_with("edit", args=[1])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("extension:override", logs.output[0])

    def test_non_callable_resolver_fields_are_recorded_as_errors_and_skipped(self):
        instance = mock.Mock(pk=7)
        resolvers = [
            AdminInstanceResolver(
                label="extension:bad-matches",
                matches="not-callable",
                resolver=lambda context: None,
            ),
            AdminInstanceResolver(
                label="extension:bad-resolver",
                matches=lambda context: True,
                resolver="not-callable",
            ),
            AdminInstanceResolver(
                label="extension:custom-package",
                matches=lambda context: True,
                resolver=lambda context: instance,
            ),
        ]

        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=resolvers,
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.reverse",
                    return_value="/admin/groups/7/",
                ):
                    with self.assertLogs("wagtail_unveil.discovery.backend_resolution", level="WARNING") as logs:
                        result = _resolve_parameterized_url(
                            "",
                            "taxonomy_person_modeladmin_edit",
                            callback=object(),
                            route="admin/taxonomy/person/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "extension:bad-matches:error",
                "extension:bad-resolver:error",
                "extension:custom-package:instance-found",
                "reverse:resolved",
            ],
        )
        self.assertEqual(len(logs.output), 2)
        self.assertIn("extension:bad-matches", logs.output[0])
        self.assertIn("extension:bad-resolver", logs.output[1])

    def test_attempts_record_full_fallback_order_when_unresolved(self):
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=register_unveil_admin_instance_resolvers(),
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution._get_form_page_instance",
                    return_value=None,
                ):
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

        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.reverse",
            side_effect=RuntimeError("should not reverse"),
        ):
            with mock.patch("wagtail.contrib.settings.registry.registry", [model]):
                result = _resolve_settings_url("edit", "admin/settings/core/socialmedia/<int:pk>/")

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "settings")
        self.assertEqual(result.attempts, ["settings:no-model-instance"])

    def test_settings_resolution_records_reverse_failures(self):
        from sandbox.core.models import SocialMediaSettings

        instance = mock.Mock(pk=3, site_id=11)
        with mock.patch.object(SocialMediaSettings.objects, "first", return_value=instance):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.reverse",
                side_effect=RuntimeError("cannot reverse"),
            ):
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

    def test_builtin_forms_resolver_skips_when_instance_already_exists(self):
        instance = mock.Mock(pk=1)

        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
            return_value=register_unveil_admin_instance_resolvers(),
        ):
            method, selected_instance, attempts = _apply_admin_instance_resolvers(
                "wagtailforms",
                "edit",
                callback=object(),
                route="admin/forms/<int:page_id>/",
                current_instance=instance,
            )

        self.assertEqual(method, "")
        self.assertIs(selected_instance, instance)
        self.assertEqual(attempts, ["namespace:wagtailforms:skipped"])


class TestModeladminURLDiscoveryWithoutProjectExtension(TestCase):
    """Test the default contract for wagtail-modeladmin routes without a project hook."""

    def setUp(self):
        from sandbox.taxonomy.models import Person

        Person.objects.create(name="Test Person", email="test@example.com")
        self.modeladmin_rows = [
            (route, name, namespace, callback)
            for route, name, namespace, callback in walk_patterns(get_resolver().url_patterns)
            if name and "modeladmin" in name
        ]

    def _get_modeladmin_urls(self):
        return [u for u in get_admin_urls() if "modeladmin" in u.name]

    def _get_modeladmin_url(self, suffix, urls):
        matches = [u for u in urls if u.name.endswith(suffix)]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def _get_modeladmin_row(self, suffix):
        matches = [row for row in self.modeladmin_rows if row[1].endswith(suffix)]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_modeladmin_urls_are_discovered_without_project_extension(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
            return_value=(),
        ):
            modeladmin_urls = self._get_modeladmin_urls()

        self.assertGreater(len(modeladmin_urls), 0)

    def test_index_and_create_routes_remain_testable_without_project_extension(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
            return_value=(),
        ):
            modeladmin_urls = self._get_modeladmin_urls()

        for suffix in ("_index", "_create"):
            with self.subTest(suffix=suffix):
                url = self._get_modeladmin_url(suffix, modeladmin_urls)
                self.assertTrue(url.is_testable)
                self.assertFalse(url.has_parameters)

    def test_parameterized_routes_remain_untestable_without_project_extension(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
            return_value=(),
        ):
            modeladmin_urls = self._get_modeladmin_urls()

        for suffix in ("_edit", "_delete", "_history"):
            with self.subTest(suffix=suffix):
                url = self._get_modeladmin_url(suffix, modeladmin_urls)
                self.assertFalse(url.is_testable)
                self.assertEqual(url.skip_reason, "URL requires parameters")
                self.assertEqual(url.resolved_route, "")

    def test_parameterized_resolution_reports_no_model_backed_instance_without_project_extension(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
            return_value=(),
        ):
            for suffix in ("_edit", "_delete", "_history"):
                with self.subTest(suffix=suffix):
                    route, name, namespace, callback = self._get_modeladmin_row(suffix)
                    result = _resolve_parameterized_url(namespace, name, callback, route)
                    self.assertFalse(result.resolved)
                    self.assertEqual(result.method, "")
                    self.assertEqual(result.attempts, ["callback-model:no-model"])
                    self.assertEqual(
                        result.detail,
                        "No model-backed instance was available for URL parameters",
                    )


class TestSandboxModeladminResolverExtension(TestCase):
    """Test that the sandbox project hook makes wagtail-modeladmin detail URLs testable."""

    def setUp(self):
        from sandbox.taxonomy.models import Person

        Person.objects.create(name="Test Person", email="test@example.com")
        self.urls = get_admin_urls()
        self.modeladmin_urls = [u for u in self.urls if "modeladmin" in u.name]

    def _get_modeladmin_url(self, suffix):
        urls = [u for u in self.modeladmin_urls if u.name.endswith(suffix)]
        self.assertEqual(len(urls), 1)
        return urls[0]

    def test_sandbox_hook_makes_parameterized_routes_testable_with_resolved_route(self):
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

        settings_instance = SocialMediaSettings.objects.first()
        self.assertIsNotNone(settings_instance)
        expected_site_pk = settings_instance.site_id

        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route and u.resolved_route]
        self.assertGreater(len(edit_urls), 0)

        for url in edit_urls:
            self.assertIn(f"/{expected_site_pk}/", url.resolved_route)

    def test_settings_preview_url_is_non_testable(self):
        """preview_on_edit URL should be non-testable since sandbox settings don't implement PreviewableMixin."""
        preview_urls = [u for u in self.settings_urls if u.name == "preview_on_edit"]

        for url in preview_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertTrue(url.skip_reason)
