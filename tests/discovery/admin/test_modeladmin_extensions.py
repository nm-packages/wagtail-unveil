from unittest import mock

from django.test import TestCase
from django.urls import get_resolver

from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.backend_resolution import resolve_parameterized_url
from wagtail_unveil.discovery.utils import walk_patterns


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
                    result = resolve_parameterized_url(namespace, name, callback, route)
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
