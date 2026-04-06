from unittest import mock

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site, Task, Workflow

from wagtail_unveil.discovery.backend import get_admin_urls
from wagtail_unveil.discovery.backend_resolution import (
    WAGTAILADMIN_PAGE_FALLBACK_NAMES,
    _get_model_from_callback,
)


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
        self.page = Page.objects.exclude(depth=1).first()
        self.page_types = {
            f"{type(page)._meta.app_label}.{type(page)._meta.object_name}"
            for page in Page.objects.exclude(depth=1).specific()
        }
        self.add_subpage_parent_types = {
            f"{type(page)._meta.app_label}.{type(page)._meta.object_name}"
            for page in Page.objects.exclude(depth=1).specific().order_by("path")
            if any(model.can_create_at(page) for model in type(page).creatable_subpage_models())
        }
        self.workflow = Workflow.objects.first() or Workflow.objects.create(name="Test workflow")
        self.task = Task.objects.first()
        if self.task is None:
            self.task = Task.objects.create(
                name="Test task",
                content_type=ContentType.objects.get_for_model(Task),
            )
        self.add_subpage_parent = next(
            (
                page
                for page in Page.objects.exclude(depth=1).specific().order_by("path")
                if any(model.can_create_at(page) for model in type(page).creatable_subpage_models())
            ),
            None,
        )

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

    def test_searchpick_edit_url_is_testable(self):
        self._assert_namespace_name_testable("searchpromotions", "edit")

    def test_workflow_task_routes_are_testable_with_resolved_routes(self):
        expected_pks = {
            "edit_task": self.task.pk,
            "task_chosen": self.task.pk,
        }
        workflow_task_urls = [
            u for u in self.urls if u.namespace == "wagtailadmin_workflows" and u.name in expected_pks
        ]

        self.assertEqual(len(workflow_task_urls), len(expected_pks))
        for url in workflow_task_urls:
            with self.subTest(name=url.name):
                self.assertTrue(url.is_testable, url.route)
                self.assertEqual(url.skip_reason, "")
                self.assertTrue(url.resolved_route, url.route)
                self.assertIn(f"/{expected_pks[url.name]}/", url.resolved_route)

    def test_safe_wagtail_page_routes_are_testable_with_resolved_routes(self):
        expected_names = set(WAGTAILADMIN_PAGE_FALLBACK_NAMES)
        self.assertGreater(len(self.page_types), 0)

        for name in expected_names:
            with self.subTest(name=name):
                page_urls = [u for u in self.urls if u.namespace == "wagtailadmin_pages" and u.name == name]
                self.assertEqual(len(page_urls), len(self.page_types))
                self.assertEqual({u.page_type for u in page_urls}, self.page_types)
                self.assertEqual(len({u.resolved_route for u in page_urls}), len(page_urls))
                for url in page_urls:
                    self.assertTrue(url.is_testable, url.route)
                    self.assertEqual(url.skip_reason, "")
                    self.assertTrue(url.resolved_route, url.route)
                    self.assertTrue(url.page_type)

    def test_add_subpage_route_is_testable_with_compatible_parent_page(self):
        add_subpage_urls = [u for u in self.urls if u.namespace == "wagtailadmin_pages" and u.name == "add_subpage"]

        self.assertIsNotNone(self.add_subpage_parent)
        self.assertEqual(len(add_subpage_urls), len(self.add_subpage_parent_types))
        self.assertEqual({u.page_type for u in add_subpage_urls}, self.add_subpage_parent_types)
        for url in add_subpage_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "")
            self.assertTrue(url.resolved_route, url.route)
            self.assertTrue(url.page_type)

    def test_convert_alias_page_route_remains_untestable(self):
        convert_alias_urls = [u for u in self.urls if u.namespace == "wagtailadmin_pages" and u.name == "convert_alias"]

        self.assertEqual(len(convert_alias_urls), 1)
        self.assertFalse(convert_alias_urls[0].is_testable, convert_alias_urls[0].route)
        self.assertEqual(convert_alias_urls[0].skip_reason, "URL requires parameters")
        self.assertEqual(convert_alias_urls[0].resolved_route, "")

    @mock.patch("wagtail_unveil.discovery.backend.resolve_parameterized_url")
    @mock.patch("wagtail_unveil.discovery.backend.get_add_subpage_parent_page_instances_by_type", return_value=[])
    def test_add_subpage_route_remains_untestable_without_compatible_parent_page(
        self,
        _get_parent_pages,
        mock_resolve_parameterized_url,
    ):
        mock_resolve_parameterized_url.return_value = mock.Mock(resolved=False, resolved_route="")
        urls = get_admin_urls()
        add_subpage_urls = [u for u in urls if u.namespace == "wagtailadmin_pages" and u.name == "add_subpage"]

        self.assertEqual(len(add_subpage_urls), 1)
        self.assertFalse(add_subpage_urls[0].is_testable, add_subpage_urls[0].route)
        self.assertEqual(add_subpage_urls[0].skip_reason, "URL requires parameters")
        self.assertEqual(add_subpage_urls[0].resolved_route, "")

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
