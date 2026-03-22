from unittest import mock

from django.test import SimpleTestCase

from wagtail_unveil.discovery.extensions import (
    AdminInstanceResolver,
    get_registered_admin_instance_resolvers,
)
from wagtail_unveil.wagtail_hooks import register_unveil_admin_instance_resolvers


class TestAdminInstanceResolverHooks(SimpleTestCase):
    def test_single_hook_result_is_returned(self):
        resolver = AdminInstanceResolver(
            label="extension:single",
            predicate=lambda context: True,
            resolver=lambda context: None,
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: resolver],
        ):
            results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [resolver])

    def test_list_hook_result_is_flattened(self):
        first = AdminInstanceResolver(
            label="extension:first",
            predicate=lambda context: True,
            resolver=lambda context: None,
        )
        second = AdminInstanceResolver(
            label="extension:second",
            predicate=lambda context: True,
            resolver=lambda context: None,
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: [first, second]],
        ):
            results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [first, second])

    def test_invalid_hook_result_raises_clear_error(self):
        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: "invalid"],
        ):
            with self.assertRaisesMessage(TypeError, "register_unveil_admin_instance_resolvers"):
                get_registered_admin_instance_resolvers()

    def test_package_registers_internal_resolvers_via_hook(self):
        hook_resolvers = register_unveil_admin_instance_resolvers()

        self.assertEqual(
            [resolver.label for resolver in hook_resolvers],
            [
                "namespace:wagtailforms",
                "namespace:wagtailadmin_workflows",
            ],
        )

    def test_registered_resolvers_include_package_internal_hooks(self):
        labels = [resolver.label for resolver in get_registered_admin_instance_resolvers()]

        self.assertIn("namespace:wagtailforms", labels)
        self.assertIn("namespace:wagtailadmin_workflows", labels)
