from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from wagtail_unveil.discovery.backend_resolution import (
    _apply_admin_instance_resolvers,
    _get_instance_for_model,
    _resolve_settings_url,
    resolve_parameterized_url,
)
from wagtail_unveil.discovery.extensions import AdminInstanceResolver
from wagtail_unveil.wagtail_hooks import register_unveil_admin_instance_resolvers


class TestParameterizedResolutionStrategies(TestCase):
    def test_settings_resolution_runs_first_and_stops(self):
        with mock.patch(
            "wagtail_unveil.discovery.backend_resolution._resolve_settings_url",
            return_value=mock.Mock(resolved=False, attempts=["settings:no-model-instance"], detail="missing"),
        ) as resolve_settings:
            with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback") as get_model:
                result = resolve_parameterized_url(
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
                        result = resolve_parameterized_url(
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
                    result = resolve_parameterized_url(
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
                    "wagtail_unveil.discovery.backend_resolution.get_form_page_instance",
                    return_value=instance,
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
                        return_value="/admin/forms/submissions/9/",
                    ):
                        result = resolve_parameterized_url(
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

    def test_wagtailadmin_pages_without_model_metadata_no_longer_uses_hook_fallback(self):
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                    return_value=register_unveil_admin_instance_resolvers(),
            ):
                with mock.patch("wagtail_unveil.discovery.backend_resolution.reverse") as reverse_mock:
                    result = resolve_parameterized_url(
                        "wagtailadmin_pages",
                        "edit",
                        callback=object(),
                        route="admin/pages/<int:page_id>/edit/",
                    )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "")
        reverse_mock.assert_not_called()
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
            ],
        )

    def test_wagtailadmin_pages_add_subpage_without_model_metadata_no_longer_uses_hook_fallback(self):
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=register_unveil_admin_instance_resolvers(),
            ):
                with mock.patch("wagtail_unveil.discovery.backend_resolution.reverse") as reverse_mock:
                    result = resolve_parameterized_url(
                        "wagtailadmin_pages",
                        "add_subpage",
                        callback=object(),
                        route="admin/pages/<int:parent_page_id>/add_subpage/",
                    )

        self.assertFalse(result.resolved)
        self.assertEqual(result.method, "")
        reverse_mock.assert_not_called()
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
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
                        "wagtail_unveil.discovery.backend_resolution.get_workflow_instance",
                        return_value=workflow_instance,
                    ):
                        with mock.patch(
                            "wagtail_unveil.discovery.backend_resolution.reverse",
                            return_value="/admin/workflows/usage/99/",
                        ) as reverse_mock:
                            result = resolve_parameterized_url(
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
                        "wagtail_unveil.discovery.backend_resolution.get_workflow_instance",
                        return_value=None,
                    ):
                        with mock.patch("wagtail_unveil.discovery.backend_resolution.reverse") as reverse_mock:
                            result = resolve_parameterized_url(
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

    def test_workflow_task_namespace_fallback_resolves_without_model_metadata(self):
        instance = mock.Mock(pk=17)
        with mock.patch("wagtail_unveil.discovery.backend_resolution._get_model_from_callback", return_value=None):
            with mock.patch(
                "wagtail_unveil.discovery.backend_resolution.get_registered_admin_instance_resolvers",
                return_value=register_unveil_admin_instance_resolvers(),
            ):
                with mock.patch(
                    "wagtail_unveil.discovery.backend_resolution.get_workflow_task_instance",
                    return_value=instance,
                ):
                    with mock.patch(
                        "wagtail_unveil.discovery.backend_resolution.reverse",
                        return_value="/admin/workflows/tasks/edit/17/",
                    ):
                        result = resolve_parameterized_url(
                            "wagtailadmin_workflows",
                            "edit_task",
                            callback=object(),
                            route="admin/workflows/tasks/edit/<int:pk>/",
                        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.method, "namespace:wagtailadmin_workflows:tasks")
        self.assertEqual(
            result.attempts,
            [
                "callback-model:no-model",
                "namespace:wagtailadmin_workflows:tasks:instance-found",
                "reverse:resolved",
            ],
        )

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
                        result = resolve_parameterized_url(
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
                        result = resolve_parameterized_url(
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
                        result = resolve_parameterized_url(
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
                            result = resolve_parameterized_url(
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
                        result = resolve_parameterized_url(
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
                    "wagtail_unveil.discovery.backend_resolution.get_form_page_instance",
                    return_value=None,
                ):
                    result = resolve_parameterized_url(
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
