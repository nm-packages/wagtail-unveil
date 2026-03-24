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
            matches=lambda context: True,
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
            matches=lambda context: True,
            resolver=lambda context: None,
        )
        second = AdminInstanceResolver(
            label="extension:second",
            matches=lambda context: True,
            resolver=lambda context: None,
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: [first, second]],
        ):
            results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [first, second])

    def test_none_hook_result_is_ignored(self):
        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: None],
        ):
            results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [])

    def test_hook_raising_is_logged_and_later_hooks_still_load(self):
        resolver = AdminInstanceResolver(
            label="extension:single",
            matches=lambda context: True,
            resolver=lambda context: None,
        )

        def broken_hook():
            raise RuntimeError("boom")

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[broken_hook, lambda: resolver],
        ):
            with self.assertLogs("wagtail_unveil.discovery.extensions", level="WARNING") as logs:
                results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [resolver])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("broken_hook", logs.output[0])
        self.assertIn("raised an exception", logs.output[0])

    def test_invalid_hook_result_is_logged_and_skipped(self):
        resolver = AdminInstanceResolver(
            label="extension:single",
            matches=lambda context: True,
            resolver=lambda context: None,
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: "invalid", lambda: resolver],
        ):
            with self.assertLogs("wagtail_unveil.discovery.extensions", level="WARNING") as logs:
                results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [resolver])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("returned invalid admin instance resolvers", logs.output[0])

    def test_invalid_item_inside_hook_result_list_is_logged_and_skipped(self):
        resolver = AdminInstanceResolver(
            label="extension:single",
            matches=lambda context: True,
            resolver=lambda context: None,
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: [resolver, "invalid"], lambda: resolver],
        ):
            with self.assertLogs("wagtail_unveil.discovery.extensions", level="WARNING") as logs:
                results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [resolver])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("returned invalid admin instance resolvers", logs.output[0])

    def test_non_callable_resolver_fields_are_logged_and_skipped(self):
        valid = AdminInstanceResolver(
            label="extension:valid",
            matches=lambda context: True,
            resolver=lambda context: None,
        )
        bad_matches = AdminInstanceResolver(
            label="extension:bad-matches",
            matches="not-callable",
            resolver=lambda context: None,
        )
        bad_resolver = AdminInstanceResolver(
            label="extension:bad-resolver",
            matches=lambda context: True,
            resolver="not-callable",
        )

        with mock.patch(
            "wagtail_unveil.discovery.extensions.hooks.get_hooks",
            return_value=[lambda: bad_matches, lambda: bad_resolver, lambda: valid],
        ):
            with self.assertLogs("wagtail_unveil.discovery.extensions", level="WARNING") as logs:
                results = get_registered_admin_instance_resolvers()

        self.assertEqual(results, [valid])
        self.assertEqual(len(logs.output), 2)
        self.assertIn("non-callable matches function", logs.output[0])
        self.assertIn("non-callable resolver", logs.output[1])

    def test_package_registers_internal_resolvers_via_hook(self):
        hook_resolvers = register_unveil_admin_instance_resolvers()
        labels = [resolver.label for resolver in hook_resolvers]

        self.assertEqual(
            labels,
            [
                "namespace:wagtailforms",
                "namespace:wagtailadmin_pages",
                "namespace:wagtailadmin_pages:add_subpage",
                "namespace:wagtailadmin_workflows",
                "namespace:wagtailadmin_workflows:tasks",
            ],
        )
        self.assertFalse(any("modeladmin" in label for label in labels))

    def test_registered_resolvers_include_package_internal_hooks(self):
        labels = [resolver.label for resolver in get_registered_admin_instance_resolvers()]

        self.assertIn("namespace:wagtailforms", labels)
        self.assertIn("namespace:wagtailadmin_pages", labels)
        self.assertIn("namespace:wagtailadmin_pages:add_subpage", labels)
        self.assertIn("namespace:wagtailadmin_workflows", labels)
        self.assertIn("namespace:wagtailadmin_workflows:tasks", labels)
